from django.contrib import admin

from .models import LikedProductOption, Notification, UrlAnalysisRecord


@admin.register(LikedProductOption)
class LikedProductOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'option_id', 'created_at')
    search_fields = ('user__username', 'brand', 'name', 'option')


@admin.register(UrlAnalysisRecord)
class UrlAnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'source_url', 'created_at')
    search_fields = ('user__username', 'title', 'source_url', 'brand', 'product_name')
    readonly_fields = (
        'user',
        'source_url',
        'title',
        'brand',
        'product_name',
        'image_url',
        'colors',
        'result_payload',
        'created_at',
        'updated_at',
    )

    # Legacy archive only; no active API or writes.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'title', 'read_at', 'created_at')
    list_filter = ('notification_type', 'read_at', 'created_at')
    search_fields = ('user__username', 'title', 'body')
    readonly_fields = ('created_at',)
