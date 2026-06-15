from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display   = ('user', 'title', 'type', 'is_read', 'created_at')
    list_filter    = ('type', 'is_read')
    search_fields  = ('user__full_name', 'user__email', 'title', 'message')
    ordering       = ('-created_at',)
    readonly_fields = ('created_at',)
    raw_id_fields  = ('user',)
    actions        = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='Mark selected as read')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected as unread')
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)