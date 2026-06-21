from django.contrib import admin

from .models import (
    ColorRecommendation,
    DiagnosisColorPalette,
    DiagnosisMakeoverStyle,
    DiagnosisRecommendedLens,
    DiagnosisRecommendedProduct,
    DiagnosisRepresentativeColor,
    DiagnosisResult,
    PersonalColor,
)


@admin.register(PersonalColor)
class PersonalColorAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'season', 'base_temperature', 'tone')
    search_fields = ('type_name',)
    list_filter = ('season', 'base_temperature', 'tone')


@admin.register(ColorRecommendation)
class ColorRecommendationAdmin(admin.ModelAdmin):
    list_display = ('personal_color', 'recommendation_type', 'makeup_part', 'color_name', 'color_hex')
    list_filter = ('recommendation_type', 'makeup_part')
    search_fields = ('color_name', 'personal_color__type_name')


class DiagnosisRepresentativeColorInline(admin.TabularInline):
    model = DiagnosisRepresentativeColor
    extra = 0


class DiagnosisColorPaletteInline(admin.TabularInline):
    model = DiagnosisColorPalette
    extra = 0


class DiagnosisMakeoverStyleInline(admin.TabularInline):
    model = DiagnosisMakeoverStyle
    extra = 0


class DiagnosisRecommendedProductInline(admin.TabularInline):
    model = DiagnosisRecommendedProduct
    extra = 0


class DiagnosisRecommendedLensInline(admin.TabularInline):
    model = DiagnosisRecommendedLens
    extra = 0


@admin.register(DiagnosisResult)
class DiagnosisResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'personal_color',
        'confidence_score',
        'diagnosed_at',
        'is_demo',
        'makeover_style_count',
        'recommended_product_count',
    )
    list_filter = ('is_demo', 'personal_color__season', 'personal_color__base_temperature', 'personal_color__tone')
    search_fields = ('user__username', 'user__nickname', 'korean_name', 'english_name')
    inlines = [
        DiagnosisRepresentativeColorInline,
        DiagnosisColorPaletteInline,
        DiagnosisMakeoverStyleInline,
        DiagnosisRecommendedProductInline,
        DiagnosisRecommendedLensInline,
    ]

    def makeover_style_count(self, obj):
        return obj.makeover_styles.count()

    def recommended_product_count(self, obj):
        return obj.recommended_products.count()


admin.site.register(DiagnosisRepresentativeColor)
admin.site.register(DiagnosisColorPalette)
admin.site.register(DiagnosisMakeoverStyle)
admin.site.register(DiagnosisRecommendedProduct)
admin.site.register(DiagnosisRecommendedLens)
