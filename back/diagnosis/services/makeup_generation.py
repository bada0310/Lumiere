import base64
import os
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


DEFAULT_MAKEOVER_STYLES = [
    {
        'key': 'natural_daily',
        'name': '내추럴 데일리룩',
        'description': '피부결과 혈색을 자연스럽게 살린 데일리 메이크업',
        'direction': 'natural daily makeup, sheer warm base, soft definition, wearable everyday look',
    },
    {
        'key': 'pure_daily',
        'name': '청순 데일리룩',
        'description': '맑고 부드러운 눈매와 은은한 립을 중심으로 한 룩',
        'direction': 'clean pure daily makeup, soft under-eye brightness, gentle lip and blush',
    },
    {
        'key': 'romantic',
        'name': '로맨틱 룩',
        'description': '톤에 맞는 립과 블러셔로 분위기를 더한 룩',
        'direction': 'romantic makeup, harmonious blush and lip, soft eye depth, polished finish',
    },
    {
        'key': 'chic',
        'name': '시크 룩',
        'description': '정돈된 음영과 선명한 포인트를 살린 룩',
        'direction': 'chic makeup, refined shading, defined liner, controlled point color',
    },
    {
        'key': 'smoky',
        'name': '스모키 룩',
        'description': '톤에 맞는 깊은 음영으로 눈매를 또렷하게 만든 룩',
        'direction': 'soft smoky makeup, deeper eye shading, natural skin, no harsh transformation',
    },
]


def enqueue_makeup_generation(diagnosis):
    jobs = enqueue_makeover_generation(diagnosis)
    return jobs[0] if jobs else None


def enqueue_makeover_generation(diagnosis):
    from diagnosis.models import DiagnosisMakeoverStyle, DiagnosisResult, MakeupGenerationJob

    jobs = []
    for index, style_data in enumerate(DEFAULT_MAKEOVER_STYLES):
        style, _ = DiagnosisMakeoverStyle.objects.update_or_create(
            diagnosis=diagnosis,
            key=style_data['key'],
            defaults={
                'name': style_data['name'],
                'description': style_data['description'],
                'order': index + 1,
                'is_default': index == 0,
            },
        )

        if style.image and style.status == DiagnosisMakeoverStyle.Status.COMPLETE:
            continue

        if style.status != DiagnosisMakeoverStyle.Status.RUNNING:
            style.status = DiagnosisMakeoverStyle.Status.QUEUED
            style.error_message = ''
            style.save(update_fields=['status', 'error_message'])

        has_active_job = MakeupGenerationJob.objects.filter(
            diagnosis=diagnosis,
            style_key=style.key,
            status__in=[MakeupGenerationJob.Status.QUEUED, MakeupGenerationJob.Status.RUNNING],
        ).exists()
        if has_active_job:
            continue

        jobs.append(
            MakeupGenerationJob.objects.create(
                diagnosis=diagnosis,
                style_key=style.key,
                status=MakeupGenerationJob.Status.QUEUED,
                prompt=build_makeup_generation_prompt(diagnosis, style_data),
            )
        )

    if jobs:
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.QUEUED
        diagnosis.makeup_generation_error = ''
        diagnosis.save(update_fields=['makeup_generation_status', 'makeup_generation_error'])

    return jobs


def retry_makeover_style_generation(diagnosis, style_key):
    from diagnosis.models import DiagnosisMakeoverStyle, DiagnosisResult, MakeupGenerationJob

    style_data = next((item for item in DEFAULT_MAKEOVER_STYLES if item['key'] == style_key), None)
    if not style_data:
        raise ValueError('Unsupported makeover style.')

    style, _ = DiagnosisMakeoverStyle.objects.update_or_create(
        diagnosis=diagnosis,
        key=style_key,
        defaults={
            'name': style_data['name'],
            'description': style_data['description'],
            'order': DEFAULT_MAKEOVER_STYLES.index(style_data) + 1,
            'is_default': style_key == DEFAULT_MAKEOVER_STYLES[0]['key'],
            'status': DiagnosisMakeoverStyle.Status.QUEUED,
            'error_message': '',
        },
    )
    style.status = DiagnosisMakeoverStyle.Status.QUEUED
    style.error_message = ''
    style.save(update_fields=['status', 'error_message'])

    MakeupGenerationJob.objects.filter(
        diagnosis=diagnosis,
        style_key=style_key,
        status=MakeupGenerationJob.Status.QUEUED,
    ).delete()
    MakeupGenerationJob.objects.create(
        diagnosis=diagnosis,
        style_key=style_key,
        status=MakeupGenerationJob.Status.QUEUED,
        prompt=build_makeup_generation_prompt(diagnosis, style_data),
    )

    diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.QUEUED
    diagnosis.makeup_generation_error = ''
    diagnosis.save(update_fields=['makeup_generation_status', 'makeup_generation_error'])
    return style


def build_makeup_generation_prompt(diagnosis, style=None):
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
    style_direction = (style or DEFAULT_MAKEOVER_STYLES[0]).get('direction', '')

    return '\n'.join(
        [
            'Edit the uploaded face photo for a personal color makeup preview.',
            'Preserve the person identity, face shape, facial features, skin texture, expression, pose, and framing.',
            'Do not change age, gender presentation, hairstyle length, background, face structure, or facial proportions.',
            'Apply only natural makeup color and finish changes.',
            f"Style direction: {style_direction}",
            f"Personal color toneKey: {diagnosis.tone_key or diagnosis.personal_color_code}",
            f"Base guide: {prompt_seed.get('base') or palette.get('baseMakeupGuide') or makeup.get('base', {}).get('guide', '')}",
            f"Lip colors: {', '.join(lip_colors)}",
            f"Cheek colors: {', '.join(cheek_colors)}",
            f"Eye colors: {', '.join(eye_colors)}",
            f"Avoid colors: {', '.join(avoid_colors)}",
            'Use only these fixed palette directions. Do not invent new color families.',
            'Keep the result photorealistic and subtle enough for a beauty consultation result page.',
        ]
    )


def get_makeover_payload(diagnosis, request=None):
    from diagnosis.serializers import DiagnosisMakeoverStyleSerializer

    styles = list(diagnosis.makeover_styles.all())
    return {
        'status': _makeover_status(diagnosis, styles),
        'styles': DiagnosisMakeoverStyleSerializer(styles, many=True, context={'request': request}).data,
        'error': diagnosis.makeup_generation_error,
    }


def process_next_makeup_job():
    from diagnosis.models import MakeupGenerationJob

    job = MakeupGenerationJob.objects.select_related('diagnosis').filter(status='queued').order_by('created_at').first()
    if not job:
        return None
    return process_makeup_job(job)


def process_makeup_job(job):
    from diagnosis.models import DiagnosisMakeoverStyle, DiagnosisResult, MakeupGenerationJob

    diagnosis = job.diagnosis
    style = diagnosis.makeover_styles.filter(key=job.style_key).first() if job.style_key else None

    job.status = MakeupGenerationJob.Status.RUNNING
    job.save(update_fields=['status', 'updated_at'])
    diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.RUNNING
    diagnosis.save(update_fields=['makeup_generation_status'])

    if style:
        style.status = DiagnosisMakeoverStyle.Status.RUNNING
        style.error_message = ''
        style.save(update_fields=['status', 'error_message'])

    try:
        image_bytes = generate_makeup_image(diagnosis, job.prompt)

        if style:
            filename = f'diagnosis/generated/makeovers/makeup-{diagnosis.pk}-{style.key}.png'
            saved_path = default_storage.save(filename, ContentFile(image_bytes))
            style.image = saved_path
            style.status = DiagnosisMakeoverStyle.Status.COMPLETE
            style.error_message = ''
            style.save(update_fields=['image', 'status', 'error_message'])
        else:
            filename = f'makeup-{diagnosis.pk}.png'
            diagnosis.generated_makeup_image.save(filename, ContentFile(image_bytes), save=False)

        job.status = MakeupGenerationJob.Status.COMPLETE
        job.error_message = ''
        job.save(update_fields=['status', 'error_message', 'updated_at'])
        _sync_diagnosis_makeover_status(diagnosis)
    except Exception as exc:
        if style:
            style.status = DiagnosisMakeoverStyle.Status.FAILED
            style.error_message = str(exc)
            style.save(update_fields=['status', 'error_message'])

        job.status = MakeupGenerationJob.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=['status', 'error_message', 'updated_at'])

        diagnosis.makeup_generation_error = str(exc)
        _sync_diagnosis_makeover_status(diagnosis)

    return job


def _sync_diagnosis_makeover_status(diagnosis):
    from diagnosis.models import DiagnosisResult

    styles = list(diagnosis.makeover_styles.all())
    status = _makeover_status(diagnosis, styles)
    if status == 'complete':
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.COMPLETE
        diagnosis.makeup_generation_error = ''
    elif status == 'failed':
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.FAILED
    elif status in {'queued', 'running', 'partial'}:
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.RUNNING
    else:
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.NONE
    diagnosis.save(update_fields=['makeup_generation_status', 'makeup_generation_error'])


def _makeover_status(diagnosis, styles):
    if not styles:
        return diagnosis.makeup_generation_status or 'none'

    statuses = {style.status for style in styles}
    if statuses == {'complete'}:
        return 'complete'
    if 'running' in statuses:
        return 'running'
    if 'queued' in statuses or 'none' in statuses:
        return 'queued'
    if 'complete' in statuses and 'failed' in statuses:
        return 'partial'
    if statuses == {'failed'}:
        return 'failed'
    return diagnosis.makeup_generation_status or 'none'


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
