import base64
import mimetypes
import os
import threading
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import close_old_connections

from io import BytesIO
from PIL import Image

_worker_lock = threading.Lock()
_worker_thread = None

MAKEUP_IMAGE_DISCLAIMER = 'AI 기술로 생성된 예시 메이크업 이미지로, 실제 화장 결과와 제품 발색은 다를 수 있어요.'

CANONICAL_MAKEOVER_STYLES = [
    {
        'key': 'daily',
        'name': '데일리 메이크업',
        'description': '자연스러운 혈색과 부드러운 음영으로 매일 쓰기 좋은 단정한 인상을 연출해요.',
        'points': ['브라운 베이지 섀도우', '자연스러운 아이라인', '코랄 핑크 블러셔', 'MLBB 립'],
        'direction': (
            'Daily makeup: clean, polished everyday makeup. Apply a smooth but realistic base finish, '
            'soft neutral shadow, natural eyeliner, soft mascara, balanced blush, and a tone-appropriate daily lip. '
            'The result should look natural but clearly made-up, not like a simple filter.'
        ),
    },
    {
        'key': 'romantic',
        'name': '로맨틱 메이크업',
        'description': '생기 있는 컬러와 부드러운 광택으로 사랑스럽고 화사한 분위기를 연출해요.',
        'points': ['로즈/코랄 섀도우', '풍성한 속눈썹', '생기 블러셔', '촉촉한 립'],
        'direction': (
            'Romantic makeup: visibly more lively and expressive than daily makeup. Apply visible blush, '
            'soft rose, coral, or pink color depending on personal color, soft defined eyes, fuller lashes, '
            'glossy or satin lips, and a romantic lively finish.'
        ),
    },
    {
        'key': 'smoky',
        'name': '스모키 메이크업',
        'description': '깊이 있는 음영과 또렷한 눈매로 세련되고 시크한 분위기를 연출해요.',
        'points': ['브라운/모브 스모키 섀도우', '딥 브라운 아이라인', '음영 블러셔', '뮤트 로즈 립'],
        'direction': (
            'Smoky makeup: the strongest style difference. Apply deeper eye shadow, defined eyeliner, '
            'stronger mascara, more contrast around the eyes, muted or deeper lip color, '
            'and a chic sophisticated finish. Do not make it fantasy-like or overly harsh.'
        ),
    },
]

STYLE_KEY_ALIASES = {
    'natural': 'daily',
    'natural_daily': 'daily',
    'pure': 'daily',
    'pure_daily': 'daily',
    'lovely': 'romantic',
    'chic': 'smoky',
}

DEFAULT_MAKEOVER_STYLES = CANONICAL_MAKEOVER_STYLES


def canonical_makeover_key(style_key):
    return STYLE_KEY_ALIASES.get(style_key, style_key)


def get_makeover_style_meta(style_key):
    canonical_key = canonical_makeover_key(style_key)
    return next((item for item in DEFAULT_MAKEOVER_STYLES if item['key'] == canonical_key), None)


def canonical_makeover_styles(styles):
    style_map = {style.key: style for style in styles}
    ordered_styles = []
    for style_data in DEFAULT_MAKEOVER_STYLES:
        style = style_map.get(style_data['key'])
        if not style:
            alias_key = next((alias for alias, target in STYLE_KEY_ALIASES.items() if target == style_data['key'] and alias in style_map), None)
            style = style_map.get(alias_key) if alias_key else None
        if style:
            ordered_styles.append(style)
    return ordered_styles


def _tone_aware_makeup_direction(tone_key, style_key):
    normalized_tone = str(tone_key or '').lower().replace('-', '_')
    normalized_style = canonical_makeover_key(style_key)

    if 'spring' in normalized_tone and 'warm' in normalized_tone:
        directions = {
            'daily': 'Spring Warm daily colors: peach beige, soft coral, warm brown shadow, natural brown liner, and a clear coral MLBB lip.',
            'romantic': 'Spring Warm romantic colors: coral rose, warm pink blush, soft warm brown definition, and glossy coral rose lip.',
            'smoky': 'Spring Warm smoky colors: warm brown, caramel shadow, soft terracotta, warm rose lip, and brown eyeliner instead of black.',
        }
        return directions.get(normalized_style, directions['daily'])

    if 'winter' in normalized_tone and 'cool' in normalized_tone and 'deep' in normalized_tone:
        directions = {
            'daily': 'Winter Cool Deep daily colors: cool rose beige, muted mauve shadow, soft cool brown liner, and clear MLBB rose lip.',
            'romantic': 'Winter Cool Deep romantic colors: rose pink, berry pink, visible cool blush, soft mauve shadow, and glossy rose lip.',
            'smoky': 'Winter Cool Deep smoky colors: deep brown, mauve, berry shadow, defined eyeliner, stronger mascara, and muted deep rose or berry lip.',
        }
        return directions.get(normalized_style, directions['daily'])

    if 'cool' in normalized_tone:
        return 'Cool tone direction: use rose, mauve, berry, cool beige, taupe, and cool brown families while avoiding orange-heavy warmth.'

    if 'warm' in normalized_tone:
        return 'Warm tone direction: use peach, coral, warm beige, caramel brown, terracotta, and warm rose families while avoiding icy blue-pink casts.'

    return 'Tone-aware direction: choose makeup colors from the provided personal color palette and avoid listed color families.'

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

        prompt = build_makeup_generation_prompt(diagnosis, style_data)
        active_job = MakeupGenerationJob.objects.filter(
            diagnosis=diagnosis,
            style_key=style.key,
            status__in=[MakeupGenerationJob.Status.QUEUED, MakeupGenerationJob.Status.RUNNING],
        ).order_by('created_at').first()
        if active_job:
            if active_job.status == MakeupGenerationJob.Status.QUEUED and active_job.prompt != prompt:
                active_job.prompt = prompt
                active_job.save(update_fields=['prompt', 'updated_at'])
            continue

        jobs.append(
            MakeupGenerationJob.objects.create(
                diagnosis=diagnosis,
                style_key=style.key,
                status=MakeupGenerationJob.Status.QUEUED,
                prompt=prompt,
            )
        )

    if jobs:
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.QUEUED
        diagnosis.makeup_generation_error = ''
        diagnosis.save(update_fields=['makeup_generation_status', 'makeup_generation_error'])

    return jobs


def retry_makeover_style_generation(diagnosis, style_key):
    from diagnosis.models import DiagnosisMakeoverStyle, DiagnosisResult, MakeupGenerationJob

    style_key = canonical_makeover_key(style_key)
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
    style_data = style or DEFAULT_MAKEOVER_STYLES[0]
    style_key = canonical_makeover_key(style_data.get('key'))
    style_direction = style_data.get('direction', '')
    tone_direction = _tone_aware_makeup_direction(diagnosis.tone_key or diagnosis.personal_color_code, style_key)

    return '\n'.join(
        [
            'Edit the uploaded face photo into a photorealistic personal color makeup preview.',
            'This is an image editing task, not a new character generation task.',
            'Keep the exact same person from the uploaded photo.',
            'Preserve identity, facial structure, face shape, eyes, nose, lips, eyebrows, skin texture, hairstyle, hair length, pose, camera angle, crop, and overall likeness.',
            'Do not redraw the person as an illustration, cartoon, avatar, doll, or different model.',
            'Do not create a beauty chart illustration. Do not create a vector-style preview.',
            'Do not change age, gender presentation, hairstyle, clothing, pose, or facial proportions.',
            'Only change the makeup on the existing face.',
            'Keep the original photo composition and realistic studio-photo quality as much as possible.',
            'If the original background is distracting, simplify it very subtly, but do not change the person or crop dramatically.',

            'The result must look like real cosmetics were professionally applied to the face.',
            'Do not make it look like a simple beauty filter, color overlay, skin smoothing filter, or global color grading.',
            'Apply actual visible makeup by facial area.',
            'Base makeup: adjust finish, coverage, glow or matte texture according to the style while preserving realistic skin texture.',
            'Eyes: apply visible eye shadow color and depth, eyeliner shape, mascara intensity, and under-eye/aegyo-sal detail when appropriate.',
            'Cheeks: apply blush placement, color, and intensity according to the style.',
            'Lips: apply lip color, texture, saturation, and shape while preserving the original lip shape.',
            'Face dimension: apply contour and highlight only if appropriate for the style, without changing the face shape.',

            f"Current style: {style_data.get('name') or style_key}.",
            f"Style direction: {style_direction}",
            f"Tone-aware makeup direction: {tone_direction}",
            f"Personal color toneKey: {diagnosis.tone_key or diagnosis.personal_color_code}",

            f"Base guide: {prompt_seed.get('base') or palette.get('baseMakeupGuide') or makeup.get('base', {}).get('guide', '')}",
            f"Lip colors to prioritize: {', '.join(lip_colors)}",
            f"Cheek colors to prioritize: {', '.join(cheek_colors)}",
            f"Eye colors to prioritize: {', '.join(eye_colors)}",
            f"Colors to avoid: {', '.join(avoid_colors)}",

            'Use the provided palette directions as the main color guide, but choose realistic cosmetic shade variations within that tone family when needed.',
            'The makeup style should be clear enough that a result card can explain the makeup points.',
            'The difference between Daily, Romantic, and Smoky styles must be visually distinguishable across the generated results.',
            'Use realistic medium intensity for Daily style, more lively and glossy expression for Romantic style, and stronger but still elegant intensity for Smoky style.',
            'The final image should be suitable for a beauty consultation result page: realistic, polished, and clearly made-up.',

            'Negative prompt: no simple beauty filter, no color overlay only, no global color grading only, no face replacement, no different person, no illustration, no cartoon, no avatar, no vector art, no plastic skin, no excessive smoothing, no unrealistic doll face, no distorted facial features, no changed hairstyle, no changed clothing, no changed pose, no fantasy makeup, no text inside generated portrait image.',
        ]
    )


def get_makeover_payload(diagnosis, request=None):
    from diagnosis.serializers import DiagnosisMakeoverStyleSerializer

    styles = canonical_makeover_styles(list(diagnosis.makeover_styles.all()))
    serialized_styles = DiagnosisMakeoverStyleSerializer(styles, many=True, context={'request': request}).data
    return {
        'status': _makeover_status(diagnosis, styles),
        'styles': serialized_styles,
        'makeup_images': serialized_styles,
        'error': diagnosis.makeup_generation_error,
    }


def process_next_makeup_job():
    from diagnosis.models import MakeupGenerationJob

    job = MakeupGenerationJob.objects.select_related('diagnosis').filter(status='queued').order_by('created_at').first()
    if not job:
        return None
    return process_makeup_job(job)


def start_makeover_worker(limit=5):
    global _worker_thread

    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            return False

        _worker_thread = threading.Thread(
            target=_process_makeover_jobs_in_background,
            args=(limit,),
            daemon=True,
        )
        _worker_thread.start()
        return True


def _process_makeover_jobs_in_background(limit):
    close_old_connections()
    try:
        for _ in range(limit):
            job = process_next_makeup_job()
            if not job:
                break
    finally:
        close_old_connections()


def process_makeup_job(job):
    from diagnosis.models import DiagnosisMakeoverStyle, DiagnosisResult, MakeupGenerationJob

    diagnosis = job.diagnosis
    style_key = canonical_makeover_key(job.style_key) if job.style_key else ''
    style = diagnosis.makeover_styles.filter(key=style_key).first() if style_key else None

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

def normalize_source_image_for_openai(image_bytes, diagnosis_id):
    try:
        image = Image.open(BytesIO(image_bytes))
        image = image.convert('RGBA')

        max_side = 1536
        width, height = image.size
        longest = max(width, height)

        if longest > max_side:
            scale = max_side / longest
            new_size = (
                max(1, int(width * scale)),
                max(1, int(height * scale)),
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        output = BytesIO()
        image.save(output, format='PNG')
        output.seek(0)

        return (
            f'diagnosis-{diagnosis_id}-source.png',
            output.read(),
            'image/png',
        )
    except Exception as exc:
        raise RuntimeError(f'Failed to normalize source image for makeup generation: {exc}') from exc
    

def _sync_diagnosis_makeover_status(diagnosis):
    from diagnosis.models import DiagnosisResult

    styles = canonical_makeover_styles(list(diagnosis.makeover_styles.all()))
    status = _makeover_status(diagnosis, styles)

    if status == 'complete':
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.COMPLETE
        diagnosis.makeup_generation_error = ''

    elif status == 'failed':
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.FAILED

    elif status == 'partial':
        # 일부 이미지는 생성 완료, 일부는 실패한 상태.
        # 더 이상 작업 중이 아니므로 RUNNING으로 두면 안 됨.
        diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.FAILED
        diagnosis.makeup_generation_error = diagnosis.makeup_generation_error or '일부 메이크업 이미지 생성에 실패했습니다.'

    elif status in {'queued', 'running'}:
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

    # IMPORTANT:
    # Django ImageFieldFile itself is not accepted by the OpenAI SDK.
    # Read the file bytes and pass a file tuple instead.
    try:
        image_field.open('rb')
        image_bytes = image_field.read()
    finally:
        image_field.close()

    if not image_bytes:
        raise RuntimeError('Source image file is empty.')

    openai_image_file = normalize_source_image_for_openai(image_bytes, diagnosis.pk)

    response = client.images.edit(
        model=os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-1'),
        image=openai_image_file,
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

