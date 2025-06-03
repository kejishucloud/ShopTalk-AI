"""
AI模型管理Django管理后台配置
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AIModelProvider, AIModel, ModelCallRecord, ModelPerformance,
    ModelLoadBalancer, ModelWeight, ModelQuota
)


@admin.register(AIModelProvider)
class AIModelProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'created_at']
    list_filter = ['provider_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


class ModelWeightInline(admin.TabularInline):
    model = ModelWeight
    extra = 1
    fields = ['model', 'weight', 'is_healthy', 'last_health_check']
    readonly_fields = ['last_health_check']


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider', 'model_type', 'is_active', 
        'priority', 'input_price_display', 'output_price_display', 'created_at'
    ]
    list_filter = [
        'provider', 'model_type', 'is_active', 
        'priority', 'created_at'
    ]
    search_fields = ['name', 'model_id', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('provider', 'name', 'model_id', 'model_type', 'capabilities', 'is_active', 'priority')
        }),
        ('模型参数', {
            'fields': ('max_tokens', 'context_window', 'default_temperature', 'default_top_p')
        }),
        ('定价信息', {
            'fields': ('input_price_per_1k', 'output_price_per_1k')
        }),
        ('限制配置', {
            'fields': ('rate_limit_rpm', 'rate_limit_tpm', 'daily_quota')
        }),
        ('认证配置', {
            'fields': ('api_key', 'additional_config'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def input_price_display(self, obj):
        return f"${obj.input_price_per_1k:.6f}/1K"
    input_price_display.short_description = '输入价格'
    
    def output_price_display(self, obj):
        return f"${obj.output_price_per_1k:.6f}/1K"
    output_price_display.short_description = '输出价格'


@admin.register(ModelCallRecord)
class ModelCallRecordAdmin(admin.ModelAdmin):
    list_display = [
        'model', 'user', 'status', 'total_tokens', 
        'cost_display', 'response_time', 'created_at'
    ]
    list_filter = ['status', 'model', 'created_at']
    search_fields = ['session_id', 'request_id', 'user__username']
    readonly_fields = [
        'model', 'session_id', 'user', 'input_text', 'parameters',
        'output_text', 'status', 'error_message', 'input_tokens',
        'output_tokens', 'total_tokens', 'response_time', 'cost',
        'request_id', 'ip_address', 'user_agent', 'created_at'
    ]
    
    def cost_display(self, obj):
        return f"${obj.cost:.6f}"
    cost_display.short_description = '成本'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ModelPerformance)
class ModelPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'model', 'date', 'total_calls', 'success_rate_display',
        'avg_response_time_display', 'total_cost_display'
    ]
    list_filter = ['model', 'date']
    readonly_fields = [
        'model', 'date', 'total_calls', 'successful_calls', 'failed_calls',
        'total_input_tokens', 'total_output_tokens', 'total_tokens',
        'average_response_time', 'success_rate', 'total_cost',
        'average_cost_per_call', 'updated_at'
    ]
    
    def success_rate_display(self, obj):
        color = 'green' if obj.success_rate >= 95 else 'orange' if obj.success_rate >= 80 else 'red'
        return format_html(
            '<span style="color: {};">{:.2f}%</span>',
            color, obj.success_rate
        )
    success_rate_display.short_description = '成功率'
    
    def avg_response_time_display(self, obj):
        return f"{obj.average_response_time:.3f}s"
    avg_response_time_display.short_description = '平均响应时间'
    
    def total_cost_display(self, obj):
        return f"${obj.total_cost:.6f}"
    total_cost_display.short_description = '总成本'
    
    def has_add_permission(self, request):
        return False


@admin.register(ModelLoadBalancer)
class ModelLoadBalancerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'strategy', 'is_active', 'enable_fallback',
        'health_check_enabled', 'created_at'
    ]
    list_filter = ['strategy', 'is_active', 'enable_fallback', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ModelWeightInline]
    
    fieldsets = (
        ('基本配置', {
            'fields': ('name', 'strategy', 'is_active')
        }),
        ('故障转移', {
            'fields': ('enable_fallback', 'max_retries', 'retry_delay')
        }),
        ('健康检查', {
            'fields': ('health_check_enabled', 'health_check_interval')
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ModelWeight)
class ModelWeightAdmin(admin.ModelAdmin):
    list_display = [
        'load_balancer', 'model', 'weight', 
        'is_healthy', 'last_health_check'
    ]
    list_filter = ['is_healthy', 'load_balancer']
    readonly_fields = ['last_health_check']


@admin.register(ModelQuota)
class ModelQuotaAdmin(admin.ModelAdmin):
    list_display = [
        'model', 'user', 'quota_type', 'usage_display',
        'is_exceeded_display', 'is_active'
    ]
    list_filter = ['quota_type', 'is_active', 'model']
    search_fields = ['user__username', 'model__name']
    readonly_fields = ['used_calls', 'used_tokens', 'used_cost', 'last_reset', 'created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('model', 'user', 'quota_type', 'is_active')
        }),
        ('配额限制', {
            'fields': ('max_calls', 'max_tokens', 'max_cost')
        }),
        ('使用情况', {
            'fields': ('used_calls', 'used_tokens', 'used_cost'),
            'classes': ('collapse',)
        }),
        ('时间设置', {
            'fields': ('reset_at', 'last_reset', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def usage_display(self, obj):
        percentages = obj.get_usage_percentage()
        max_percentage = max(percentages.values())
        color = 'red' if max_percentage >= 90 else 'orange' if max_percentage >= 70 else 'green'
        
        return format_html(
            '<span style="color: {};">调用: {:.1f}% | Token: {:.1f}% | 成本: {:.1f}%</span>',
            color, percentages['calls'], percentages['tokens'], percentages['cost']
        )
    usage_display.short_description = '使用率'
    
    def is_exceeded_display(self, obj):
        is_exceeded = obj.is_exceeded()
        color = 'red' if is_exceeded else 'green'
        text = '已超限' if is_exceeded else '正常'
        return format_html('<span style="color: {};">{}</span>', color, text)
    is_exceeded_display.short_description = '状态'


# 自定义管理后台标题
admin.site.site_header = 'ShopTalk-AI 模型管理'
admin.site.site_title = 'AI模型管理'
admin.site.index_title = 'AI模型管理控制台' 