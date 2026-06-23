from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from diagnosis.models import DiagnosisResult, PersonalColor
from .models import Product, ProductOffer, ProductOption, ProductOptionToneScore, Review


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
