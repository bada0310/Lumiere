from django.conf import settings
from rest_framework import serializers

from .models import (
    Product,
    ProductImageAnalysis,
    ProductImageAnalysisOption,
    ProductOffer,
    ProductOption,
    ProductOptionToneScore,
    Review,
)
from .services.recommendation import calculate_option_match


def prefetched_options(product):
    return list(getattr(product, '_prefetched_objects_cache', {}).get('options', []) or product.options.all())


def option_offers(option):
    return list(getattr(option, '_prefetched_objects_cache', {}).get('offers', []) or option.offers.all())

def absolute_media_url(request, file_field):
    if not file_field:
        return ''

    try:
        url = file_field.url
    except ValueError:
        return ''

    if url.startswith('http://') or url.startswith('https://'):
        return url

    if request:
        return request.build_absolute_uri(url)

    base_url = (
        getattr(settings, 'BACKEND_ORIGIN', '')
        or getattr(settings, 'SITE_URL', '')
        or 'http://127.0.0.1:8000'
    )

    return f'{base_url.rstrip("/")}{url}'

class ProductOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOffer
        fields = [
            'id',
            'mall_name',
            'price',
            'product_url',
            'naver_product_id',
            'is_representative',
            'created_at',
        ]


class ProductOptionToneScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOptionToneScore
        fields = [
            'id',
            'target_tone',
            'match_score',
            'grade',
            'reason',
            'created_at',
            'updated_at',
        ]


class ProductOptionSerializer(serializers.ModelSerializer):
    match_score = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()
    offers = ProductOfferSerializer(many=True, read_only=True)
    tone_scores = ProductOptionToneScoreSerializer(many=True, read_only=True)
    representative_offer = serializers.SerializerMethodField()

    class Meta:
        model = ProductOption
        fields = [
            'id',
            'option_no',
            'option_name',
            'option_key',
            'image_url',
            'color_family',
            'analyzed_tone_tag',
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
            'match_score',
            'grade',
            'reason',
            'representative_offer',
            'offers',
            'tone_scores',
        ]

    def get_match_score(self, obj):
        return self._match(obj)['match_score']

    def get_grade(self, obj):
        return self._match(obj)['grade']

    def get_reason(self, obj):
        return self._match(obj)['reason']

    def get_representative_offer(self, obj):
        offers = option_offers(obj)
        representative = next((offer for offer in offers if offer.is_representative), None)
        if representative is None and offers:
            representative = sorted(offers, key=lambda offer: (offer.price or 10**12, offer.id))[0]
        return ProductOfferSerializer(representative).data if representative else None

    def _match(self, obj):
        cache = self.context.setdefault('option_match_cache', {})
        if obj.id not in cache:
            cache[obj.id] = calculate_option_match(
                obj,
                self.context.get('user_tone_profile') or {},
                getattr(obj.product, 'category', None),
            )
        return cache[obj.id]


class ProductSerializer(serializers.ModelSerializer):
    review_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    image = serializers.CharField(source='display_image_url', read_only=True)
    options = serializers.SerializerMethodField()
    best_option = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'brand',
            'name',
            'canonical_key',
            'category',
            'image',
            'image_url',
            'representative_image_url',
            'product_url',
            'description',
            'price',
            'mall_name',
            'naver_product_id',
            'source_query',
            'naver_category1',
            'naver_category2',
            'naver_category3',
            'naver_category4',
            'texture',
            'finish',
            'tone_tag',
            'color_family',
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
            'match_score',
            'reason',
            'min_price',
            'max_price',
            'best_option',
            'options',
            'review_count',
            'average_rating',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_options(self, obj):
        return ProductOptionSerializer(prefetched_options(obj), many=True, context=self.context).data

    def get_best_option(self, obj):
        options = prefetched_options(obj)
        if not options:
            return {
                'id': obj.id,
                'option_no': '',
                'option_name': obj.texture or obj.name,
                'option_key': obj.naver_product_id or obj.product_url or str(obj.id),
                'image_url': obj.display_image_url,
                'color_family': obj.color_family,
                'analyzed_tone_tag': obj.tone_tag,
                'hex_code': obj.hex_code,
                'rgb_r': obj.rgb_r,
                'rgb_g': obj.rgb_g,
                'rgb_b': obj.rgb_b,
                'brightness': obj.brightness,
                'saturation': obj.saturation,
                'coolness': obj.coolness,
                'warmth': obj.warmth,
                'depth': obj.depth,
                'softness': obj.softness,
                'contrast': obj.contrast,
                'match_score': obj.match_score,
                'grade': '',
                'reason': obj.reason,
                'representative_offer': {
                    'id': obj.id,
                    'mall_name': obj.mall_name,
                    'price': obj.price,
                    'product_url': obj.product_url,
                    'naver_product_id': obj.naver_product_id,
                    'is_representative': True,
                    'created_at': obj.created_at,
                } if obj.product_url or obj.price else None,
                'offers': [],
                'tone_scores': [],
            }
        option_serializer = ProductOptionSerializer(context=self.context)
        best = max(options, key=lambda option: option_serializer.get_match_score(option))
        return ProductOptionSerializer(best, context=self.context).data

    def get_min_price(self, obj):
        prices = self._prices(obj)
        return min(prices) if prices else obj.price or 0

    def get_max_price(self, obj):
        prices = self._prices(obj)
        return max(prices) if prices else obj.price or 0

    def _prices(self, obj):
        return [
            offer.price
            for option in prefetched_options(obj)
            for offer in option_offers(option)
            if offer.price
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


class ProductImageAnalysisRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    product_name = serializers.CharField(max_length=300, required=False, allow_blank=True)
    brand_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=Product.Category.choices,
        required=False,
        allow_blank=True,
    )


class ProductImageAnalysisReviewOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    option_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    hex_code = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    chart_x = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    chart_y = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    confidence = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=1)
    removed = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if attrs.get('removed'):
            return attrs
        if not (attrs.get('option_name') or attrs.get('display_name')):
            raise serializers.ValidationError('option_name or display_name is required.')
        return attrs


class ProductImageAnalysisUpdateSerializer(serializers.Serializer):
    product_name = serializers.CharField(max_length=300, required=False, allow_blank=True)
    brand_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=Product.Category.choices,
        required=False,
        allow_blank=True,
    )
    options = ProductImageAnalysisReviewOptionSerializer(many=True, required=False)


class ProductImageAnalysisSummarySerializer(serializers.ModelSerializer):
    uploaded_image_url = serializers.SerializerMethodField()
    colors = serializers.SerializerMethodField()
    confirmed = serializers.SerializerMethodField()

    class Meta:
        model = ProductImageAnalysis
        fields = [
            'id',
            'product_name',
            'brand_name',
            'category',
            'uploaded_image_url',
            'colors',
            'confirmed',
            'created_at',
            'updated_at',
        ]

    def get_uploaded_image_url(self, obj):
        request = self.context.get('request')
        return absolute_media_url(request, obj.uploaded_image)

    def get_colors(self, obj):
        return [
            option.hex_code
            for option in obj.options.all()
            if option.hex_code
        ][:5]

    def get_confirmed(self, obj):
        return obj.status == ProductImageAnalysis.Status.CONFIRMED

