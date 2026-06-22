import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from diagnosis.ai_clients.openai_compatible import AIClientConfigurationError
from diagnosis.domain.palette_seed_data import PALETTE_SEED_DATA, validate_palette_seed_data
from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS
from diagnosis.domain.tone_key_normalizer import ToneKeyError, normalize_tone_key
from diagnosis.models import DiagnosisResult, PersonalColor, PersonalColorPalette
from diagnosis.services.ai_diagnosis import diagnose_personal_color
from diagnosis.services.makeup_generation import build_makeup_generation_prompt
from diagnosis.services.multimodal_diagnosis import validate_diagnosis_payload
from diagnosis.services.palettes import get_palette_for_tone_key, serialize_palette


class ToneKeyNormalizerTests(TestCase):
    def test_normalizes_aliases(self):
        self.assertEqual(normalize_tone_key('fall-cool-muted'), 'autumn_cool_mute')
        self.assertEqual(normalize_tone_key('winter cool clear'), 'winter_cool_bright')

    def test_rejects_unknown_tone_key(self):
        with self.assertRaises(ToneKeyError):
            normalize_tone_key('summer_cool_true')


class DiagnosisPayloadValidationTests(TestCase):
    def test_rejects_invalid_tone_key(self):
        payload = {
            'toneKey': 'summer_cool_true',
            'toneName': 'Summer Cool True',
            'confidence': 0.8,
            'summary': 'summary',
            'analysis': {
                'temperature': 'cool',
                'brightness': 'medium',
                'chroma': 'low_to_medium',
                'contrast': 'low',
                'skinUndertone': 'pink',
                'recommendedIntensity': 'soft',
            },
            'evidence': {
                'skinToneReason': 'reason',
                'contrastReason': 'reason',
                'chromaReason': 'reason',
            },
            'cautions': ['lighting can affect the result'],
        }

        with self.assertRaises(ValidationError):
            validate_diagnosis_payload(payload)


class AIDiagnosisServiceTests(TestCase):
    @override_settings(OPENAI_MODEL='gpt-4.1')
    def test_calls_openai_with_image_data_url_and_without_stream(self):
        class FakeCompletions:
            def __init__(self):
                self.kwargs = None

            async def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=json.dumps(
                                    {
                                        'tone_key': 'summer-cool-mute',
                                        'confidence': 0.85,
                                        'summary': 'AI summary',
                                        'features': {
                                            'temperature': 'cool',
                                            'brightness': 'medium',
                                            'chroma': 'low',
                                            'contrast': 'medium',
                                        },
                                    }
                                )
                            )
                        )
                    ]
                )

        class FakeClient:
            def __init__(self):
                self.chat = SimpleNamespace(completions=FakeCompletions())
                self.closed = False

            async def close(self):
                self.closed = True

        fake_client = FakeClient()
        upload = SimpleUploadedFile('face.png', b'image-bytes', content_type='image/png')

        with patch('diagnosis.services.ai_diagnosis._create_client', return_value=fake_client):
            result = diagnose_personal_color(upload)

        kwargs = fake_client.chat.completions.kwargs
        self.assertEqual(kwargs['model'], 'gpt-4.1')
        self.assertNotIn('stream', kwargs)
        self.assertEqual(kwargs['response_format'], {'type': 'json_object'})
        self.assertTrue(kwargs['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))
        self.assertEqual(result['tone_key'], 'summer_cool_mute')
        self.assertEqual(result['confidence'], 85)
        self.assertTrue(fake_client.closed)

    @override_settings(OPENAI_API_KEY='')
    def test_requires_openai_api_key(self):
        upload = SimpleUploadedFile('face.jpg', b'image-bytes', content_type='image/jpeg')

        with self.assertRaises(AIClientConfigurationError):
            diagnose_personal_color(upload)


class PaletteServiceTests(TestCase):
    @override_settings(DEBUG=True)
    def test_missing_palette_returns_preparing_fallback(self):
        palette, status = get_palette_for_tone_key('winter_cool_bright')

        self.assertEqual(status, 'preparing')
        self.assertEqual(palette['toneName'], '팔레트 준비 중')
        self.assertEqual(palette['requestedToneKey'], 'winter_cool_bright')
        self.assertGreater(len(palette['bestColors']), 0)

    @override_settings(DEBUG=False)
    def test_missing_palette_returns_missing_without_dev_fallback(self):
        palette, status = get_palette_for_tone_key('winter_cool_bright')

        self.assertEqual(status, 'missing')
        self.assertEqual(palette['toneKey'], 'winter_cool_bright')
        self.assertTrue(palette['isPlaceholder'])

    def test_seeded_palette_is_ready_for_any_canonical_tone_key(self):
        call_command('seed_personal_color_palettes', verbosity=0)

        palette, status = get_palette_for_tone_key('winter_cool_bright')

        self.assertEqual(status, 'ready')
        self.assertEqual(palette['toneKey'], 'winter_cool_bright')
        self.assertFalse(palette['isPlaceholder'])
        self.assertGreater(len(palette['palettes']['best']), 0)
        self.assertGreater(len(palette['palettes']['worst']), 0)
        self.assertEqual(set(palette['makeupColorGuide']['eye']['roles'].keys()), {'highlighter', 'base', 'shading', 'point'})


class PaletteSeedDataTests(TestCase):
    def test_seed_payload_covers_all_32_tone_keys_without_placeholders(self):
        self.assertEqual(list(PALETTE_SEED_DATA.keys()), CANONICAL_TONE_KEYS)
        self.assertEqual(validate_palette_seed_data(PALETTE_SEED_DATA), [])
        self.assertTrue(all(payload['is_placeholder'] is False for payload in PALETTE_SEED_DATA.values()))

    def test_seed_command_creates_32_complete_rows(self):
        call_command('seed_personal_color_palettes', verbosity=0)
        call_command('validate_personal_color_palettes', verbosity=0)

        self.assertEqual(PersonalColorPalette.objects.count(), 32)
        self.assertEqual(PersonalColorPalette.objects.filter(is_placeholder=False).count(), 32)
        for tone_key in CANONICAL_TONE_KEYS:
            payload = serialize_palette(PersonalColorPalette.objects.get(tone_key=tone_key))
            self.assertGreater(len(payload['palettes']['best']), 0)
            self.assertGreater(len(payload['palettes']['worst']), 0)
            self.assertEqual(set(payload['makeupColorGuide']['eye']['roles'].keys()), {'highlighter', 'base', 'shading', 'point'})


class MakeupGenerationPromptTests(TestCase):
    def test_prompt_uses_fixed_makeup_palette(self):
        user = self._user()
        personal_color = self._personal_color()
        diagnosis = DiagnosisResult.objects.create(
            user=user,
            personal_color=personal_color,
            tone_key='summer_cool_mute',
            personal_color_code='summer_cool_mute',
            confidence_score=82,
            palette_snapshot={
                'baseMakeupGuide': 'Use pink neutral base.',
                'makeupPalette': {
                    'lip': {'recommended': ['dusty rose']},
                    'cheek': {'recommended': ['lavender pink']},
                    'eye': {'recommended': ['taupe brown']},
                },
            },
        )

        prompt = build_makeup_generation_prompt(diagnosis)

        self.assertIn('summer_cool_mute', prompt)
        self.assertIn('dusty rose', prompt)
        self.assertIn('taupe brown', prompt)

    def _user(self):
        return get_user_model().objects.create_user(username='tester', email='tester@example.com', password='test1234!')

    def _personal_color(self):
        return PersonalColor.objects.create(
            type_name='여름 쿨 뮤트',
            tone_key='summer_cool_mute',
            base_temperature='cool',
            season='summer',
            tone='MUTE',
            description='desc',
            temperature_degree=82,
            brightness_degree=55,
            saturation_degree=38,
            turbidity_degree=62,
            glossiness_degree=50,
            contrast_degree=25,
        )


class DiagnosisAnalyzeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='api-user', email='api@example.com', password='test1234!')
        self.client.force_authenticate(self.user)
        self.personal_color = PersonalColor.objects.create(
            type_name='API 여름 쿨 뮤트',
            tone_key='summer_cool_mute',
            base_temperature='cool',
            season='summer',
            tone='MUTE',
            description='desc',
            temperature_degree=82,
            brightness_degree=55,
            saturation_degree=38,
            turbidity_degree=62,
            glossiness_degree=50,
            contrast_degree=25,
        )
        self.palette_data = {
            'toneKey': 'summer_cool_mute',
            'toneName': '여름 쿨 뮤트',
            'keywords': ['soft', 'cool'],
            'palettes': {
                'best': [{'name': 'Soft Rose', 'nameKo': '소프트 로즈', 'hex': '#CFA0AC'}],
                'neutral': [],
                'accent': [],
                'try': [],
                'worst': [{'name': 'Orange Brown', 'nameKo': '오렌지 브라운', 'hex': '#A65A35'}],
            },
            'makeupColorGuide': {},
            'styleGuide': {},
            'recommendedProductToneRange': {},
        }
        self.palette = PersonalColorPalette.objects.create(
            tone_key='summer_cool_mute',
            data=self.palette_data,
            tone_name='여름 쿨 뮤트',
            season='summer',
            temperature='cool',
            brightness='medium',
            chroma='low_to_medium',
            contrast='low',
            keywords=['soft', 'cool'],
            is_placeholder=False,
            personal_color=self.personal_color,
        )

    def test_analyze_endpoint_returns_created_result(self):
        upload = SimpleUploadedFile('face.jpg', b'fake-image', content_type='image/jpeg')
        ai_payload = {
            'tone_key': 'summer_cool_mute',
            'confidence': 85,
            'summary': 'AI summary',
            'features': {
                'temperature': 'cool',
                'brightness': 'medium',
                'chroma': 'low',
                'contrast': 'medium',
            },
        }

        with patch('diagnosis.views.diagnose_personal_color', return_value=ai_payload):
            response = self.client.post('/api/diagnosis/analyze/', {'image': upload}, format='multipart')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tone_key'], 'summer_cool_mute')
        self.assertEqual(response.data['palette']['toneKey'], 'summer_cool_mute')
        self.assertEqual(response.data['confidence'], 85)
        self.assertEqual(response.data['summary'], 'AI summary')
        self.assertEqual(response.data['diagnosis_json'], ai_payload)
        diagnosis = DiagnosisResult.objects.get(pk=response.data['id'])
        self.assertEqual(diagnosis.palette_snapshot, self.palette_data)
        self.assertEqual(diagnosis.makeup_generation_status, DiagnosisResult.MakeupGenerationStatus.NONE)

    def test_analyze_endpoint_returns_palette_missing(self):
        upload = SimpleUploadedFile('face.jpg', b'fake-image', content_type='image/jpeg')
        ai_payload = {
            'tone_key': 'winter_cool_bright',
            'confidence': 80,
            'summary': 'AI summary',
            'features': {
                'temperature': 'cool',
                'brightness': 'high',
                'chroma': 'high',
                'contrast': 'high',
            },
        }

        with patch('diagnosis.views.diagnose_personal_color', return_value=ai_payload):
            response = self.client.post('/api/diagnosis/analyze/', {'image': upload}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'palette_missing')

    def test_analyze_endpoint_returns_ai_configuration_error(self):
        upload = SimpleUploadedFile('face.jpg', b'fake-image', content_type='image/jpeg')

        with patch('diagnosis.views.diagnose_personal_color', side_effect=AIClientConfigurationError('OPENAI_API_KEY is not configured.')):
            response = self.client.post('/api/diagnosis/analyze/', {'image': upload}, format='multipart')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data['code'], 'ai_not_configured')

    def test_analyze_endpoint_requires_image(self):
        response = self.client.post('/api/diagnosis/analyze/', {}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'image_required')
