import json

from django.core.exceptions import ValidationError

from diagnosis.ai_clients.openai_compatible import OpenAICompatibleClient
from diagnosis.domain.personal_color_criteria import PERSONAL_COLOR_CRITERIA_TEXT
from diagnosis.domain.tone_key_normalizer import ToneKeyError, normalize_tone_key
from diagnosis.schemas.diagnosis_schema import DIAGNOSIS_JSON_SCHEMA


def create_diagnosis_from_image(processed_image_file):
    image_bytes = processed_image_file.read()
    processed_image_file.seek(0)

    prompt = _build_prompt()
    ai_payload = OpenAICompatibleClient().create_diagnosis_json(
        image_bytes=image_bytes,
        mime_type='image/jpeg',
        prompt=prompt,
        schema=DIAGNOSIS_JSON_SCHEMA,
    )
    return validate_diagnosis_payload(ai_payload)


def validate_diagnosis_payload(payload):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        _fallback_validate(payload)
    else:
        errors = sorted(Draft202012Validator(DIAGNOSIS_JSON_SCHEMA).iter_errors(payload), key=lambda error: error.path)
        if errors:
            raise ValidationError(f'AI diagnosis JSON schema validation failed: {errors[0].message}')

    try:
        payload['toneKey'] = normalize_tone_key(payload.get('toneKey'), allow_close_match=False)
    except ToneKeyError as exc:
        raise ValidationError(str(exc)) from exc

    payload['confidence'] = float(payload.get('confidence', 0))
    return payload


def _fallback_validate(payload):
    if not isinstance(payload, dict):
        raise ValidationError('AI diagnosis payload must be a JSON object.')
    required = DIAGNOSIS_JSON_SCHEMA['required']
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValidationError(f'AI diagnosis JSON missing fields: {", ".join(missing)}')
    if not isinstance(payload.get('analysis'), dict) or not isinstance(payload.get('evidence'), dict):
        raise ValidationError('AI diagnosis analysis and evidence must be objects.')


def _build_prompt():
    schema_text = json.dumps(DIAGNOSIS_JSON_SCHEMA, ensure_ascii=False)
    return f"""
Analyze the uploaded face image and choose exactly one toneKey from the personal color criteria.

Rules:
- Return only JSON matching the provided schema.
- Do not create or return color chips, palettes, product colors, makeup colors, or styling keyword lists.
- The fixed palette database will provide all colors and makeup guides after toneKey selection.
- If image evidence is weak, lower confidence instead of forcing certainty.
- Include cautions that lighting, filters, and white balance can change the result.

Personal color criteria:
{PERSONAL_COLOR_CRITERIA_TEXT}

JSON Schema:
{schema_text}
""".strip()
