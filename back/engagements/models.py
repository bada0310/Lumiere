from django.conf import settings
from django.db import models
from django.utils import timezone


class LikedProductOption(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='liked_product_options',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='liked_by_users',
    )
    product_option = models.ForeignKey(
        'products.ProductOption',
        on_delete=models.CASCADE,
        related_name='liked_by_users',
        null=True,
        blank=True,
    )
    option_id = models.CharField(max_length=120, blank=True)
    group_key = models.CharField(max_length=200, blank=True, db_index=True)
    brand = models.CharField(max_length=120, blank=True)
    name = models.CharField(max_length=300, blank=True)
    option = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    product_url = models.URLField(max_length=1000, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product', 'option_id'],
                name='unique_liked_product_option',
            )
        ]

    def __str__(self):
        return f'{self.user_id} likes {self.product_id}'


class UrlAnalysisRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='url_analysis_records',
    )
    source_url = models.URLField(max_length=1000)
    title = models.CharField(max_length=300, blank=True)
    brand = models.CharField(max_length=120, blank=True)
    product_name = models.CharField(max_length=300, blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    colors = models.JSONField(default=list, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.source_url


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=80, blank=True, db_index=True)
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    route = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read_at', '-created_at']),
        ]

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_read(self):
        if self.read_at:
            return False
        self.read_at = timezone.now()
        self.save(update_fields=['read_at'])
        return True

    def __str__(self):
        return f'{self.user_id} {self.title}'
