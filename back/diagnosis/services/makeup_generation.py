import base64
import os
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.db import transaction


def enqueue_makeup_generation(diagnosis):
    from diagnosis.models import MakeupGenerationJob

    diagnosis.makeup_generation_status = 'queued'
    diagnosis.save(update_fields=['makeup_generation_status'])
    return MakeupGenerationJob.objects.create(
        diagnosis=diagnosis,
        status='queued',
        prompt=build_makeup_generation_prompt(diagnosis),
    )


def build_makeup_generation_prompt(diagnosis):
    palette = diagnosis.palette_snapshot or {}
    prompt_seed = palette.get('genAiPromptSeed') or {}
    makeup = palette.get('makeupPalette') or {}
    guide = palette.get('makeupColorGuide') or {}
    eye_roles = (guide.get('eye') or {}).get('roles') or {}
    eye_colors = prompt_seed.get('eye') or [
        item.get('name')
        for item in eye_roles.values()
        if isinstance(item, dict) and item.get('name')
    ] or makeup.get('eye', {}).get('recommended', [])
    lip_colors = prompt_seed.get('lip') or makeup.get('lip', {}).get('recommended', [])
    cheek_colors = prompt_seed.get('cheek') or makeup.get('cheek', {}).get('recommended', [])
    avoid_colors = prompt_seed.get('avoid') or []
    return '\n'.join(
        [
            'Apply a natural makeup look to the uploaded face photo.',
            f"Personal color toneKey: {diagnosis.tone_key or diagnosis.personal_color_code}",
            f"Base guide: {prompt_seed.get('base') or palette.get('baseMakeupGuide') or makeup.get('base', {}).get('guide', '')}",
            f"Lip colors: {', '.join(lip_colors)}",
            f"Cheek colors: {', '.join(cheek_colors)}",
            f"Eye colors: {', '.join(eye_colors)}",
            f"Avoid colors: {', '.join(avoid_colors)}",
            'Use only these fixed palette directions. Do not invent new color families.',
        ]
    )


def process_next_makeup_job():
    from diagnosis.models import MakeupGenerationJob

    job = MakeupGenerationJob.objects.select_related('diagnosis').filter(status='queued').order_by('created_at').first()
    if not job:
        return None
    return process_makeup_job(job)


@transaction.atomic
def process_makeup_job(job):
    diagnosis = job.diagnosis
    job.status = 'running'
    diagnosis.makeup_generation_status = 'running'
    job.save(update_fields=['status', 'updated_at'])
    diagnosis.save(update_fields=['makeup_generation_status'])

    try:
        image_bytes = generate_makeup_image(diagnosis, job.prompt)
        filename = f'makeup-{diagnosis.pk}.png'
        diagnosis.generated_makeup_image.save(filename, ContentFile(image_bytes), save=False)
        diagnosis.makeup_generation_status = 'complete'
        diagnosis.makeup_generation_error = ''
        diagnosis.save(update_fields=['generated_makeup_image', 'makeup_generation_status', 'makeup_generation_error'])
        job.status = 'complete'
        job.error_message = ''
        job.save(update_fields=['status', 'error_message', 'updated_at'])
    except Exception as exc:
        diagnosis.makeup_generation_status = 'failed'
        diagnosis.makeup_generation_error = str(exc)
        diagnosis.save(update_fields=['makeup_generation_status', 'makeup_generation_error'])
        job.status = 'failed'
        job.error_message = str(exc)
        job.save(update_fields=['status', 'error_message', 'updated_at'])
    return job


def generate_makeup_image(diagnosis, prompt):
    if os.getenv('OPENAI_IMAGE_GENERATION_MOCK', '').lower() in {'1', 'true', 'yes'}:
        if diagnosis.processed_image:
            with diagnosis.processed_image.open('rb') as image_file:
                return image_file.read()
        with diagnosis.uploaded_image.open('rb') as image_file:
            return image_file.read()

    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_COMPATIBLE_API_KEY')
    if not api_key:
        raise RuntimeError('GenAI image generation provider is not configured.')

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError('The openai package is not installed.') from exc

    kwargs = {'api_key': api_key}
    base_url = os.getenv('OPENAI_BASE_URL') or os.getenv('OPENAI_COMPATIBLE_BASE_URL')
    if base_url:
        kwargs['base_url'] = base_url

    client = OpenAI(**kwargs)
    image_field = diagnosis.processed_image or diagnosis.uploaded_image
    if not image_field:
        raise RuntimeError('No source image exists for GenAI makeup generation.')

    with image_field.open('rb') as source_image:
        response = client.images.edit(
            model=os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-1'),
            image=source_image,
            prompt=prompt,
            size=os.getenv('OPENAI_IMAGE_SIZE', '1024x1024'),
        )

    item = response.data[0]
    if getattr(item, 'b64_json', None):
        return base64.b64decode(item.b64_json)
    if getattr(item, 'url', None):
        with urlopen(item.url, timeout=30) as generated:
            return generated.read()

    raise RuntimeError('GenAI image generation response did not include image data.')
