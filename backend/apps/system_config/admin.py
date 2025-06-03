from django.contrib import admin
from .models import ConfigCategory, SystemConfig, ConfigGroup


@admin.register(ConfigCategory)
class ConfigCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['order', 'name']


@admin.register(ConfigGroup)
class ConfigGroupAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'category', 'name', 'order', 'is_collapsible', 'is_expanded']
    list_filter = ['category', 'is_collapsible', 'is_expanded']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['category__order', 'order', 'name']


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'key', 'category', 'group', 'config_type', 'is_required', 'is_active']
    list_filter = ['category', 'config_type', 'is_required', 'is_encrypted', 'is_active', 'created_at']
    search_fields = ['key', 'display_name', 'description']
    ordering = ['category__order', 'order', 'key']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('category', 'group', 'key', 'display_name', 'description')
        }),
        ('配置值', {
            'fields': ('config_type', 'value', 'default_value', 'choices')
        }),
        ('属性设置', {
            'fields': ('is_required', 'is_encrypted', 'order', 'is_active')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑现有对象
            return ['key']
        return [] 