from django.contrib import admin

from .models import LikedProductOption, UrlAnalysisRecord


@admin.register(LikedProductOption)
class LikedProductOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'option_id', 'created_at')
    search_fields = ('user__username', 'brand', 'name', 'option')


@admin.register(UrlAnalysisRecord)
class UrlAnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'source_url', 'created_at')
    search_fields = ('user__username', 'title', 'source_url', 'brand', 'product_name')
