import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

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
from .services.url_color_analysis import extract_oliveyoung_goods_no


class FakeHttpResponse:
    def __init__(self, body='', *, url='https://example.com/', status_code=200, content_type='text/html; charset=utf-8'):
        self.body = body.encode('utf-8')
        self.url = url
        self.status = status_code
        self.code = status_code
        self.headers = {'Content-Type': content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, *args):
        return self.body

    def geturl(self):
        return self.url


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


class ProductColorAnalysisApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='analysis-user',
            password='password1234',
            nickname='analysis_user',
        )

    def test_color_analysis_rejects_invalid_url_with_safe_json(self):
        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'not-a-url'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_url')
        self.assertNotIn('<html', response.data['detail'].lower())

    @patch('products.views.analyze_product_color_url')
    def test_color_analysis_endpoint_returns_payload(self, mocked_analyze):
        mocked_analyze.return_value = {
            'product': {'url': 'https://example.com/product', 'product_name': 'Test Tint'},
            'user_tone': None,
            'personalized': False,
            'options': [],
            'recommendation_groups': {'BEST': [], 'GOOD': [], 'CAUTION': []},
        }
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://example.com/product'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product']['product_name'], 'Test Tint')
        mocked_analyze.assert_called_once_with('https://example.com/product', user=self.user)

    def test_extracts_oliveyoung_goods_no(self):
        url = 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056&trackingCd=test'

        self.assertEqual(extract_oliveyoung_goods_no(url), 'A000000207056')

    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.url_color_analysis.urlopen')
    def test_oliveyoung_url_analysis_returns_partial_success_without_options(self, mocked_urlopen, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.return_value = FakeHttpResponse(
            '''
            <html>
              <head>
                <meta property="og:title" content="롬앤 쥬시 래스팅 틴트">
                <meta property="og:image" content="https://image.example/tint.jpg">
                <meta name="description" content="립틴트 상품">
              </head>
              <body><span class="brand">romand</span></body>
            </html>
            ''',
            url='https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056',
        )

        response = self.client.post(
            '/api/products/color-analysis/',
            {
                'product_url': (
                    'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?'
                    'goodsNo=A000000207056&trackingCd=Cat'
                )
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['source'], 'OLIVEYOUNG')
        self.assertEqual(response.data['goods_no'], 'A000000207056')
        self.assertEqual(response.data['normalized_url'], 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056')
        self.assertEqual(response.data['product']['product_name'], '롬앤 쥬시 래스팅 틴트')
        self.assertEqual(response.data['options'], [])

    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.url_color_analysis.urlopen')
    def test_oliveyoung_short_url_resolves_before_analysis(self, mocked_urlopen, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        final_url = 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056&trackingCd=short'
        mocked_urlopen.side_effect = [
            FakeHttpResponse('', url=final_url),
            FakeHttpResponse('<meta property="og:title" content="Short Tint">', url=final_url),
        ]

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://oy.run/kuIDk8W4ng2dG6'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['goods_no'], 'A000000207056')
        self.assertEqual(response.data['source'], 'OLIVEYOUNG')
        self.assertEqual(mocked_urlopen.call_count, 2)

    @patch('products.services.url_color_analysis.fetch_oliveyoung_with_browser')
    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.url_color_analysis.urlopen')
    def test_oliveyoung_http_failure_uses_browser_fallback(
        self,
        mocked_urlopen,
        mocked_getaddrinfo,
        mocked_browser_fetch,
    ):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.side_effect = HTTPError(
            'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056',
            502,
            'Bad Gateway',
            hdrs=None,
            fp=None,
        )
        mocked_browser_fetch.return_value = (
            '<meta property="og:title" content="Browser Tint">',
            'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056',
        )

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_status'], 'COMPLETE')
        self.assertEqual(response.data['product']['product_name'], 'Browser Tint')
        mocked_browser_fetch.assert_called_once()

    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.url_color_analysis.urlopen')
    def test_oliveyoung_fetch_forbidden_returns_safe_json(self, mocked_urlopen, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.side_effect = HTTPError(
            'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056',
            403,
            'Forbidden',
            hdrs=None,
            fp=None,
        )

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000207056'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['analysis_status'], 'PARTIAL')
        self.assertEqual(response.data['goods_no'], 'A000000207056')
        self.assertEqual(response.data['message'], '상품 번호를 확인했습니다. 상세 상품 정보는 자동으로 가져오지 못했습니다.')
        return
        self.assertEqual(
            response.data['message'],
            '상품 번호를 확인했습니다. 상세 상품 정보는 자동으로 가져오지 못했습니다.',
        )

    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.url_color_analysis.urlopen')
    def test_oliveyoung_short_url_resolve_failure_returns_safe_json(self, mocked_urlopen, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.side_effect = URLError('short url failed')

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://oy.run/kuIDk8W4ng2dG6'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['code'], 'SHORT_URL_RESOLVE_FAILED')
        self.assertNotIn('<html', response.data['message'].lower())

    @patch('products.services.threece_analysis.extract_rendered_swatch_candidates', return_value=[])
    @patch('products.services.threece_analysis.dominant_color_from_image_url')
    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.threece_analysis.urlopen')
    def test_threece_url_analysis_extracts_real_options_and_colors(
        self,
        mocked_urlopen,
        mocked_getaddrinfo,
        mocked_dominant_color,
        mocked_rendered_candidates,
    ):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_dominant_color.return_value = (180, 72, 104)
        mocked_urlopen.return_value = FakeHttpResponse(
            '''
            <html>
              <head>
                <meta property="og:title" content="3CE GUMMY OIL TINT">
                <meta property="og:description" content="Glossy oil tint">
                <meta property="og:image" content="https://image.example/3ce-tint.jpg">
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "Product",
                  "name": "3CE GUMMY OIL TINT",
                  "brand": {"@type": "Brand", "name": "3CE"},
                  "description": "Glossy oil tint",
                  "image": "https://image.example/json-tint.jpg",
                  "offers": {"@type": "Offer", "price": "17000"}
                }
                </script>
              </head>
              <body>
                <nav>LIP TINT CE Gummy Oil Tint CE</nav>
                <div class="product-color-swatches">
                  <button class="color-swatch" data-option-name="BAGEL PEACH" style="background-color: #C94D5F;">BAGEL PEACH</button>
                  <button class="color-swatch" data-option-name="MELTING GUMMY">
                    <img src="https://image.example/melting-gummy.png" alt="MELTING GUMMY">
                  </button>
                  <button class="color-swatch" data-option-name="GLOWY">GLOWY</button>
                  <button class="color-swatch" data-option-name="ROSE GUMMY">ROSE GUMMY</button>
                  <button class="color-swatch" data-option-name="MAUVE JELLY">MAUVE JELLY</button>
                  <button class="color-swatch" data-option-name="SUMMER BITE">SUMMER BITE</button>
                </div>
                <section>Description</section>
              </body>
            </html>
            ''',
            url='https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint?variant=%EB%B2%A0%EC%9D%B4%EA%B8%80+%ED%94%BC%EC%B9%98',
        )

        response = self.client.post(
            '/api/products/color-analysis/',
            {
                'product_url': (
                    'https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint?'
                    'variant=%EB%B2%A0%EC%9D%B4%EA%B8%80+%ED%94%BC%EC%B9%98'
                )
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['source'], 'THREE_CE')
        self.assertEqual(response.data['selected_option'], '베이글 피치')
        self.assertEqual(response.data['product']['brand_name'], '3CE')
        self.assertEqual(response.data['product']['product_name'], '3CE GUMMY OIL TINT')
        self.assertEqual(response.data['product']['price'], 17000)
        self.assertEqual(response.data['product']['category'], Product.Category.LIP)
        self.assertEqual(response.data['best_option']['option_name'], 'BAGEL PEACH')
        self.assertEqual(response.data['best_option']['display_name'], '베이글 피치')
        self.assertTrue(response.data['best_option']['is_selected'])

        names = [option['option_name'] for option in response.data['options']]
        self.assertIn('BAGEL PEACH', names)
        self.assertIn('MELTING GUMMY', names)
        self.assertIn('GLOWY', names)
        self.assertIn('ROSE GUMMY', names)
        self.assertIn('MAUVE JELLY', names)
        self.assertIn('SUMMER BITE', names)
        self.assertIn('DEW ON', names)
        self.assertNotIn('LIP TINT', names)
        self.assertNotIn('CE Gummy Oil Tint', names)
        self.assertNotIn('CE', names)

        bagel = next(option for option in response.data['options'] if option['option_name'] == 'BAGEL PEACH')
        melting = next(option for option in response.data['options'] if option['option_name'] == 'MELTING GUMMY')
        pending = next(option for option in response.data['options'] if option['option_name'] == 'GLOWY')
        self.assertEqual(bagel['hex_code'], '#C94D5F')
        self.assertEqual(bagel['analysis_status'], 'DONE')
        self.assertIsNotNone(bagel['color_metrics'])
        self.assertEqual(melting['hex_code'], '#B44868')
        self.assertEqual(melting['analysis_status'], 'DONE')
        self.assertIsNone(pending['hex_code'])
        self.assertIsNone(pending['match_score'])
        self.assertEqual(pending['grade'], 'PENDING')
        self.assertEqual(pending['analysis_status'], 'PENDING_COLOR_ANALYSIS')

    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.threece_analysis.urlopen')
    def test_threece_fetch_failure_returns_safe_json(self, mocked_urlopen, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.side_effect = URLError('blocked')

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['code'], 'THREE_CE_ANALYSIS_FAILED')
        self.assertNotIn('<html', response.data['message'].lower())
        self.assertNotIn('blocked', response.data['message'].lower())

    @patch('products.services.threece_analysis.extract_rendered_swatch_candidates', return_value=[])
    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.threece_analysis.urlopen')
    def test_threece_parse_failure_returns_safe_json(self, mocked_urlopen, mocked_getaddrinfo, mocked_rendered_candidates):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.return_value = FakeHttpResponse(
            '<html><head><meta property="og:title" content="3CE UNKNOWN"></head><body>No variants here</body></html>',
            url='https://www.3cecosmetics.co.kr/all-products/unknown-product',
        )

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://www.3cecosmetics.co.kr/all-products/unknown-product'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['code'], 'THREE_CE_PARSE_FAILED')
        self.assertNotIn('<html', response.data['message'].lower())

    @patch('products.services.threece_analysis.extract_rendered_swatch_candidates')
    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.threece_analysis.urlopen')
    def test_threece_embedded_json_colors_are_used_before_rendered_dom(
        self,
        mocked_urlopen,
        mocked_getaddrinfo,
        mocked_rendered_candidates,
    ):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.return_value = FakeHttpResponse(
            '''
            <html>
              <head>
                <meta property="og:title" content="3CE GUMMY OIL TINT">
                <script>
                  window.__PRODUCT__ = {
                    "variants": [
                      {"name": "BAGEL PEACH", "hex": "#C94D5F"},
                      {"name": "MELTING GUMMY", "hex": "#B44868"},
                      {"name": "GLOWY", "hex": "#D87888"},
                      {"name": "ROSE GUMMY", "hex": "#A84657"},
                      {"name": "MAUVE JELLY", "hex": "#8E536A"},
                      {"name": "SUMMER BITE", "hex": "#DA4F5C"}
                    ]
                  }
                </script>
              </head>
              <body><div id="app"></div></body>
            </html>
            ''',
            url='https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint',
        )

        response = self.client.post(
            '/api/products/color-analysis/',
            {'product_url': 'https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bagel = next(option for option in response.data['options'] if option['option_name'] == 'BAGEL PEACH')
        summer = next(option for option in response.data['options'] if option['option_name'] == 'SUMMER BITE')
        pending = next(option for option in response.data['options'] if option['option_name'] == 'DEW ON')
        self.assertEqual(bagel['hex_code'], '#C94D5F')
        self.assertEqual(summer['analysis_status'], 'DONE')
        self.assertEqual(pending['grade'], 'PENDING')
        self.assertIsNone(pending['match_score'])
        mocked_rendered_candidates.assert_not_called()

    @patch('products.services.threece_analysis.extract_rendered_swatch_candidates')
    @patch('products.services.url_color_analysis.socket.getaddrinfo')
    @patch('products.services.threece_analysis.urlopen')
    def test_threece_rendered_dom_colors_fill_known_options_and_select_taupe_drop(
        self,
        mocked_urlopen,
        mocked_getaddrinfo,
        mocked_rendered_candidates,
    ):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.return_value = FakeHttpResponse(
            '''
            <html>
              <head><meta property="og:title" content="3CE GUMMY OIL TINT"></head>
              <body><div id="app"><!-- Vue renders shadeSelector later --></div></body>
            </html>
            ''',
            url='https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint?variant=%ED%86%A0%ED%94%84+%EB%93%9C%EB%A1%AD',
        )
        mocked_rendered_candidates.return_value = [
            {'name': 'BAGEL PEACH', 'hex_code': 'rgb(201, 77, 95)', 'source': 'rendered-dom'},
            {'name': 'MELTING GUMMY', 'hex_code': 'rgb(180, 72, 104)', 'source': 'rendered-dom'},
            {'name': 'GLOWY', 'hex_code': 'rgb(216, 120, 136)', 'source': 'rendered-dom'},
            {'name': 'ROSE GUMMY', 'hex_code': 'rgb(168, 70, 87)', 'source': 'rendered-dom'},
            {'name': 'MAUVE JELLY', 'hex_code': 'rgb(142, 83, 106)', 'source': 'rendered-dom'},
            {'name': 'SUMMER BITE', 'hex_code': 'rgb(218, 79, 92)', 'source': 'rendered-dom'},
            {'name': 'DEW ON', 'hex_code': 'rgb(235, 137, 135)', 'source': 'rendered-dom'},
            {'name': 'TAUPE DROP', 'hex_code': 'rgb(111, 59, 61)', 'source': 'rendered-dom'},
        ]

        response = self.client.post(
            '/api/products/color-analysis/',
            {
                'product_url': (
                    'https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint?'
                    'variant=%ED%86%A0%ED%94%84+%EB%93%9C%EB%A1%AD'
                )
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['selected_option'], '\ud1a0\ud504 \ub4dc\ub86d')
        self.assertEqual(response.data['best_option']['option_name'], 'TAUPE DROP')
        self.assertTrue(response.data['best_option']['is_selected'])
        taupe = next(option for option in response.data['options'] if option['option_name'] == 'TAUPE DROP')
        self.assertEqual(taupe['display_name'], '\ud1a0\ud504 \ub4dc\ub86d')
        self.assertEqual(taupe['hex_code'], '#6F3B3D')
        self.assertEqual(taupe['analysis_status'], 'DONE')
        self.assertIsNotNone(taupe['color_metrics'])
        names = [option['option_name'] for option in response.data['options']]
        self.assertNotIn('LIP TINT', names)
        self.assertNotIn('CE', names)
        mocked_rendered_candidates.assert_called_once()

    def test_threece_rendered_entries_assign_known_option_order(self):
        from products.services.threece_analysis import rendered_entries_to_candidates

        candidates = rendered_entries_to_candidates(
            [
                {'backgroundColor': 'rgb(201, 77, 95)', 'backgroundImage': 'none'},
                {'backgroundColor': 'rgb(180, 72, 104)', 'backgroundImage': 'none'},
                {'backgroundColor': 'rgba(0, 0, 0, 0)', 'backgroundImage': 'none'},
            ],
            'https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint',
        )

        self.assertEqual(candidates[0]['name'], 'BAGEL PEACH')
        self.assertEqual(candidates[0]['hex_code'], '#C94D5F')
        self.assertEqual(candidates[1]['name'], 'MELTING GUMMY')
        self.assertEqual(candidates[1]['hex_code'], '#B44868')
        self.assertEqual(len(candidates), 2)

    @patch('products.services.threece_analysis.extract_rendered_swatch_candidates', return_value=[])
    @patch('products.services.scraping.http_client.socket.getaddrinfo')
    @patch('products.services.threece_analysis.urlopen')
    def test_product_scrape_endpoint_returns_unified_3ce_schema(self, mocked_urlopen, mocked_getaddrinfo, mocked_rendered_candidates):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.return_value = FakeHttpResponse(
            '''
            <html>
              <head>
                <meta property="og:title" content="3CE GUMMY OIL TINT">
                <meta property="og:image" content="https://image.example/3ce-tint.jpg">
              </head>
              <body>
                <div class="product-color-swatches">
                  <button class="color-swatch" data-option-name="BAGEL PEACH" style="background-color: #C94D5F;">BAGEL PEACH</button>
                  <button class="color-swatch" data-option-name="MELTING GUMMY">MELTING GUMMY</button>
                </div>
              </body>
            </html>
            ''',
            url='https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint',
        )

        response = self.client.post(
            '/api/products/scrape/',
            {'product_url': 'https://www.3cecosmetics.co.kr/all-products/lips/lip-tint/3ce-gummy-oil-tint'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {'product_name', 'brand', 'options'})
        self.assertEqual(response.data['product_name'], '3CE GUMMY OIL TINT')
        self.assertEqual(response.data['brand'], '3CE')
        names = [option['option_name'] for option in response.data['options']]
        self.assertIn('BAGEL PEACH', names)
        bagel = next(option for option in response.data['options'] if option['option_name'] == 'BAGEL PEACH')
        self.assertEqual(bagel['color_code'], '#C94D5F')
        self.assertEqual(bagel['image_url'], 'https://image.example/3ce-tint.jpg')

    @patch('products.services.scraping.http_client.socket.getaddrinfo')
    @patch('products.services.scraping.http_client.urlopen')
    def test_product_scrape_short_url_failure_returns_safe_json(self, mocked_urlopen, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_urlopen.side_effect = URLError('short url blocked')

        response = self.client.post(
            '/api/products/scrape/',
            {'product_url': 'https://oy.run/kuIDk8W4ng2dG6'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'fail')
        self.assertEqual(response.data['code'], 'SHORT_URL_RESOLVE_FAILED')
        self.assertNotIn('blocked', response.data['message'].lower())
        self.assertNotIn('<html', response.data['message'].lower())

    @patch('products.services.scraping.http_client.socket.getaddrinfo')
    @patch('products.services.scraping.scrapers.render_html')
    def test_product_scrape_generic_fallback_uses_browser_rendered_html(self, mocked_render_html, mocked_getaddrinfo):
        mocked_getaddrinfo.return_value = [(None, None, None, None, ('23.1.1.1', 443))]
        mocked_render_html.return_value = (
            '''
            <html>
              <head>
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "Product",
                  "name": "Generic Lip Tint",
                  "brand": {"@type": "Brand", "name": "Demo Brand"},
                  "image": "https://image.example/generic.jpg"
                }
                </script>
              </head>
              <body>
                <button class="color-option" aria-label="Rose" style="background-color:#E98FA2">Rose</button>
              </body>
            </html>
            ''',
            'https://shop.example/products/1',
        )

        response = self.client.post(
            '/api/products/scrape/',
            {'product_url': 'https://shop.example/products/1'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_name'], 'Generic Lip Tint')
        self.assertEqual(response.data['brand'], 'Demo Brand')
        self.assertEqual(response.data['options'][0]['color_code'], '#E98FA2')
        mocked_render_html.assert_called_once()

    def test_color_metrics_builds_chart_values(self):
        metrics = build_color_metrics((233, 143, 162))

        self.assertEqual(metrics['hex_code'], '#E98FA2')
        self.assertGreaterEqual(metrics['brightness'], 0)
        self.assertLessEqual(metrics['brightness'], 100)
        self.assertEqual(metrics['chart_x'], metrics['coolness'])
        self.assertEqual(metrics['chart_y'], 100 - metrics['brightness'])
        self.assertEqual(public_grade_from_score(86), 'BEST')
        self.assertEqual(public_grade_from_score(65), 'GOOD')
        self.assertEqual(public_grade_from_score(30), 'CAUTION')


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
        self.assertEqual(ProductImageAnalysis.objects.count(), 0)
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
        self.assertEqual(ProductImageAnalysis.objects.count(), 0)
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
