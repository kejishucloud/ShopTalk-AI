from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'company', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone', 'company')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('phone', 'avatar', 'user_type', 'company', 'department')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {
            'fields': ('phone', 'user_type', 'company', 'department')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'timezone', 'language', 'auto_reply_enabled', 'max_concurrent_conversations')
    list_filter = ('timezone', 'language', 'auto_reply_enabled')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('基本设置', {
            'fields': ('user', 'timezone', 'language')
        }),
        ('通知设置', {
            'fields': ('notification_email', 'notification_sms')
        }),
        ('客服设置', {
            'fields': ('auto_reply_enabled', 'max_concurrent_conversations')
        }),
    ) 