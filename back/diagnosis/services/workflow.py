from django.conf import settings
from django.db import transaction
from django.utils import timezone

from diagnosis.domain.tone_keys import build_tone_name, tone_key_to_personal_color_fields
from diagnosis.domain.tone_profiles import build_tone_result_payload
from diagnosis.schemas.diagnosis_schema import LOW_CONFIDENCE_THRESHOLD
from diagnosis.services.image_quality import validate_and_prepare_image
from diagnosis.services.makeup_generation import enqueue_makeup_generation
from diagnosis.services.multimodal_diagnosis import create_diagnosis_from_image
from diagnosis.services.palettes import apply_palette_snapshot_to_diagnosis, get_palette_for_tone_key
from diagnosis.services.primary import user_has_primary_diagnosis

from diagnosis.models import DiagnosisResult, PersonalColor


class ImageQualityError(ValueError):
    def __init__(self, result):
        super().__init__(result.message)
        self.result = result


class PaletteNotReadyError(ValueError):
    pass


def run_personal_color_diagnosis(user, uploaded_file):
    quality = validate_and_prepare_image(uploaded_file)
    if not quality.ok:
        raise ImageQualityError(quality)

    diagnosis_json = create_diagnosis_from_image(quality.processed_image)
    tone_key = diagnosis_json['toneKey']
    diagnosis_json = {
        **diagnosis_json,
        **build_tone_result_payload(
            tone_key,
            diagnosis_json.get('secondToneKey') or diagnosis_json.get('second_tone_key'),
        ),
    }
    palette_data, palette_status = get_palette_for_tone_key(tone_key)
    if palette_status != DiagnosisResult.PaletteStatus.READY and not settings.DEBUG:
        raise PaletteNotReadyError(f'Fixed palette is not ready for toneKey={tone_key}')

    personal_color = get_or_create_personal_color(tone_key, diagnosis_json, palette_data)

    with transaction.atomic():
        diagnosis = build_diagnosis_result(
            user=user,
            uploaded_file=uploaded_file,
            quality=quality,
            diagnosis_json=diagnosis_json,
            tone_key=tone_key,
            palette_data=palette_data,
            palette_status=palette_status,
            personal_color=personal_color,
        )
        apply_palette_snapshot_to_diagnosis(diagnosis, palette_data)

        if diagnosis.status == DiagnosisResult.Status.COMPLETED and diagnosis.palette_status == DiagnosisResult.PaletteStatus.READY:
            enqueue_makeup_generation(diagnosis)
        elif diagnosis.makeup_generation_status != DiagnosisResult.MakeupGenerationStatus.SKIPPED:
            diagnosis.makeup_generation_status = DiagnosisResult.MakeupGenerationStatus.SKIPPED
            diagnosis.save(update_fields=['makeup_generation_status'])

    return diagnosis


def get_or_create_personal_color(tone_key, diagnosis_json, palette_data):
    fields = tone_key_to_personal_color_fields(tone_key)
    analysis = diagnosis_json.get('analysis') or {}
    defaults = {
        'type_name': palette_data.get('toneName') or diagnosis_json.get('toneName') or build_tone_name(tone_key),
        'base_temperature': fields['base_temperature'],
        'season': fields['season'],
        'tone': fields['tone'],
        'description': palette_data.get('description') or diagnosis_json.get('summary', ''),
        'temperature_degree': _temperature_degree(analysis.get('temperature')),
        'brightness_degree': _degree(analysis.get('brightness')),
        'saturation_degree': _degree(analysis.get('chroma')),
        'turbidity_degree': 100 - _degree(analysis.get('chroma')),
        'glossiness_degree': 50,
        'contrast_degree': _degree(analysis.get('contrast')),
        'best_pccs': _pccs_codes(tone_key),
        'sub_pccs': [],
    }
    personal_color = (
        PersonalColor.objects.filter(tone_key=tone_key).first()
        or PersonalColor.objects.filter(type_name=defaults['type_name']).first()
        or PersonalColor(tone_key=tone_key)
    )
    for key, value in defaults.items():
        setattr(personal_color, key, value)
    personal_color.tone_key = tone_key
    personal_color.full_clean()
    personal_color.save()
    return personal_color


def build_diagnosis_result(*, user, uploaded_file, quality, diagnosis_json, tone_key, palette_data, palette_status, personal_color):
    confidence = float(diagnosis_json.get('confidence') or 0)
    confidence_score = max(0, min(100, round(confidence * 100)))
    is_low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD
    analysis = diagnosis_json.get('analysis') or {}

    diagnosis = DiagnosisResult(
        user=user,
        personal_color=personal_color,
        status=DiagnosisResult.Status.LOW_CONFIDENCE if is_low_confidence else DiagnosisResult.Status.COMPLETED,
        tone_key=tone_key,
        personal_color_code=tone_key,
        korean_name=palette_data.get('toneName') or diagnosis_json.get('toneName') or build_tone_name(tone_key),
        english_name=_english_name(tone_key),
        confidence_score=confidence_score,
        diagnosed_at=timezone.localdate(),
        summary=diagnosis_json.get('summary', ''),
        diagnosis_json=diagnosis_json,
        palette_snapshot=palette_data,
        palette_status=palette_status,
        keywords=palette_data.get('keywords') or [],
        image_features=_image_features(diagnosis_json),
        skin_metrics=_skin_metrics(analysis),
        radar_chart=_radar_chart(analysis),
        style_guide=_style_guide(palette_data),
        is_primary=not user_has_primary_diagnosis(user),
        makeup_generation_status=DiagnosisResult.MakeupGenerationStatus.SKIPPED if is_low_confidence else DiagnosisResult.MakeupGenerationStatus.NONE,
    )

    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    diagnosis.uploaded_image = uploaded_file
    diagnosis.processed_image.save(quality.processed_filename, quality.processed_image, save=False)
    diagnosis.full_clean()
    diagnosis.save()
    return diagnosis


def _degree(value):
    return {
        'low': 25,
        'low_to_medium': 38,
        'medium_low': 40,
        'medium': 55,
        'medium_high': 70,
        'high': 85,
    }.get(value, 50)


def _temperature_degree(value):
    return {
        'warm': 20,
        'neutral': 50,
        'cool': 82,
    }.get(value, 50)


def _skin_metrics(analysis):
    temperature = analysis.get('temperature')
    return {
        'brightness': _degree(analysis.get('brightness')),
        'saturation': _degree(analysis.get('chroma')),
        'clarity': max(0, min(100, 100 - _degree(analysis.get('chroma')) + 20)),
        'contrast': _degree(analysis.get('contrast')),
        'cool_warm': _temperature_degree(temperature),
        'softness': max(0, min(100, 100 - _degree(analysis.get('contrast')) + 10)),
        'gloss': 50,
    }


def _radar_chart(analysis):
    metrics = _skin_metrics(analysis)
    return {
        'brightness': metrics['brightness'],
        'saturation': metrics['saturation'],
        'clarity': metrics['clarity'],
        'contrast': metrics['contrast'],
        'softness': metrics['softness'],
        'coolness': metrics['cool_warm'],
    }


def _image_features(diagnosis_json):
    evidence = diagnosis_json.get('evidence') or {}
    return [
        {'key': 'skin_tone', 'title': '피부톤 근거', 'description': evidence.get('skinToneReason', ''), 'icon': 'sparkle'},
        {'key': 'contrast', 'title': '대비 근거', 'description': evidence.get('contrastReason', ''), 'icon': 'cloud'},
        {'key': 'chroma', 'title': '채도 근거', 'description': evidence.get('chromaReason', ''), 'icon': 'diamond'},
    ]


def _style_guide(palette_data):
    if palette_data.get('styleGuide'):
        return {
            **palette_data['styleGuide'],
            'styling_keywords': palette_data.get('stylingKeywords') or palette_data.get('keywords') or [],
            'recommended_product_tone_range': palette_data.get('recommendedProductToneRange') or {},
        }

    best_colors = palette_data.get('bestColors') or []
    return {
        'styling_keywords': palette_data.get('stylingKeywords') or [],
        'recommended_product_tone_range': palette_data.get('recommendedProductToneRange') or {},
        'fashion': [
            {
                'name': item.get('nameKo') or item.get('name'),
                'hex': item.get('hex'),
                'description': item.get('description', ''),
            }
            for item in best_colors
        ],
    }


def _english_name(tone_key):
    return ' '.join(part.title() for part in tone_key.split('_'))


def _pccs_codes(tone_key):
    tone = tone_key.rsplit('_', 1)[-1]
    return {
        'bright': ['b', 'v'],
        'light': ['p', 'lt'],
        'mute': ['sf', 'ltg'],
        'deep': ['dp', 'dk'],
    }.get(tone, ['lt'])
