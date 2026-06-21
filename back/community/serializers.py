from rest_framework import serializers

from products.models import Product
from products.serializers import ProductSerializer

from .models import Comment, CommentLike, Post, PostLike


class CommentSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_nickname = serializers.CharField(source='author.nickname', read_only=True)
    author_profile_image_url = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'post',
            'author_id',
            'author_username',
            'author_nickname',
            'author_profile_image_url',
            'parent',
            'content',
            'like_count',
            'is_liked',
            'replies',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'author_id',
            'author_username',
            'author_nickname',
            'author_profile_image_url',
            'like_count',
            'is_liked',
            'replies',
            'created_at',
            'updated_at',
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_author_profile_image_url(self, obj):
        if not obj.author.profile_image:
            return None
        request = self.context.get('request')
        url = obj.author.profile_image.url
        return request.build_absolute_uri(url) if request else url

    def get_like_count(self, obj):
        annotated_count = getattr(obj, 'like_count', None)
        if annotated_count is not None:
            return annotated_count
        return obj.likes.count()

    def get_replies(self, obj):
        if obj.parent_id:
            return []

        replies = obj.replies.select_related('author').prefetch_related('likes').all()
        return CommentSerializer(
            replies,
            many=True,
            context=self.context,
        ).data

    def validate(self, attrs):
        parent = attrs.get('parent')
        post = attrs.get('post') or getattr(self.instance, 'post', None)
        if parent:
            if parent.parent_id:
                raise serializers.ValidationError({'parent': 'Replies can only be added to top-level comments.'})
            if post and parent.post_id != post.id:
                raise serializers.ValidationError({'parent': 'Parent comment must belong to the same post.'})
        return attrs

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_nickname = serializers.CharField(source='author.nickname', read_only=True)
    author_profile_image_url = serializers.SerializerMethodField()
    product_ids = serializers.PrimaryKeyRelatedField(
        source='products',
        queryset=Product.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    products = ProductSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'author_id',
            'author_username',
            'author_nickname',
            'author_profile_image_url',
            'title',
            'content',
            'category',
            'product_ids',
            'products',
            'image_url',
            'view_count',
            'comment_count',
            'like_count',
            'is_liked',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'author_id',
            'author_username',
            'author_nickname',
            'author_profile_image_url',
            'view_count',
            'comment_count',
            'like_count',
            'is_liked',
            'created_at',
            'updated_at',
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_author_profile_image_url(self, obj):
        if not obj.author.profile_image:
            return None
        request = self.context.get('request')
        url = obj.author.profile_image.url
        return request.build_absolute_uri(url) if request else url

    def create(self, validated_data):
        products = validated_data.pop('products', [])
        validated_data['author'] = self.context['request'].user
        post = super().create(validated_data)
        post.products.set(products)
        return post

    def update(self, instance, validated_data):
        products = validated_data.pop('products', None)
        post = super().update(instance, validated_data)
        if products is not None:
            post.products.set(products)
        return post


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ['id', 'post', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']


class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']
