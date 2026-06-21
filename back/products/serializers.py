from rest_framework import serializers

from .models import Product, Review


class ProductSerializer(serializers.ModelSerializer):
    review_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    image = serializers.CharField(source='image_url', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'brand',
            'name',
            'category',
            'image',
            'image_url',
            'product_url',
            'description',

            # 네이버 쇼핑 API 원본 정보
            'price',
            'mall_name',
            'naver_product_id',
            'source_query',
            'naver_category1',
            'naver_category2',
            'naver_category3',
            'naver_category4',

            # 추천/필터용 정보
            'texture',
            'finish',
            'tone_tag',
            'color_family',

            # 색상 분석 정보
            'hex_code',
            'rgb_r',
            'rgb_g',
            'rgb_b',
            'brightness',
            'saturation',
            'coolness',
            'warmth',
            'depth',
            'softness',
            'contrast',

            # 추천 결과
            'match_score',
            'reason',

            # 리뷰/시간 정보
            'review_count',
            'average_rating',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'created_at',
            'updated_at',
        ]


class ReviewSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_nickname = serializers.CharField(source='author.nickname', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'product',
            'author_id',
            'author_username',
            'author_nickname',
            'rating',
            'content',
            'image_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'author_id',
            'author_username',
            'author_nickname',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)