from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product, Review


class ProductReviewApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='reviewer',
            password='password1234',
            nickname='reviewer_nick',
        )
        self.product = Product.objects.create(
            brand='롬앤',
            name='쥬시 래스팅 틴트',
            category=Product.Category.LIP,
            match_score=92,
        )

    def test_product_list_returns_products(self):
        response = self.client.get('/api/products/items/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['brand'], '롬앤')

    def test_authenticated_user_can_create_review(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/products/reviews/',
            {
                'product': self.product.id,
                'rating': 5,
                'content': '쿨톤에게 잘 맞아요.',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

# Create your tests here.
