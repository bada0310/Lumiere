from django.db import models

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator


class Product(models.Model):
    class Category(models.TextChoices):
        LIP = 'LIP', '립'
        EYE = 'EYE', '아이'
        CHEEK = 'CHEEK', '치크'
        BASE = 'BASE', '베이스'
        LENS = 'LENS', '렌즈'
        ETC = 'ETC', '기타'

    brand = models.CharField(max_length=80)
    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ETC,
    )
    image_url = models.URLField(blank=True)
    product_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    match_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand', 'name']

    def __str__(self):
        return f'{self.brand} {self.name}'


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    content = models.TextField()
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'author'],
                name='unique_review_per_product_author',
            )
        ]

    def __str__(self):
        return f'{self.product} - {self.rating}'
