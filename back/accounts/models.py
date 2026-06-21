import uuid
from pathlib import Path

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def user_profile_image_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f'profiles/uploads/user-{instance.pk or "new"}-{uuid.uuid4().hex}{suffix}'


class User(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True, null=True)
    social_id = models.CharField(max_length=100, null=True, blank=True)
    social_provider = models.CharField(max_length=20, null=True, blank=True)

    ROLE_CHOICES = (
        ('USER', '일반 사용자'),
        ('MANAGER', '매니저'),
        ('ADMIN', '관리자'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')

    # User avatar only. Diagnosis/Gen AI images must never be stored here.
    profile_image = models.ImageField(
        upload_to=user_profile_image_upload_to,
        null=True,
        blank=True,
    )

    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()
