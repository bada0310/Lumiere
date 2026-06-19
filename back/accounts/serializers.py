from rest_framework import serializers
from django.contrib.auth import get_user_model
import random 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        # 1. 수정: 프론트엔드에서 보내는 아이디는 'username'으로 받습니다.
        fields = ['username', 'password', 'email'] 
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # 임의의 닉네임 생성
        random_nickname = f"루미에르_{random.randint(1000, 9999)}"
        
        # 유저 생성
        user = get_user_model().objects.create_user(
            username=validated_data['username'], # 2. 수정:  username(장고)
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            nickname=random_nickname # 3. 수정: userName이 아니라 nickname
        )
        return user