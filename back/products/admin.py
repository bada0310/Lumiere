from django.contrib import admin

from .models import Product, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'name', 'category', 'match_score', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('brand', 'name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'author', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__brand', 'product__name', 'author__username')
