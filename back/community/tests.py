from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product

from .models import Comment, CommentLike, Post, PostLike


class CommunityApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='writer',
            password='password1234',
            nickname='writer_nick',
        )
        self.product = Product.objects.create(
            brand='클리오',
            name='프로 아이 팔레트',
            category=Product.Category.EYE,
        )

    def test_authenticated_user_can_create_post_with_product_tags(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/community/posts/',
            {
                'title': '여쿨라 조합 추천',
                'content': '이 팔레트랑 틴트 조합이 좋아요.',
                'category': Post.Category.LIFE_ITEM,
                'product_ids': [self.product.id],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().products.count(), 1)

    def test_authenticated_user_can_toggle_like(self):
        post = Post.objects.create(
            author=self.user,
            title='발색 리뷰',
            content='맑은 발색입니다.',
            category=Post.Category.COLOR_REVIEW,
        )
        self.client.force_authenticate(self.user)

        liked = self.client.post(f'/api/community/posts/{post.id}/like/')
        unliked = self.client.post(f'/api/community/posts/{post.id}/like/')

        self.assertEqual(liked.status_code, status.HTTP_201_CREATED)
        self.assertEqual(unliked.status_code, status.HTTP_200_OK)
        self.assertEqual(PostLike.objects.count(), 0)

    def test_authenticated_user_can_create_comment_on_post(self):
        post = Post.objects.create(
            author=self.user,
            title='질문',
            content='립 추천해주세요.',
            category=Post.Category.QUESTION,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            f'/api/community/posts/{post.id}/comments/',
            {'content': '이 제품 좋아요.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_authenticated_user_can_toggle_comment_like(self):
        post = Post.objects.create(
            author=self.user,
            title='질문',
            content='립 추천해주세요.',
            category=Post.Category.QUESTION,
        )
        comment = Comment.objects.create(
            post=post,
            author=self.user,
            content='이 제품 좋아요.',
        )
        self.client.force_authenticate(self.user)

        liked = self.client.post(f'/api/community/comments/{comment.id}/like/')
        unliked = self.client.post(f'/api/community/comments/{comment.id}/like/')

        self.assertEqual(liked.status_code, status.HTTP_201_CREATED)
        self.assertEqual(unliked.status_code, status.HTTP_200_OK)
        self.assertEqual(CommentLike.objects.count(), 0)
