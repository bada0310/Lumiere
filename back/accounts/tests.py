from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from community.models import Comment, CommentLike, Post, PostLike
from diagnosis.models import DiagnosisResult, PersonalColor
from engagements.models import LikedProductOption, UrlAnalysisRecord
from products.models import Product


class CurrentUserDeleteApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='delete_me',
            password='password1234',
            email='delete@example.com',
            nickname='delete_nick',
        )
        self.product = Product.objects.create(
            brand='brand',
            name='product',
            category=Product.Category.LIP,
        )
        self.personal_color = PersonalColor.objects.create(
            type_name='Test Tone',
            tone_key='test_tone',
            base_temperature=PersonalColor.BaseTemperature.cool,
            season=PersonalColor.SeasonChoice.summer,
            tone=PersonalColor.ToneChoices.MUTE,
            description='test',
            temperature_degree=70,
            brightness_degree=50,
            saturation_degree=50,
            turbidity_degree=50,
            glossiness_degree=50,
            contrast_degree=50,
            best_pccs=[],
            sub_pccs=[],
        )

    def test_requires_exact_confirmation(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            '/accounts/user/',
            {'confirmation': '삭제합니다', 'password': 'password1234'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())

    def test_requires_password_for_password_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            '/accounts/user/',
            {'confirmation': '탈퇴합니다', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())

    def test_hard_deletes_user_and_related_records(self):
        post = Post.objects.create(author=self.user, title='post', content='content')
        comment = Comment.objects.create(post=post, author=self.user, content='comment')
        PostLike.objects.create(post=post, user=self.user)
        CommentLike.objects.create(comment=comment, user=self.user)
        DiagnosisResult.objects.create(
            user=self.user,
            personal_color=self.personal_color,
            confidence_score=80,
            tone_key='test_tone',
        )
        LikedProductOption.objects.create(
            user=self.user,
            product=self.product,
            option_id=str(self.product.id),
        )
        UrlAnalysisRecord.objects.create(
            user=self.user,
            source_url='https://example.com/product',
            title='analysis',
        )
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            '/accounts/user/',
            {'confirmation': '탈퇴합니다', 'password': 'password1234'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(get_user_model().objects.filter(username='delete_me').exists())
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(PostLike.objects.count(), 0)
        self.assertEqual(CommentLike.objects.count(), 0)
        self.assertEqual(DiagnosisResult.objects.count(), 0)
        self.assertEqual(LikedProductOption.objects.count(), 0)
        self.assertEqual(UrlAnalysisRecord.objects.count(), 0)

    def test_unusable_password_user_can_delete_with_confirmation_only(self):
        social_user = get_user_model().objects.create_user(
            username='social',
            email='social@example.com',
            nickname='social_nick',
        )
        social_user.set_unusable_password()
        social_user.save()
        self.client.force_authenticate(social_user)

        response = self.client.delete(
            '/accounts/user/',
            {'confirmation': '탈퇴합니다'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(get_user_model().objects.filter(username='social').exists())
