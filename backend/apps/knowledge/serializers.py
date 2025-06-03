"""
知识库管理序列化器
提供API数据序列化和反序列化功能
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    KnowledgeBase, DocumentCategory, DocumentTag, Document, FAQ, Product, 
    Script, KnowledgeVector, KnowledgeAccessRecord, KnowledgeRecommendation
)

User = get_user_model()


class DocumentCategorySerializer(serializers.ModelSerializer):
    """文档分类序列化器"""
    children_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'parent', 'parent_name', 'description', 'color', 
            'sort_order', 'is_active', 'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()


class DocumentTagSerializer(serializers.ModelSerializer):
    """文档标签序列化器"""
    
    class Meta:
        model = DocumentTag
        fields = [
            'id', 'name', 'color', 'description', 'usage_count', 'created_at'
        ]
        read_only_fields = ['usage_count', 'created_at']


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """知识库序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    knowledge_type_display = serializers.CharField(source='get_knowledge_type_display', read_only=True)
    access_level_display = serializers.CharField(source='get_access_level_display', read_only=True)
    document_count = serializers.SerializerMethodField()
    qa_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'name', 'knowledge_type', 'knowledge_type_display', 'description',
            'access_level', 'access_level_display', 'is_active', 'enable_version_control',
            'enable_ai_enhancement', 'auto_extract_keywords', 'total_documents',
            'total_qa_pairs', 'total_views', 'embedding_model', 'search_config',
            'permissions', 'document_count', 'qa_count', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_documents', 'total_qa_pairs', 'total_views', 'created_at', 'updated_at']
    
    def get_document_count(self, obj):
        return obj.get_document_count()
    
    def get_qa_count(self, obj):
        return obj.get_qa_count()


class DocumentSerializer(serializers.ModelSerializer):
    """文档序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    process_status_display = serializers.CharField(source='get_process_status_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'category', 'category_name',
            'tags', 'tag_ids', 'title', 'slug', 'document_type', 'document_type_display',
            'file_path', 'content', 'summary', 'file_size', 'file_size_mb', 'file_hash',
            'language', 'keywords', 'metadata', 'process_status', 'process_status_display',
            'process_message', 'extracted_text', 'view_count', 'download_count', 'rating',
            'rating_count', 'is_active', 'is_featured', 'is_public', 'version',
            'parent_document', 'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'file_size', 'file_hash', 'extracted_text', 'view_count', 'download_count',
            'rating', 'rating_count', 'created_at', 'updated_at'
        ]
    
    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2) if obj.file_size > 0 else 0
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        document = Document.objects.create(**validated_data)
        if tag_ids:
            document.tags.set(tag_ids)
        return document
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance


class FAQSerializer(serializers.ModelSerializer):
    """FAQ序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    helpfulness_ratio = serializers.ReadOnlyField()
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'category', 'category_name',
            'tags', 'tag_ids', 'question', 'answer', 'answer_html', 'faq_category',
            'keywords', 'related_questions', 'priority', 'status', 'status_display',
            'is_active', 'is_featured', 'view_count', 'helpful_count', 'unhelpful_count',
            'helpfulness_ratio', 'auto_generated', 'confidence_score', 'source_documents',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'view_count', 'helpful_count', 'unhelpful_count', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        faq = FAQ.objects.create(**validated_data)
        if tag_ids:
            faq.tags.set(tag_ids)
        return faq
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance


class ProductSerializer(serializers.ModelSerializer):
    """商品序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_in_stock = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'category', 'category_name',
            'tags', 'tag_ids', 'sku', 'name', 'product_category', 'brand', 'price',
            'original_price', 'cost_price', 'stock_quantity', 'min_stock_level',
            'max_stock_level', 'status', 'status_display', 'description', 'short_description',
            'specifications', 'attributes', 'variants', 'images', 'videos', 'documents',
            'sales_points', 'keywords', 'sales_count', 'view_count', 'meta_title',
            'meta_description', 'meta_keywords', 'is_in_stock', 'discount_percentage',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['sales_count', 'view_count', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        product = Product.objects.create(**validated_data)
        if tag_ids:
            product.tags.set(tag_ids)
        return product
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance


class ScriptSerializer(serializers.ModelSerializer):
    """话术模板序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    script_type_display = serializers.CharField(source='get_script_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Script
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'category', 'category_name',
            'tags', 'tag_ids', 'name', 'script_type', 'script_type_display', 'content',
            'variables', 'placeholders', 'conditions', 'triggers', 'status', 'status_display',
            'priority', 'is_active', 'usage_count', 'success_rate', 'ai_optimized',
            'sentiment_score', 'effectiveness_score', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['usage_count', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        script = Script.objects.create(**validated_data)
        if tag_ids:
            script.tags.set(tag_ids)
        return script
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance


class KnowledgeVectorSerializer(serializers.ModelSerializer):
    """知识向量序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    
    class Meta:
        model = KnowledgeVector
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'content_type', 'content_id',
            'text_chunk', 'chunk_index', 'chunk_size', 'embedding_model', 'vector_data',
            'vector_dimension', 'metadata', 'keywords', 'language', 'quality_score',
            'relevance_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class KnowledgeAccessRecordSerializer(serializers.ModelSerializer):
    """知识访问记录序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    access_type_display = serializers.CharField(source='get_access_type_display', read_only=True)
    
    class Meta:
        model = KnowledgeAccessRecord
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'content_type', 'content_id',
            'user', 'user_name', 'session_id', 'ip_address', 'user_agent', 'access_type',
            'access_type_display', 'query_text', 'search_results_count', 'response_time',
            'success', 'error_message', 'time_spent', 'scroll_depth', 'feedback_rating',
            'feedback_comment', 'created_at'
        ]
        read_only_fields = ['created_at']


class KnowledgeRecommendationSerializer(serializers.ModelSerializer):
    """知识推荐序列化器"""
    knowledge_base_name = serializers.CharField(source='knowledge_base.name', read_only=True)
    recommendation_type_display = serializers.CharField(source='get_recommendation_type_display', read_only=True)
    click_through_rate = serializers.ReadOnlyField()
    conversion_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = KnowledgeRecommendation
        fields = [
            'id', 'knowledge_base', 'knowledge_base_name', 'source_content_type',
            'source_content_id', 'target_content_type', 'target_content_id',
            'recommendation_type', 'recommendation_type_display', 'similarity_score',
            'confidence_score', 'algorithm', 'features_used', 'view_count', 'click_count',
            'conversion_count', 'click_through_rate', 'conversion_rate', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['view_count', 'click_count', 'conversion_count', 'created_at', 'updated_at']


# 搜索相关序列化器
class KnowledgeSearchRequestSerializer(serializers.Serializer):
    """知识搜索请求序列化器"""
    query = serializers.CharField(max_length=500, help_text="搜索查询")
    knowledge_base_id = serializers.IntegerField(required=False, help_text="知识库ID")
    content_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="内容类型筛选"
    )
    categories = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="分类筛选"
    )
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="标签筛选"
    )
    limit = serializers.IntegerField(default=20, max_value=100, help_text="结果数量限制")
    include_vectors = serializers.BooleanField(default=False, help_text="是否包含向量搜索")
    similarity_threshold = serializers.FloatField(default=0.5, min_value=0.0, max_value=1.0, help_text="相似度阈值")


class KnowledgeSearchResultSerializer(serializers.Serializer):
    """知识搜索结果序列化器"""
    content_type = serializers.CharField()
    content_id = serializers.IntegerField()
    title = serializers.CharField()
    summary = serializers.CharField()
    score = serializers.FloatField()
    source = serializers.CharField()
    url = serializers.CharField()
    highlights = serializers.ListField(child=serializers.CharField())
    metadata = serializers.DictField()


class DocumentUploadSerializer(serializers.Serializer):
    """文档上传序列化器"""
    knowledge_base_id = serializers.IntegerField(help_text="知识库ID")
    category_id = serializers.IntegerField(required=False, help_text="分类ID")
    title = serializers.CharField(max_length=200, help_text="文档标题")
    file = serializers.FileField(help_text="上传文件")
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="标签ID列表"
    )
    auto_extract = serializers.BooleanField(default=True, help_text="是否自动提取内容")
    auto_vectorize = serializers.BooleanField(default=True, help_text="是否自动向量化")


class BatchOperationSerializer(serializers.Serializer):
    """批量操作序列化器"""
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete', 'move_category', 'add_tags', 'remove_tags'],
        help_text="操作类型"
    )
    content_type = serializers.CharField(help_text="内容类型")
    content_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="内容ID列表"
    )
    target_category_id = serializers.IntegerField(required=False, help_text="目标分类ID")
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="标签ID列表"
    )


class KnowledgeAnalyticsSerializer(serializers.Serializer):
    """知识分析统计序列化器"""
    knowledge_base_id = serializers.IntegerField(required=False, help_text="知识库ID")
    date_from = serializers.DateField(required=False, help_text="开始日期")
    date_to = serializers.DateField(required=False, help_text="结束日期")
    group_by = serializers.ChoiceField(
        choices=['day', 'week', 'month'],
        default='day',
        help_text="分组方式"
    )
    metrics = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="指标列表"
    ) 