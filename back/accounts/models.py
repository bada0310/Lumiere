from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    # 1. 기본 유저 정보 (ERD 및 소셜 로그인 기반)
    nickname = models.CharField(max_length=50, unique=True, null=True)
    social_id = models.CharField(max_length=100, null=True, blank=True)
    social_provider = models.CharField(max_length=20, null=True, blank=True)
    # 2. 프로필 및 서비스 기능
    
    # (선택) 서비스 내부에서 사용할 세부 권한 등급
    ROLE_CHOICES = (
        ('USER', '일반 유저'),
        ('MANAGER', '매니저'),
        ('ADMIN', '관리자'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    
    # 프로필 이미지 (직접 서버에 올릴 경우 ImageField, 외부 S3 등 링크면 URLField 사용)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)


    # 3. 계정 상태 관리 (논리적 삭제 - Soft Delete)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # 유저 삭제 시 DB에서 완전히 날리지 않고 상태만 변경하는 오버라이딩 기법
    def delete(self, *args, **kwargs):
        self.is_active = False            
        self.deleted_at = timezone.now()  # 삭제 시간 기록
        self.save()                       # DB에 변경 상태 저장        