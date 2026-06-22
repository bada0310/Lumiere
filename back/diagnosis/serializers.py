from django.conf import settings
from rest_framework import serializers

from diagnosis.services.palettes import build_makeup_color_guide

from .models import (
    DiagnosisColorPalette,
    DiagnosisMakeoverStyle,
    DiagnosisRecommendedLens,
    DiagnosisRecommendedProduct,
    DiagnosisRepresentativeColor,
    DiagnosisResult,
    PersonalColor,
)


def build_absolute_url(request, url):
    if not url:
        return None
    return request.build_absolute_uri(url) if request else url


def build_media_url(request, path):
    if not path:
        return None
    if path.startswith('http://') or path.startswith('https://') or path.startswith('/'):
        return build_absolute_url(request, path)
    return build_absolute_url(request, f'{settings.MEDIA_URL}{path}')


class PersonalColorSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    temperature = serializers.CharField(source='base_temperature')
    korean_name = serializers.CharField(source='type_name')
    english_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonalColor
        fields = [
            'id',
            'code',
            'type_name',
            'tone_key',
            'korean_name',
            'english_name',
            'season',
            'temperature',
            'base_temperature',
            'tone',
            'description',
            'temperature_degree',
            'brightness_degree',
            'saturation_degree',
            'turbidity_degree',
            'glossiness_degree',
            'contrast_degree',
            'best_pccs',
            'sub_pccs',
        ]

    def get_code(self, obj):
        if obj.tone_key:
            return obj.tone_key
        tone = (obj.tone or '').lower()
        tone_map = {'bright': 'bright', 'light': 'light', 'mute': 'mute', 'deep': 'deep'}
        season = 'autumn' if obj.season == 'fall' else obj.season
        return f'{season}_{obj.base_temperature}_{tone_map.get(tone, tone)}'

    def get_english_name(self, obj):
        season = 'Autumn' if obj.season == 'fall' else (obj.season or '').title()
        temperature = (obj.base_temperature or '').title()
        tone = (obj.tone or '').title().replace('Mute', 'Muted')
        return f'{season} {temperature} {tone}'.strip()


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_image_url = serializers.SerializerMethodField()

    def get_profile_image_url(self, obj):
        profile_image = getattr(obj, 'profile_image', None)
        if not profile_image:
            return None
        return build_absolute_url(self.context.get('request'), profile_image.url)


class DiagnosisRepresentativeColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosisRepresentativeColor
        fields = ['name', 'hex', 'order']


class DiagnosisColorPaletteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosisColorPalette
        fields = ['group', 'name', 'hex', 'order']


class DiagnosisMakeoverStyleSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosisMakeoverStyle
        fields = ['key', 'name', 'description', 'image', 'image_url', 'order', 'is_default']

    def get_image_url(self, obj):
        return build_media_url(self.context.get('request'), obj.image)


class DiagnosisRecommendedProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosisRecommendedProduct
        fields = [
            'category',
            'category_name',
            'tone_label',
            'brand',
            'product_name',
            'shade',
            'description',
            'image',
            'image_url',
            'product_url',
            'order',
        ]

    def get_image_url(self, obj):
        return build_media_url(self.context.get('request'), obj.image)


class DiagnosisRecommendedLensSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosisRecommendedLens
        fields = ['rank', 'brand', 'product_name', 'color', 'description', 'image', 'image_url', 'order']

    def get_image_url(self, obj):
        return build_media_url(self.context.get('request'), obj.image)


class DiagnosisResultSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    personal_color = PersonalColorSerializer(read_only=True)
    personal_color_id = serializers.PrimaryKeyRelatedField(
        source='personal_color',
        queryset=PersonalColor.objects.all(),
        write_only=True,
    )
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    confidence = serializers.IntegerField(source='confidence_score', read_only=True)
    diagnosed_at = serializers.SerializerMethodField()
    uploaded_image_url = serializers.SerializerMethodField()
    processed_image_url = serializers.SerializerMethodField()
    generated_makeup_image_url = serializers.SerializerMethodField()
    representative_colors = DiagnosisRepresentativeColorSerializer(many=True, read_only=True)
    makeover_styles = DiagnosisMakeoverStyleSerializer(many=True, read_only=True)
    recommended_products = DiagnosisRecommendedProductSerializer(many=True, read_only=True)
    recommended_lenses = DiagnosisRecommendedLensSerializer(many=True, read_only=True)
    color_palettes = serializers.SerializerMethodField()
    palette = serializers.SerializerMethodField()
    makeup_color_guide = serializers.SerializerMethodField()
    analysis = serializers.SerializerMethodField()
    evidence = serializers.SerializerMethodField()
    cautions = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosisResult
        fields = [
            'id',
            'user',
            'user_id',
            'status',
            'personal_color',
            'personal_color_id',
            'tone_key',
            'personal_color_code',
            'korean_name',
            'english_name',
            'confidence',
            'confidence_score',
            'diagnosed_at',
            'summary',
            'diagnosis_json',
            'analysis',
            'evidence',
            'cautions',
            'palette',
            'palette_snapshot',
            'palette_status',
            'keywords',
            'image_features',
            'skin_metrics',
            'radar_chart',
            'representative_colors',
            'makeover_styles',
            'color_palettes',
            'recommended_products',
            'recommended_lenses',
            'style_guide',
            'uploaded_image',
            'uploaded_image_url',
            'processed_image',
            'processed_image_url',
            'generated_makeup_image',
            'generated_makeup_image_url',
            'makeup_generation_status',
            'makeup_generation_error',
            'makeup_color_guide',
            'is_demo',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_id',
            'personal_color',
            'uploaded_image_url',
            'processed_image_url',
            'generated_makeup_image_url',
            'created_at',
        ]

    def _absolute_image_url(self, image_field):
        if not image_field:
            return None
        return build_absolute_url(self.context.get('request'), image_field.url)

    def get_diagnosed_at(self, obj):
        value = obj.diagnosed_at or obj.created_at.date()
        return value.isoformat()

    def get_uploaded_image_url(self, obj):
        return self._absolute_image_url(obj.uploaded_image)

    def get_processed_image_url(self, obj):
        return self._absolute_image_url(obj.processed_image)

    def get_generated_makeup_image_url(self, obj):
        return self._absolute_image_url(obj.generated_makeup_image)

    def get_color_palettes(self, obj):
        grouped = {'best': [], 'neutral': [], 'accent': [], 'try': [], 'worst': []}
        serializer_context = {'request': self.context.get('request')}
        for item in obj.color_palettes.all():
            grouped[item.group].append(DiagnosisColorPaletteSerializer(item, context=serializer_context).data)
        return grouped

    def get_palette(self, obj):
        return obj.palette_snapshot or None

    def get_makeup_color_guide(self, obj):
        if not obj.palette_snapshot:
            return None
        return build_makeup_color_guide(obj.palette_snapshot)

    def get_analysis(self, obj):
        return (obj.diagnosis_json or {}).get('analysis')

    def get_evidence(self, obj):
        return (obj.diagnosis_json or {}).get('evidence')

    def get_cautions(self, obj):
        return (obj.diagnosis_json or {}).get('cautions', [])
