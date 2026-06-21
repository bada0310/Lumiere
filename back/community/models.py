from django.db import models
from django.conf import settings


class Post(models.Model):
    class Category(models.TextChoices):
        LIFE_ITEM = 'LIFE_ITEM', '인생템 공유'
        COLOR_REVIEW = 'COLOR_REVIEW', '발색 리뷰'
        QUESTION = 'QUESTION', '질문'
        PRODUCT_RECOMMENDATION = 'PRODUCT_RECOMMENDATION', '제품 추천'
        ROUTINE = 'ROUTINE', '메이크업 루틴'
        FREE = 'FREE', '자유'

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',
    )
    title = models.CharField(max_length=120)
    content = models.TextField()
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.FREE,
    )
    products = models.ManyToManyField(
        'products.Product',
        related_name='mentioned_posts',
        blank=True,
    )
    image_url = models.URLField(blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comments',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} - {self.post}'


class PostLike(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_community_post_like',
            )
        ]

    def __str__(self):
        return f'{self.user} likes {self.post}'


class CommentLike(models.Model):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comment_likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['comment', 'user'],
                name='unique_community_comment_like',
            )
        ]

    def __str__(self):
        return f'{self.user} likes comment {self.comment_id}'
