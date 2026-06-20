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
            'match_score',
            'review_count',
            'average_rating',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


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
