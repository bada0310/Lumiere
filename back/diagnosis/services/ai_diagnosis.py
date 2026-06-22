import base64
import inspect
import json
import logging
from io import BytesIO

from asgiref.sync import async_to_sync
from django.conf import settings
from PIL import Image, ImageOps

from diagnosis.ai_clients.openai_compatible import AIClientConfigurationError, AIClientResponseError
from diagnosis.domain.tone_key_normalizer import ToneKeyError, normalize_tone_key
from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS

logger = logging.getLogger(__name__)

REQUIRED_RESPONSE_KEYS = {'tone_key', 'confidence', 'summary', 'features'}
REQUIRED_FEATURE_KEYS = {'temperature', 'brightness', 'chroma', 'contrast'}
DEFAULT_MIME_TYPE = 'image/jpeg'
AI_IMAGE_MIME_TYPE = 'image/jpeg'
AI_IMAGE_MAX_EDGE = 768
AI_IMAGE_JPEG_QUALITY = 80


def diagnose_personal_color(image_file):
    if getattr(settings, 'OPENAI_DIAGNOSIS_MOCK', False):
        return _mock_diagnosis()

    return async_to_sync(_diagnose_personal_color_async)(image_file)


async def _diagnose_personal_color_async(image_file):
    data_url = _image_file_to_data_url(image_file)
    client = _create_client()
    try:
        response = await client.chat.completions.create(
            **_build_chat_completion_kwargs(data_url),
        )
    except Exception as exc:
        if _should_fallback_on_ai_error():
            logger.warning('AI diagnosis request failed; using mock fallback: %s', exc)
            return _mock_diagnosis()
        raise AIClientResponseError(f'AI diagnosis request failed: {exc}') from exc
    finally:
        await _close_client(client)

    try:
        return _parse_response(response)
    except AIClientResponseError as exc:
        if _should_fallback_on_ai_error():
            logger.warning('AI diagnosis response was invalid; using mock fallback: %s', exc)
            return _mock_diagnosis()
        raise


def _build_chat_completion_kwargs(data_url):
    kwargs = {
        'model': settings.AI_DIAGNOSIS_MODEL,
        'messages': [
                {
                    'role': 'system',
                    'content': (
                        'You are a personal color diagnosis assistant. '
                        'Return exactly one valid JSON object and no extra text.'
                    ),
                },
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': _build_prompt()},
                        {'type': 'image_url', 'image_url': {'url': data_url}},
                    ],
                },
        ],
        'response_format': {'type': 'json_object'},
    }

    if _supports_custom_temperature(settings.AI_DIAGNOSIS_MODEL):
        kwargs['temperature'] = 0.1

    return kwargs


def _supports_custom_temperature(model):
    return not str(model or '').lower().startswith('gpt-5')


def _create_client():
    if not settings.OPENAI_API_KEY:
        raise AIClientConfigurationError('OPENAI_API_KEY is not configured.')

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise AIClientConfigurationError('The openai package is not installed.') from exc

    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)


async def _close_client(client):
    close = getattr(client, 'close', None)
    if not close:
        return

    result = close()
    if inspect.isawaitable(result):
        await result


def _image_file_to_data_url(image_file):
    position = None
    if hasattr(image_file, 'tell'):
        try:
            position = image_file.tell()
        except (OSError, ValueError):
            position = None

    image_bytes = image_file.read()

    if hasattr(image_file, 'seek'):
        try:
            image_file.seek(0 if position is None else position)
        except (OSError, ValueError):
            pass

    if not image_bytes:
        raise AIClientResponseError('Uploaded image is empty.')

    mime_type = getattr(image_file, 'content_type', None) or DEFAULT_MIME_TYPE
    image_bytes, mime_type = _prepare_image_bytes_for_ai(image_bytes, mime_type)
    encoded = base64.b64encode(image_bytes).decode('ascii')
    return f'data:{mime_type};base64,{encoded}'


def _prepare_image_bytes_for_ai(image_bytes, mime_type):
    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception:
        return image_bytes, mime_type

    image = ImageOps.exif_transpose(image).convert('RGB')
    image.thumbnail((AI_IMAGE_MAX_EDGE, AI_IMAGE_MAX_EDGE))

    output = BytesIO()
    image.save(output, format='JPEG', quality=AI_IMAGE_JPEG_QUALITY, progressive=False)
    return output.getvalue(), AI_IMAGE_MIME_TYPE


def _build_prompt():
    tone_keys = ', '.join(CANONICAL_TONE_KEYS)
    return f"""
Analyze the uploaded face image and choose exactly one tone_key from this list:
{tone_keys}

Return only this JSON shape:
{{
  "tone_key": "summer_cool_light",
  "confidence": 85,
  "summary": "diagnosis summary in Korean",
  "features": {{
    "temperature": "cool",
    "brightness": "high",
    "chroma": "low",
    "contrast": "medium"
  }}
}}

Rules:
- tone_key must be one of the allowed values exactly.
- confidence must be a number from 0 to 100.
- Do not return palettes, product recommendations, makeup images, or extra fields.
""".strip()


def _parse_response(response):
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise AIClientResponseError('AI response did not include message content.') from exc

    if not isinstance(content, str):
        raise AIClientResponseError('AI response content was not a JSON string.')

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIClientResponseError('AI response was not valid JSON.') from exc

    if not isinstance(payload, dict):
        raise AIClientResponseError('AI response JSON must be an object.')

    extra_keys = set(payload) - REQUIRED_RESPONSE_KEYS
    if extra_keys:
        raise AIClientResponseError(f'AI response contained unsupported fields: {", ".join(sorted(extra_keys))}')

    missing_keys = REQUIRED_RESPONSE_KEYS - set(payload)
    if missing_keys:
        raise AIClientResponseError(f'AI response missing fields: {", ".join(sorted(missing_keys))}')

    features = payload.get('features')
    if not isinstance(features, dict):
        raise AIClientResponseError('AI response features must be an object.')

    extra_features = set(features) - REQUIRED_FEATURE_KEYS
    if extra_features:
        raise AIClientResponseError(f'AI response features contained unsupported fields: {", ".join(sorted(extra_features))}')

    missing_features = REQUIRED_FEATURE_KEYS - set(features)
    if missing_features:
        raise AIClientResponseError(f'AI response features missing fields: {", ".join(sorted(missing_features))}')

    try:
        tone_key = normalize_tone_key(payload.get('tone_key'), allow_close_match=False)
    except ToneKeyError as exc:
        raise AIClientResponseError(str(exc)) from exc

    payload['tone_key'] = tone_key
    payload['confidence'] = _normalize_confidence(payload.get('confidence'))
    payload['summary'] = str(payload.get('summary') or '').strip()

    if not payload['summary']:
        raise AIClientResponseError('AI response summary is required.')

    return payload


def _normalize_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise AIClientResponseError('AI response confidence must be a number.') from exc

    if 0 <= confidence <= 1:
        confidence *= 100

    if confidence < 0 or confidence > 100:
        raise AIClientResponseError('AI response confidence must be between 0 and 100.')

    return round(confidence)


def _should_fallback_on_ai_error():
    return bool(getattr(settings, 'OPENAI_DIAGNOSIS_FALLBACK_ON_ERROR', False))


def _mock_diagnosis():
    return {
        'tone_key': 'summer_cool_mute',
        'confidence': 82,
        'summary': 'Development fallback diagnosis result. External AI analysis is unavailable.',
        'features': {
            'temperature': 'cool',
            'brightness': 'medium',
            'chroma': 'low',
            'contrast': 'medium',
        },
    }
