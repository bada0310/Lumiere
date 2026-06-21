import random

from django.contrib.auth import get_user_model
from rest_framework import serializers


class CurrentUserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(write_only=True, required=False, allow_empty_file=False)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'nickname', 'email', 'profile_image', 'profile_image_url']
        read_only_fields = ['id', 'username', 'profile_image_url']

    def validate_profile_image(self, value):
        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
        max_size = 5 * 1024 * 1024
        content_type = getattr(value, 'content_type', None)

        if content_type and content_type not in allowed_types:
            raise serializers.ValidationError('JPG, PNG, WEBP 이미지만 업로드할 수 있습니다.')
        if value.size > max_size:
            raise serializers.ValidationError('프로필 이미지는 5MB 이하로 업로드해주세요.')
        return value

    def get_profile_image_url(self, obj):
        if not obj.profile_image:
            return None

        request = self.context.get('request')
        url = obj.profile_image.url
        return request.build_absolute_uri(url) if request else url

    def update(self, instance, validated_data):
        profile_image = validated_data.pop('profile_image', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if profile_image:
            instance.profile_image = profile_image

        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            nickname=f'루미에르_{random.randint(1000, 9999)}',
        )
