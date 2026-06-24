import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import openai
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from diagnosis.ai_clients.openai_compatible import AIClientParseError, OpenAICompatibleClient
from diagnosis.models import DiagnosisResult, PersonalColor
from PIL import Image, ImageDraw
from .models import Product, ProductImageAnalysis, ProductOffer, ProductOption, ProductOptionToneScore, Review
from .services.color_metrics import build_color_metrics, public_grade_from_score
from .services.image_color_analysis import (
    PRODUCT_IMAGE_ANALYSIS_SCHEMA,
    extract_color_blobs_from_image,
    resolve_product_image_analysis_model,
)


def openai_request():
    return httpx.Request('POST', 'https://example.com/v1/chat/completions')


def make_bad_request_error(message):
    response = httpx.Response(400, request=openai_request())
    return openai.BadRequestError(message, response=response, body={'message': message})


def make_authentication_error(message='auth failed'):
    response = httpx.Response(401, request=openai_request())
    return openai.AuthenticationError(message, response=response, body={'message': message})


def make_api_error(message='provider failed'):
    return openai.APIError(message, request=openai_request(), body={'message': message})


def make_chart_upload():
    image = Image.new('RGB', (320, 240), 'white')
    draw = ImageDraw.Draw(image)
    draw.ellipse((30, 40, 110, 120), fill='#B95F55')
    draw.ellipse((180, 60, 260, 140), fill='#7A4B6A')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return SimpleUploadedFile('chart.png', buffer.getvalue(), content_type='image/png')


def make_blank_upload():
    image = Image.new('RGB', (320, 240), 'white')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return SimpleUploadedFile('blank.png', buffer.getvalue(), content_type='image/png')


class ProductReviewApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='reviewer',
            password='password1234',
            nickname='reviewer_nick',
        )
        self.personal_color = PersonalColor.objects.create(
            type_name='Product Test Tone',
            tone_key='spring_warm_light',
            base_temperature=PersonalColor.BaseTemperature.warm,
            season=PersonalColor.SeasonChoice.spring,
            tone=PersonalColor.ToneChoices.LIGHT,
            description='test',
            temperature_degree=20,
            brightness_degree=80,
            saturation_degree=40,
            turbidity_degree=60,
            glossiness_degree=50,
            contrast_degree=25,
            best_pccs=[],
            sub_pccs=[],
        )
        self.product = Product.objects.create(
            brand='romand',
            name='Juicy Lasting Tint',
            category=Product.Category.LIP,
            canonical_key='romand|lip|juicy-lasting-tint',
            match_score=92,
        )
        self.option = ProductOption.objects.create(
            product=self.product,
            option_no='04',
            option_name='Peach Coral',
            option_key='04-peach-coral',
            analyzed_tone_tag='spring_warm_light',
            hex_code='#f8ad9d',
            rgb_r=248,
            rgb_g=173,
            rgb_b=157,
            brightness=79,
            saturation=87,
            coolness=9,
            warmth=91,
            depth=21,
            softness=9,
            contrast=35,
        )
        ProductOffer.objects.create(
            option=self.option,
            mall_name='test mall',
            price=8900,
            product_url='https://example.com/product',
            is_representative=True,
        )
        ProductOptionToneScore.objects.create(
            option=self.option,
            target_tone='spring_warm_light',
            match_score=88,
            grade=ProductOptionToneScore.Grade.BEST,
            reason='good match',
        )

    def test_product_list_returns_grouped_products(self):
        response = self.client.get('/api/products/items/?tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id'], self.product.id)
        self.assertEqual(response.data[0]['brand'], 'romand')
        self.assertEqual(response.data[0]['best_option']['option_no'], '04')
        self.assertEqual(response.data[0]['best_option']['id'], self.option.id)
        self.assertEqual(response.data[0]['options'][0]['hex_code'], '#f8ad9d')
        self.assertEqual(response.data[0]['min_price'], 8900)

    def test_product_detail_returns_nested_product_data(self):
        response = self.client.get(f'/api/products/{self.product.id}/?tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.id)
        self.assertEqual(response.data['best_option']['id'], self.option.id)
        self.assertEqual(response.data['options'][0]['offers'][0]['price'], 8900)
        self.assertEqual(response.data['options'][0]['tone_scores'][0]['target_tone'], 'spring_warm_light')
        self.assertEqual(response.data['min_price'], 8900)
        self.assertEqual(response.data['max_price'], 8900)

    def test_product_catalog_color_analysis_returns_shared_result_shape(self):
        response = self.client.get(f'/api/products/{self.product.id}/color-analysis/?tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product']['id'], self.product.id)
        self.assertTrue(response.data['personalized'])
        self.assertEqual(response.data['options'][0]['id'], self.option.id)
        self.assertIn(response.data['options'][0]['grade'], ['BEST', 'GOOD', 'CAUTION'])
        self.assertEqual(response.data['best_option']['id'], self.option.id)
        self.assertIn('recommendation_groups', response.data)

    def test_product_catalog_color_analysis_handles_missing_primary(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/products/{self.product.id}/color-analysis/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['personalized'])
        self.assertIsNone(response.data['user_tone'])
        self.assertIsNone(response.data['options'][0]['match_score'])

    def test_product_detail_does_not_resolve_by_option_id(self):
        second_option = ProductOption.objects.create(
            product=self.product,
            option_no='05',
            option_name='Rose Coral',
            option_key='05-rose-coral',
            analyzed_tone_tag='spring_warm_light',
            hex_code='#e78f9e',
            brightness=75,
            saturation=77,
            coolness=16,
            warmth=84,
            depth=24,
            softness=14,
            contrast=30,
        )

        response = self.client.get(f'/api/products/{second_option.id}/?tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_list_uses_primary_diagnosis_when_tone_query_is_missing(self):
        DiagnosisResult.objects.create(
            user=self.user,
            personal_color=self.personal_color,
            tone_key='spring_warm_light',
            personal_color_code='spring_warm_light',
            confidence_score=90,
            is_primary=True,
        )
        DiagnosisResult.objects.create(
            user=self.user,
            personal_color=self.personal_color,
            tone_key='winter_cool_bright',
            personal_color_code='winter_cool_bright',
            confidence_score=80,
        )
        self.client.force_authenticate(self.user)

        inferred_response = self.client.get('/api/products/items/')
        explicit_primary_response = self.client.get('/api/products/items/?tone_key=spring_warm_light')
        explicit_latest_response = self.client.get('/api/products/items/?tone_key=winter_cool_bright')

        self.assertEqual(inferred_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            inferred_response.data[0]['best_option']['match_score'],
            explicit_primary_response.data[0]['best_option']['match_score'],
        )
        self.assertNotEqual(
            inferred_response.data[0]['best_option']['match_score'],
            explicit_latest_response.data[0]['best_option']['match_score'],
        )

    def test_product_list_handles_authenticated_user_without_primary_diagnosis(self):
        DiagnosisResult.objects.create(
            user=self.user,
            personal_color=self.personal_color,
            tone_key='winter_cool_bright',
            personal_color_code='winter_cool_bright',
            confidence_score=80,
        )
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/products/items/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id'], self.product.id)
        self.assertIn('best_option', response.data[0])

    def test_authenticated_user_can_create_review(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/products/reviews/',
            {
                'product': self.product.id,
                'rating': 5,
                'content': 'good match',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)


class ProductCatalogSeedTests(APITestCase):
    def test_seed_product_catalog_command_creates_curated_catalog(self):
        call_command('seed_product_catalog', '--commit', '--reset-catalog', verbosity=0)

        self.assertEqual(Product.objects.filter(canonical_key__startswith='catalog:').count(), 36)
        self.assertEqual(ProductOption.objects.filter(product__canonical_key__startswith='catalog:').count(), 108)
        self.assertEqual(ProductOffer.objects.filter(option__product__canonical_key__startswith='catalog:').count(), 108)
        self.assertEqual(
            ProductOptionToneScore.objects.filter(option__product__canonical_key__startswith='catalog:').count(),
            3456,
        )

        product = Product.objects.get(id=10001)
        self.assertEqual(product.options.count(), 3)
        self.assertTrue(product.options.first().tone_scores.exists())


class RecommendationColorMatchingApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='recommendation-user',
            password='password1234',
            nickname='recommendation_user',
        )
        self.product = Product.objects.create(
            brand='romand',
            name='Juicy Lasting Tint',
            category=Product.Category.LIP,
            canonical_key='romand|lip|juicy-lasting-tint-api',
            product_url='https://example.com/product',
            representative_image_url='https://image.example/tint.jpg',
        )
        self.option = ProductOption.objects.create(
            product=self.product,
            option_no='04',
            option_name='Peach Coral',
            option_key='04-peach-coral',
            hex_code='#F07C78',
            rgb_r=240,
            rgb_g=124,
            rgb_b=120,
            brightness=72,
            saturation=62,
            coolness=38,
            warmth=62,
            depth=28,
            softness=36,
            contrast=40,
        )
        ProductOptionToneScore.objects.create(
            option=self.option,
            target_tone='spring_warm_light',
            match_score=91,
            grade=ProductOptionToneScore.Grade.BEST,
            reason='test reason',
        )
        self.avoid_product = Product.objects.create(
            brand='cool brand',
            name='Deep Cool Tint',
            category=Product.Category.LIP,
            canonical_key='cool-brand|lip|deep-cool-tint-api',
        )
        self.avoid_option = ProductOption.objects.create(
            product=self.avoid_product,
            option_no='99',
            option_name='Icy Deep Berry',
            option_key='99-icy-deep-berry',
            hex_code='#221026',
            rgb_r=34,
            rgb_g=16,
            rgb_b=38,
            brightness=5,
            saturation=5,
            coolness=100,
            warmth=0,
            depth=95,
            softness=0,
            contrast=100,
            analyzed_tone_tag='winter_cool_deep',
        )

    def test_personalized_products_returns_balanced_recommendation_shape(self):
        response = self.client.get('/api/recommendations/personalized-products/?limit=12&per_category=2&tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('category_balance', response.data)
        self.assertGreaterEqual(response.data['count'], 1)
        first = response.data['results'][0]
        self.assertEqual(first['id'], self.product.id)
        self.assertEqual(first['best_option']['id'], self.option.id)
        self.assertIn(first['match_status'], {'BEST', 'GOOD', 'CAUTION'})
        self.assertTrue(first['short_reason'])

    def test_personalized_products_excludes_avoid_matches(self):
        response = self.client.get('/api/recommendations/personalized-products/?limit=12&per_category=2&tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data['results']}
        returned_statuses = {item['match_status'] for item in response.data['results']}
        self.assertIn(self.product.id, returned_ids)
        self.assertNotIn(self.avoid_product.id, returned_ids)
        self.assertNotIn('AVOID', returned_statuses)

    def test_recommendation_color_matching_returns_option_chart_and_table_data(self):
        response = self.client.get(f'/api/recommendations/{self.product.id}/color-matching/?tone_key=spring_warm_light')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product']['id'], self.product.id)
        self.assertEqual(response.data['product']['brand'], 'romand')
        self.assertEqual(response.data['options'][0]['id'], self.option.id)
        self.assertIn('chart_x', response.data['options'][0])
        self.assertIn('chart_y', response.data['options'][0])
        self.assertIn('match_status', response.data['options'][0])
        self.assertTrue(response.data['comparison_metrics'])

class ProductImageAnalysisModelSelectionTests(TestCase):
    @override_settings(PRODUCT_IMAGE_ANALYSIS_MODEL='gpt-4.1', AI_DIAGNOSIS_MODEL='gpt-5.5', OPENAI_MODEL='gpt-5.5')
    def test_resolve_product_image_analysis_model_prefers_product_setting(self):
        self.assertEqual(resolve_product_image_analysis_model(), 'gpt-4.1')

    def test_local_color_blob_extraction_finds_distinct_colors(self):
        upload = make_chart_upload()
        image = Image.open(BytesIO(upload.read())).convert('RGBA')

        candidates = extract_color_blobs_from_image(image)

        self.assertEqual(len(candidates), 2)
        self.assertEqual([candidate['option_name'] for candidate in candidates], ['Option 1', 'Option 2'])
        self.assertNotEqual(candidates[0]['hex_code'], candidates[1]['hex_code'])
        self.assertLess(candidates[0]['chart_y'], candidates[1]['chart_y'] + 15)
        self.assertLess(candidates[0]['chart_x'], candidates[1]['chart_x'])

    @override_settings(OPENAI_API_KEY='test-key', OPENAI_BASE_URL='https://gms.example/v1')
    def test_product_vision_request_uses_json_object_and_omits_temperature_for_gpt5(self):
        captured = {}
        payload = {
            'product_name': 'Demo Chart',
            'brand_name': 'Demo',
            'chart_labels': {
                'warm_label': 'Warm',
                'cool_label': 'Cool',
                'light_label': 'Light',
                'deep_label': 'Deep',
                'best_region_labels': [],
                'season_labels': [],
            },
            'options': [],
        }

        class FakeOpenAI:
            def __init__(self, **kwargs):
                captured['init_kwargs'] = kwargs
                self.chat = SimpleNamespace(
                    completions=SimpleNamespace(create=self.create),
                )

            def create(self, **kwargs):
                captured['request_kwargs'] = kwargs
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=json.dumps(payload)),
                        )
                    ]
                )

        with patch('openai.OpenAI', FakeOpenAI):
            client = OpenAICompatibleClient(model='gpt-5.5')
            result = client.create_vision_json(
                image_bytes=b'fake-image',
                mime_type='image/png',
                prompt='analyze this chart',
                schema=PRODUCT_IMAGE_ANALYSIS_SCHEMA,
                response_format_type='json_object',
                validate_schema=True,
                debug_label='product image',
            )

        self.assertEqual(captured['init_kwargs']['api_key'], 'test-key')
        self.assertEqual(captured['init_kwargs']['base_url'], 'https://gms.example/v1')
        self.assertEqual(captured['request_kwargs']['model'], 'gpt-5.5')
        self.assertEqual(captured['request_kwargs']['response_format'], {'type': 'json_object'})
        self.assertNotIn('temperature', captured['request_kwargs'])
        self.assertTrue(
            captured['request_kwargs']['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')
        )
        self.assertEqual(result['product_name'], 'Demo Chart')

    @override_settings(PRODUCT_IMAGE_ANALYSIS_ENABLE_AI=False)
    def test_product_image_analysis_can_disable_ai_vision(self):
        self.assertFalse(settings.PRODUCT_IMAGE_ANALYSIS_ENABLE_AI)


class ProductImageAnalysisApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='image-analysis-user',
            password='password1234',
            nickname='image_analysis_user',
        )
        self.personal_color = PersonalColor.objects.create(
            type_name='Image Test Tone',
            tone_key='spring_warm_light',
            base_temperature=PersonalColor.BaseTemperature.warm,
            season=PersonalColor.SeasonChoice.spring,
            tone=PersonalColor.ToneChoices.LIGHT,
            description='test',
            temperature_degree=18,
            brightness_degree=82,
            saturation_degree=40,
            turbidity_degree=55,
            glossiness_degree=40,
            contrast_degree=28,
            best_pccs=[],
            sub_pccs=[],
        )
        DiagnosisResult.objects.create(
            user=self.user,
            personal_color=self.personal_color,
            tone_key='spring_warm_light',
            personal_color_code='spring_warm_light',
            confidence_score=88,
            is_primary=True,
        )
        self.client.force_authenticate(self.user)

    def test_analyze_image_requires_image(self):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'IMAGE_REQUIRED')
        self.assertEqual(ProductImageAnalysis.objects.count(), 0)

    @patch('products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json')
    @override_settings(PRODUCT_IMAGE_ANALYSIS_ENABLE_AI=False)
    def test_analyze_image_skips_ai_when_disabled(self, mocked_vision):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['ai_used'])
        self.assertIsNone(response.data['warning'])
        mocked_vision.assert_not_called()

    @patch(
        'products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json',
        side_effect=make_bad_request_error('Error code: 400 - Model not found in request for domain api.openai.com'),
    )
    @override_settings(PRODUCT_IMAGE_ANALYSIS_MODEL='gpt-4.1', AI_DIAGNOSIS_MODEL='gpt-5.5', OPENAI_MODEL='gpt-5.5')
    def test_analyze_image_uses_local_fallback_when_model_is_unavailable(self, mocked_vision):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_status'], 'DRAFT')
        self.assertEqual(response.data['analysis_type'], 'IMAGE_COLOR_CHART')
        self.assertFalse(response.data['ai_used'])
        self.assertEqual(response.data['warning']['code'], 'AI_VISION_UNAVAILABLE_FALLBACK_USED')
        self.assertEqual(response.data['product']['source'], 'uploaded_image')
        self.assertEqual(len(response.data['options']), 2)
        self.assertEqual([option['option_name'] for option in response.data['options']], ['Option 1', 'Option 2'])
        self.assertTrue(all(option['color_source'] == 'IMAGE_EXTRACTED' for option in response.data['options']))
        self.assertTrue(all(option['analysis_status'] == 'DONE' for option in response.data['options']))
        self.assertNotEqual(response.data['options'][0]['hex_code'], response.data['options'][1]['hex_code'])
        self.assertEqual(ProductImageAnalysis.objects.count(), 1)
        mocked_vision.assert_called_once()

    @patch(
        'products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json',
        side_effect=make_authentication_error(),
    )
    def test_analyze_image_uses_local_fallback_for_authentication_error(self, mocked_vision):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['ai_used'])
        self.assertEqual(response.data['warning']['code'], 'AI_VISION_UNAVAILABLE_FALLBACK_USED')
        self.assertEqual(ProductImageAnalysis.objects.count(), 1)
        mocked_vision.assert_called_once()

    @patch(
        'products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json',
        side_effect=make_api_error(),
    )
    def test_analyze_image_uses_local_fallback_for_provider_error(self, mocked_vision):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['ai_used'])
        self.assertEqual(response.data['warning']['code'], 'AI_VISION_UNAVAILABLE_FALLBACK_USED')
        self.assertEqual(ProductImageAnalysis.objects.count(), 1)
        mocked_vision.assert_called_once()

    @patch(
        'products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json',
        side_effect=AIClientParseError('AI response was not valid JSON.'),
    )
    def test_analyze_image_uses_local_fallback_for_parse_error(self, mocked_vision):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['ai_used'])
        self.assertEqual(response.data['warning']['code'], 'AI_VISION_UNAVAILABLE_FALLBACK_USED')
        self.assertEqual(ProductImageAnalysis.objects.count(), 1)
        mocked_vision.assert_called_once()

    @patch(
        'products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json',
        side_effect=make_bad_request_error('Error code: 400 - Model not found in request for domain api.openai.com'),
    )
    def test_analyze_image_returns_no_color_candidates_when_local_extraction_fails(self, mocked_vision):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_blank_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['code'], 'NO_COLOR_CANDIDATES_FOUND')
        self.assertEqual(ProductImageAnalysis.objects.count(), 1)
        self.assertEqual(ProductImageAnalysis.objects.first().raw_ai_response['analysis_meta']['code'], 'NO_COLOR_CANDIDATES_FOUND')
        mocked_vision.assert_not_called()

    @patch('products.models.ProductImageAnalysis.objects.create', side_effect=OSError('disk full'))
    def test_analyze_image_returns_safe_json_when_initial_save_fails(self, mocked_create):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['code'], 'IMAGE_ANALYSIS_SAVE_FAILED')
        self.assertEqual(response.data['message'], 'The uploaded image could not be saved for analysis.')
        self.assertEqual(ProductImageAnalysis.objects.count(), 0)
        mocked_create.assert_called_once()

    @patch('products.services.image_color_analysis.ProductImageAnalysisPipeline.run', side_effect=RuntimeError('boom'))
    def test_analyze_image_returns_safe_json_for_unexpected_runtime_failure(self, mocked_run):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['code'], 'IMAGE_ANALYSIS_FAILED')
        self.assertEqual(response.data['message'], 'Product image analysis failed unexpectedly.')
        self.assertEqual(ProductImageAnalysis.objects.count(), 1)
        self.assertEqual(ProductImageAnalysis.objects.first().raw_ai_response['analysis_meta']['code'], 'IMAGE_ANALYSIS_FAILED')
        mocked_run.assert_called_once()

    @patch('products.services.image_color_analysis.build_tone_result_payload', side_effect=RuntimeError('bad tone payload'))
    @override_settings(PRODUCT_IMAGE_ANALYSIS_ENABLE_AI=False)
    def test_analyze_image_continues_when_tone_payload_fails(self, mocked_tone_payload):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['personalized'])
        self.assertIsNone(response.data['user_tone'])
        self.assertEqual(len(response.data['options']), 2)
        self.assertTrue(all(option['match_score'] is None for option in response.data['options']))
        mocked_tone_payload.assert_called_once()

    @patch('products.services.image_color_analysis.calculate_option_match', side_effect=RuntimeError('bad score'))
    @override_settings(PRODUCT_IMAGE_ANALYSIS_ENABLE_AI=False)
    def test_analyze_image_retries_without_personalization_when_scoring_fails(self, mocked_match):
        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['personalized'])
        self.assertIsNone(response.data['user_tone'])
        self.assertEqual(len(response.data['options']), 2)
        self.assertTrue(all(option['match_score'] is None for option in response.data['options']))
        mocked_match.assert_called()

    @patch('products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json')
    def test_analyze_image_creates_draft_and_extracts_colors(self, mocked_vision):
        mocked_vision.return_value = {
            'product_name': '3CE GUMMY OIL TINT',
            'brand_name': '3CE',
            'chart_labels': {
                'warm_label': 'Warm',
                'cool_label': 'Cool',
                'light_label': 'Light',
                'deep_label': 'Deep',
                'best_region_labels': ['WARM BEST', 'COOL BEST'],
                'season_labels': ['SPRING', 'SUMMER'],
            },
            'options': [
                {
                    'option_name': '베이글 피치',
                    'display_name': '베이글 피치',
                    'confidence': 0.93,
                    'ai_estimated_hex': '',
                    'blob_box': {'x': 8, 'y': 16, 'width': 28, 'height': 34},
                },
                {
                    'option_name': '모브 젤리',
                    'display_name': '모브 젤리',
                    'confidence': 0.91,
                    'ai_estimated_hex': '',
                    'blob_box': {'x': 54, 'y': 24, 'width': 28, 'height': 34},
                },
            ],
        }

        response = self.client.post(
            '/api/products/analyze-image/',
            {
                'image': make_chart_upload(),
                'product_name': '',
                'brand_name': '',
                'category': Product.Category.LIP,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source'], 'IMAGE_CHART')
        self.assertEqual(response.data['analysis_type'], 'IMAGE_COLOR_CHART')
        self.assertTrue(response.data['ai_used'])
        self.assertIsNone(response.data['warning'])
        self.assertFalse(response.data['confirmed'])
        self.assertEqual(response.data['product']['product_name'], '3CE GUMMY OIL TINT')
        self.assertEqual(response.data['product']['source'], 'uploaded_image')
        self.assertEqual(len(response.data['options']), 2)
        self.assertTrue(all(option['hex_code'] for option in response.data['options']))
        self.assertTrue(all(option['color_source'] == 'IMAGE_EXTRACTED' for option in response.data['options']))
        self.assertNotEqual(response.data['options'][0]['hex_code'], response.data['options'][1]['hex_code'])
        self.assertEqual(response.data['options'][0]['option_no'], '01')
        self.assertIn(response.data['options'][0]['grade'], ['BEST', 'GOOD', 'CAUTION'])

    @patch('products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json')
    def test_ai_name_failure_does_not_turn_local_colors_into_pending(self, mocked_vision):
        mocked_vision.return_value = {
            'product_name': 'Blank Chart',
            'brand_name': 'Demo',
            'chart_labels': {
                'warm_label': 'Warm',
                'cool_label': 'Cool',
                'light_label': 'Light',
                'deep_label': 'Deep',
                'best_region_labels': [],
                'season_labels': [],
            },
            'options': [
                {
                    'option_name': '색상 확인 필요',
                    'display_name': '색상 확인 필요',
                    'confidence': 0.62,
                    'ai_estimated_hex': '',
                    'blob_box': {'x': 88, 'y': 88, 'width': 8, 'height': 8},
                },
            ],
        }

        response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        done_options = [option for option in response.data['options'] if option['analysis_status'] == 'DONE']
        self.assertGreaterEqual(len(done_options), 2)
        self.assertTrue(all(option['grade'] != 'PENDING' for option in done_options))

    @patch('products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json')
    def test_review_patch_marks_user_edited_and_confirm_locks(self, mocked_vision):
        mocked_vision.return_value = {
            'product_name': '3CE GUMMY OIL TINT',
            'brand_name': '3CE',
            'chart_labels': {
                'warm_label': 'Warm',
                'cool_label': 'Cool',
                'light_label': 'Light',
                'deep_label': 'Deep',
                'best_region_labels': ['WARM BEST'],
                'season_labels': ['SPRING'],
            },
            'options': [
                {
                    'option_name': '베이글 피치',
                    'display_name': '베이글 피치',
                    'confidence': 0.88,
                    'ai_estimated_hex': '',
                    'blob_box': {'x': 8, 'y': 16, 'width': 28, 'height': 34},
                },
            ],
        }

        create_response = self.client.post(
            '/api/products/analyze-image/',
            {'image': make_chart_upload(), 'category': Product.Category.LIP},
        )
        analysis_id = create_response.data['analysis_id']
        option = create_response.data['options'][0]

        patch_response = self.client.patch(
            f'/api/products/image-analyses/{analysis_id}/',
            {
                'product_name': '3CE GUMMY OIL TINT EDITED',
                'options': [
                    {
                        'id': option['id'],
                        'option_name': '베이글 피치',
                        'display_name': '베이글 피치 수정',
                        'hex_code': '#C26A5E',
                        'chart_x': option['chart_x'],
                        'chart_y': option['chart_y'],
                    }
                ],
            },
            format='json',
        )

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        patched_option = patch_response.data['options'][0]
        self.assertEqual(patch_response.data['product']['product_name'], '3CE GUMMY OIL TINT EDITED')
        self.assertEqual(patched_option['display_name'], '베이글 피치 수정')
        self.assertEqual(patched_option['color_source'], 'USER_EDITED')
        self.assertEqual(patched_option['hex_code'], '#C26A5E')

        confirm_response = self.client.post(f'/api/products/image-analyses/{analysis_id}/confirm/')
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertTrue(confirm_response.data['confirmed'])

        rejected_patch = self.client.patch(
            f'/api/products/image-analyses/{analysis_id}/',
            {'options': [{'id': patched_option['id'], 'removed': True}]},
            format='json',
        )
        self.assertEqual(rejected_patch.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rejected_patch.data['code'], 'INVALID_REVIEW_UPDATE')

    @patch('products.services.image_color_analysis.OpenAICompatibleClient.create_vision_json')
    def test_image_analysis_list_only_returns_current_user_records(self, mocked_vision):
        other_user = get_user_model().objects.create_user(
            username='other-image-user',
            password='password1234',
            nickname='other_image_user',
        )
        mocked_vision.return_value = {
            'product_name': 'Demo Chart',
            'brand_name': 'Demo',
            'chart_labels': {
                'warm_label': 'Warm',
                'cool_label': 'Cool',
                'light_label': 'Light',
                'deep_label': 'Deep',
                'best_region_labels': [],
                'season_labels': [],
            },
            'options': [
                {
                    'option_name': '베이글 피치',
                    'display_name': '베이글 피치',
                    'confidence': 0.8,
                    'ai_estimated_hex': '',
                    'blob_box': {'x': 8, 'y': 16, 'width': 28, 'height': 34},
                },
            ],
        }

        self.client.post('/api/products/analyze-image/', {'image': make_chart_upload(), 'category': Product.Category.LIP})
        self.client.force_authenticate(other_user)
        self.client.post('/api/products/analyze-image/', {'image': make_chart_upload(), 'category': Product.Category.LIP})
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/products/image-analyses/?limit=5')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product_name'], 'Demo Chart')
