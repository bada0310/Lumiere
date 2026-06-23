from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product, ProductOption

from .models import LikedProductOption, UrlAnalysisRecord


class EngagementApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='engagement_user',
            password='password1234',
            nickname='engagement_nick',
        )
        self.products = [
            Product.objects.create(
                brand='brand',
                name=f'product {index}',
                category=Product.Category.LIP,
                canonical_key=f'brand|lip|product-{index}',
            )
            for index in range(3)
        ]
        self.options = [
            ProductOption.objects.create(
                product=product,
                option_no=f'{index + 1:02d}',
                option_name=f'option {index}',
                option_key=f'option-{index}',
                analyzed_tone_tag='spring_warm_light',
            )
            for index, product in enumerate(self.products)
        ]

    def test_liked_options_support_limit_and_pagination(self):
        for product, option in zip(self.products, self.options):
            LikedProductOption.objects.create(
                user=self.user,
                product=product,
                product_option=option,
                option_id=str(option.id),
                name=product.name,
            )
        self.client.force_authenticate(self.user)

        preview = self.client.get('/api/engagements/liked-options/?limit=2')
        page = self.client.get('/api/engagements/liked-options/?page=1&page_size=2')

        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertEqual(len(preview.data), 2)
        returned_option_ids = {row['product_option']['id'] for row in preview.data}
        self.assertTrue(returned_option_ids.issubset({option.id for option in self.options}))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        self.assertEqual(page.data['count'], 3)
        self.assertEqual(len(page.data['results']), 2)

    def test_can_toggle_liked_option(self):
        self.client.force_authenticate(self.user)

        liked = self.client.post(
            '/api/engagements/liked-options/toggle/',
            {
                'product_option_id': self.options[0].id,
                'brand': 'brand',
                'name': 'product 0',
            },
            format='json',
        )
        unliked = self.client.post(
            '/api/engagements/liked-options/toggle/',
            {
                'product_option_id': self.options[0].id,
            },
            format='json',
        )

        self.assertEqual(liked.status_code, status.HTTP_201_CREATED)
        self.assertTrue(liked.data['is_liked'])
        self.assertEqual(liked.data['item']['product_option']['id'], self.options[0].id)
        self.assertEqual(unliked.status_code, status.HTTP_200_OK)
        self.assertFalse(unliked.data['is_liked'])
        self.assertEqual(LikedProductOption.objects.count(), 0)

    def test_url_analysis_records_support_limit_and_pagination(self):
        for index in range(3):
            UrlAnalysisRecord.objects.create(
                user=self.user,
                source_url=f'https://example.com/products/{index}',
                title=f'analysis {index}',
            )
        self.client.force_authenticate(self.user)

        preview = self.client.get('/api/engagements/url-analyses/?limit=2')
        page = self.client.get('/api/engagements/url-analyses/?page=1&page_size=2')

        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertEqual(len(preview.data), 2)
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        self.assertEqual(page.data['count'], 3)
        self.assertEqual(len(page.data['results']), 2)
