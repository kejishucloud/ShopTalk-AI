"""
知识库管理Django管理后台
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    KnowledgeBase, DocumentCategory, DocumentTag, Document, FAQ, Product,
    Script, KnowledgeVector, KnowledgeAccessRecord, KnowledgeRecommendation
)


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    """知识库管理"""
    list_display = [
        'name', 'knowledge_type', 'access_level', 'total_documents', 
        'total_qa_pairs', 'total_views', 'is_active', 'created_at'
    ]
    list_filter = ['knowledge_type', 'access_level', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['total_documents', 'total_qa_pairs', 'total_views', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'knowledge_type', 'description', 'access_level', 'is_active')
        }),
        ('功能设置', {
            'fields': ('enable_version_control', 'enable_ai_enhancement', 'auto_extract_keywords')
        }),
        ('配置信息', {
            'fields': ('embedding_model', 'search_config', 'permissions'),
            'classes': ('collapse',)
        }),
        ('统计信息', {
            'fields': ('total_documents', 'total_qa_pairs', 'total_views'),
            'classes': ('collapse',)
        }),
        ('创建信息', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """文档分类管理"""
    list_display = ['name', 'knowledge_base', 'parent', 'sort_order', 'is_active', 'created_at']
    list_filter = ['knowledge_base', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['sort_order']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'name', 'parent', 'description')
        }),
        ('显示设置', {
            'fields': ('color', 'sort_order', 'is_active')
        }),
    )


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    """文档标签管理"""
    list_display = ['name', 'knowledge_base', 'color_display', 'usage_count', 'created_at']
    list_filter = ['knowledge_base', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.name
        )
    color_display.short_description = '颜色预览'


class DocumentTagInline(admin.TabularInline):
    """文档标签内联"""
    model = Document.tags.through
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """文档管理"""
    list_display = [
        'title', 'knowledge_base', 'category', 'document_type', 'process_status',
        'view_count', 'rating', 'is_active', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'document_type', 'process_status', 'is_active', 'is_featured', 'created_at'
    ]
    search_fields = ['title', 'content', 'summary']
    readonly_fields = [
        'file_size', 'file_hash', 'extracted_text', 'view_count', 'download_count',
        'rating', 'rating_count', 'created_at', 'updated_at'
    ]
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'category', 'title', 'slug', 'document_type')
        }),
        ('内容', {
            'fields': ('file_path', 'content', 'summary')
        }),
        ('元数据', {
            'fields': ('language', 'keywords', 'metadata'),
            'classes': ('collapse',)
        }),
        ('处理状态', {
            'fields': ('process_status', 'process_message', 'extracted_text'),
            'classes': ('collapse',)
        }),
        ('文件信息', {
            'fields': ('file_size', 'file_hash'),
            'classes': ('collapse',)
        }),
        ('统计信息', {
            'fields': ('view_count', 'download_count', 'rating', 'rating_count'),
            'classes': ('collapse',)
        }),
        ('状态控制', {
            'fields': ('is_active', 'is_featured', 'is_public')
        }),
        ('版本信息', {
            'fields': ('version', 'parent_document'),
            'classes': ('collapse',)
        }),
        ('创建信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """FAQ管理"""
    list_display = [
        'question_short', 'knowledge_base', 'faq_category', 'priority', 'status',
        'view_count', 'helpful_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'status', 'is_active', 'is_featured', 'auto_generated', 'created_at'
    ]
    search_fields = ['question', 'answer']
    readonly_fields = ['view_count', 'helpful_count', 'unhelpful_count', 'created_at', 'updated_at']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'category', 'question', 'answer', 'answer_html')
        }),
        ('分类和标识', {
            'fields': ('faq_category', 'keywords', 'related_questions')
        }),
        ('优先级和状态', {
            'fields': ('priority', 'status', 'is_active', 'is_featured')
        }),
        ('统计信息', {
            'fields': ('view_count', 'helpful_count', 'unhelpful_count'),
            'classes': ('collapse',)
        }),
        ('AI增强', {
            'fields': ('auto_generated', 'confidence_score', 'source_documents'),
            'classes': ('collapse',)
        }),
        ('创建信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_short(self, obj):
        return obj.question[:100] + '...' if len(obj.question) > 100 else obj.question
    question_short.short_description = '问题'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """商品管理"""
    list_display = [
        'sku', 'name', 'brand', 'price', 'stock_quantity', 'status',
        'sales_count', 'view_count', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'status', 'brand', 'product_category', 'created_at'
    ]
    search_fields = ['sku', 'name', 'description', 'brand']
    readonly_fields = ['sales_count', 'view_count', 'created_at', 'updated_at']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'category', 'sku', 'name', 'product_category', 'brand')
        }),
        ('价格信息', {
            'fields': ('price', 'original_price', 'cost_price')
        }),
        ('库存信息', {
            'fields': ('stock_quantity', 'min_stock_level', 'max_stock_level')
        }),
        ('描述', {
            'fields': ('description', 'short_description')
        }),
        ('规格和属性', {
            'fields': ('specifications', 'attributes', 'variants'),
            'classes': ('collapse',)
        }),
        ('媒体资源', {
            'fields': ('images', 'videos', 'documents'),
            'classes': ('collapse',)
        }),
        ('销售信息', {
            'fields': ('sales_points', 'keywords', 'sales_count', 'view_count'),
            'classes': ('collapse',)
        }),
        ('SEO优化', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('状态', {
            'fields': ('status',)
        }),
        ('创建信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    """话术模板管理"""
    list_display = [
        'name', 'script_type', 'status', 'priority', 'usage_count',
        'success_rate', 'is_active', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'script_type', 'status', 'is_active', 'ai_optimized', 'created_at'
    ]
    search_fields = ['name', 'content']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'category', 'name', 'script_type', 'content')
        }),
        ('模板变量', {
            'fields': ('variables', 'placeholders'),
            'classes': ('collapse',)
        }),
        ('使用条件', {
            'fields': ('conditions', 'triggers'),
            'classes': ('collapse',)
        }),
        ('状态和优先级', {
            'fields': ('status', 'priority', 'is_active')
        }),
        ('统计信息', {
            'fields': ('usage_count', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('AI增强', {
            'fields': ('ai_optimized', 'sentiment_score', 'effectiveness_score'),
            'classes': ('collapse',)
        }),
        ('创建信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(KnowledgeVector)
class KnowledgeVectorAdmin(admin.ModelAdmin):
    """知识向量管理"""
    list_display = [
        'knowledge_base', 'content_type', 'content_id', 'chunk_index',
        'embedding_model', 'vector_dimension', 'quality_score', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'content_type', 'embedding_model', 'language', 'created_at'
    ]
    search_fields = ['text_chunk']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'content_type', 'content_id')
        }),
        ('文本内容', {
            'fields': ('text_chunk', 'chunk_index', 'chunk_size')
        }),
        ('向量数据', {
            'fields': ('embedding_model', 'vector_dimension', 'quality_score', 'relevance_score'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('metadata', 'keywords', 'language'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KnowledgeAccessRecord)
class KnowledgeAccessRecordAdmin(admin.ModelAdmin):
    """知识访问记录管理"""
    list_display = [
        'knowledge_base', 'content_type', 'content_id', 'user', 'access_type',
        'response_time', 'success', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'content_type', 'access_type', 'success', 'created_at'
    ]
    search_fields = ['query_text', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'content_type', 'content_id')
        }),
        ('用户信息', {
            'fields': ('user', 'session_id', 'ip_address', 'user_agent')
        }),
        ('访问信息', {
            'fields': ('access_type', 'query_text', 'search_results_count')
        }),
        ('响应信息', {
            'fields': ('response_time', 'success', 'error_message')
        }),
        ('用户行为', {
            'fields': ('time_spent', 'scroll_depth', 'feedback_rating', 'feedback_comment'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )


@admin.register(KnowledgeRecommendation)
class KnowledgeRecommendationAdmin(admin.ModelAdmin):
    """知识推荐管理"""
    list_display = [
        'knowledge_base', 'source_content', 'target_content', 'recommendation_type',
        'similarity_score', 'click_count', 'conversion_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'knowledge_base', 'recommendation_type', 'is_active', 'created_at'
    ]
    readonly_fields = ['view_count', 'click_count', 'conversion_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('knowledge_base', 'recommendation_type', 'is_active')
        }),
        ('源内容', {
            'fields': ('source_content_type', 'source_content_id')
        }),
        ('目标内容', {
            'fields': ('target_content_type', 'target_content_id')
        }),
        ('评分信息', {
            'fields': ('similarity_score', 'confidence_score')
        }),
        ('算法信息', {
            'fields': ('algorithm', 'features_used'),
            'classes': ('collapse',)
        }),
        ('效果统计', {
            'fields': ('view_count', 'click_count', 'conversion_count'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def source_content(self, obj):
        return f"{obj.source_content_type}:{obj.source_content_id}"
    source_content.short_description = '源内容'
    
    def target_content(self, obj):
        return f"{obj.target_content_type}:{obj.target_content_id}"
    target_content.short_description = '目标内容' 