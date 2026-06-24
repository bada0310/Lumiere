import base64
import json
import os

from django.conf import settings


class AIClientConfigurationError(RuntimeError):
    pass


class AIClientResponseError(RuntimeError):
    pass


class AIClientParseError(AIClientResponseError):
    pass


class OpenAICompatibleClient:
    def __init__(self, *, model=None):
        api_key = (
            getattr(settings, 'OPENAI_API_KEY', None)
            or os.getenv('OPENAI_API_KEY')
            or os.getenv('OPENAI_COMPATIBLE_API_KEY')
        )
        self.base_url = (
            getattr(settings, 'OPENAI_BASE_URL', None)
            or os.getenv('OPENAI_BASE_URL')
            or os.getenv('OPENAI_COMPATIBLE_BASE_URL')
        )
        self.model = model or getattr(settings, 'AI_DIAGNOSIS_MODEL', None) or settings.OPENAI_MODEL
        self.mock_enabled = os.getenv('OPENAI_DIAGNOSIS_MOCK', '').lower() in {'1', 'true', 'yes'}

        if self.mock_enabled:
            self.client = None
            return

        if not api_key:
            raise AIClientConfigurationError('OPENAI_API_KEY is not configured.')

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AIClientConfigurationError('The openai package is not installed.') from exc

        kwargs = {'api_key': api_key}
        if self.base_url:
            kwargs['base_url'] = self.base_url
        self.client = OpenAI(**kwargs)

    def create_diagnosis_json(self, *, image_bytes, mime_type, prompt, schema):
        if self.mock_enabled:
            return _mock_diagnosis()

        data_url = f'data:{mime_type};base64,{base64.b64encode(image_bytes).decode("ascii")}'
        kwargs = {
            'model': self.model,
            'response_format': {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'personal_color_diagnosis',
                    'schema': schema,
                    'strict': True,
                },
            },
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'You are a personal color diagnosis assistant. Return only valid JSON. '
                        'Do not invent color chips, makeup colors, product colors, or palette data.'
                    ),
                },
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': data_url}},
                    ],
                },
            ],
        }
        if _supports_custom_temperature(self.model):
            kwargs['temperature'] = 0.1
        response = self.client.chat.completions.create(
            **kwargs,
        )

        return _parse_json_content(response)

    def create_chat_json(self, *, prompt, schema, schema_name='structured_response', system_prompt=None, temperature=0.2):
        if self.mock_enabled:
            return {}

        kwargs = {
            'model': self.model,
            'response_format': {
                'type': 'json_schema',
                'json_schema': {
                    'name': schema_name,
                    'schema': schema,
                    'strict': True,
                },
            },
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt or 'Return only valid JSON that matches the provided schema.',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
        }
        if _supports_custom_temperature(self.model):
            kwargs['temperature'] = temperature
        response = self.client.chat.completions.create(
            **kwargs,
        )

        return _parse_json_content(response)

    def create_vision_json(
        self,
        *,
        image_bytes,
        mime_type,
        prompt,
        schema,
        schema_name='vision_structured_response',
        system_prompt=None,
        temperature=0.1,
        response_format_type='json_schema',
        validate_schema=False,
        debug_label=None,
    ):
        if self.mock_enabled:
            return {}

        data_url = f'data:{mime_type};base64,{base64.b64encode(image_bytes).decode("ascii")}'
        kwargs = {
            'model': self.model,
            'response_format': _build_response_format(
                response_format_type=response_format_type,
                schema=schema,
                schema_name=schema_name,
            ),
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt or 'Return only valid JSON that matches the provided schema.',
                },
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': data_url}},
                    ],
                },
            ],
        }
        if _supports_custom_temperature(self.model):
            kwargs['temperature'] = temperature

        if debug_label == 'product image':
            print('DEBUG product image AI model:', repr(self.model))
            print('DEBUG OPENAI_BASE_URL:', settings.OPENAI_BASE_URL)
            print('DEBUG OpenAICompatibleClient self.model:', repr(self.model))

        response = self.client.chat.completions.create(
            **kwargs,
        )

        payload = _parse_json_content(response)
        if validate_schema:
            _validate_payload_schema(payload, schema)
        return payload


def _supports_custom_temperature(model):
    return not str(model or '').lower().startswith('gpt-5')


def _build_response_format(*, response_format_type, schema, schema_name):
    if response_format_type == 'json_object':
        return {'type': 'json_object'}
    return {
        'type': 'json_schema',
        'json_schema': {
            'name': schema_name,
            'schema': schema,
            'strict': True,
        },
    }


def _parse_json_content(response):
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise AIClientParseError('AI response did not include message content.') from exc

    try:
        return json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AIClientParseError('AI response was not valid JSON.') from exc


def _validate_payload_schema(payload, schema):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        if not isinstance(payload, dict):
            raise AIClientParseError('AI response JSON must be an object.')
        return

    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        raise AIClientParseError(f'AI response schema validation failed: {errors[0].message}')


def _mock_diagnosis():
    return {
        'toneKey': 'summer_cool_mute',
        'toneName': '여름 쿨 뮤트',
        'confidence': 0.82,
        'summary': '전체적으로 부드럽고 차분한 쿨톤 경향이 강하며 저채도와 중명도 계열이 자연스럽게 어울립니다.',
        'analysis': {
            'temperature': 'cool',
            'brightness': 'medium',
            'chroma': 'low_to_medium',
            'contrast': 'low',
            'skinUndertone': 'pink_or_neutral_cool',
            'recommendedIntensity': 'soft',
        },
        'evidence': {
            'skinToneReason': '피부가 노란기보다 붉은기 또는 중성 쿨 경향으로 보입니다.',
            'contrastReason': '머리카락, 눈동자, 피부 사이의 대비가 강하지 않아 부드러운 색이 적합합니다.',
            'chromaReason': '선명한 고채도 색보다 탁하고 부드러운 색에서 조화가 좋습니다.',
        },
        'cautions': [
            '조명, 필터, 화이트밸런스에 따라 결과가 달라질 수 있습니다.',
            '정확도를 높이려면 자연광에서 정면 얼굴 사진을 사용하는 것이 좋습니다.',
        ],
    }
