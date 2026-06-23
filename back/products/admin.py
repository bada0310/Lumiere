from django.contrib import admin

from .models import Product, ProductOffer, ProductOption, ProductOptionToneScore, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'name', 'category', 'canonical_key', 'match_score', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('brand', 'name', 'canonical_key')


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'option_no', 'option_name', 'hex_code', 'analyzed_tone_tag')
    list_filter = ('product__category', 'analyzed_tone_tag', 'color_family')
    search_fields = ('product__brand', 'product__name', 'option_no', 'option_name', 'option_key')


@admin.register(ProductOffer)
class ProductOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'option', 'mall_name', 'price', 'is_representative', 'created_at')
    list_filter = ('mall_name', 'is_representative')
    search_fields = ('option__product__brand', 'option__product__name', 'option__option_name', 'naver_product_id')


@admin.register(ProductOptionToneScore)
class ProductOptionToneScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'option', 'target_tone', 'match_score', 'grade')
    list_filter = ('target_tone', 'grade')
    search_fields = ('option__product__brand', 'option__product__name', 'option__option_name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'author', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__brand', 'product__name', 'author__username')
