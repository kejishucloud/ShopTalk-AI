"""
知识库API序列化器
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    KnowledgeBase, Script, Product, Document, FAQ, 
    DocumentCategory, DocumentTag, KnowledgeVector
)

User = get_user_model()

class DocumentTagSerializer(serializers.ModelSerializer):
    """文档标签序列化器"""
    
    class Meta:
        model = DocumentTag
        fields = ['id', 'name', 'color', 'description', 'usage_count', 'created_at']
        read_only_fields = ['usage_count', 'created_at']

class DocumentCategorySerializer(serializers.ModelSerializer):
    """文档分类序列化器"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'parent', 'description', 'color', 
            'sort_order', 'is_active', 'children', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children(self, obj):
        if obj.children.exists():
            return DocumentCategorySerializer(obj.children.all(), many=True).data
        return []

class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """知识库序列化器"""
    
    created_by = serializers.StringRelatedField(read_only=True)
    knowledge_type_display = serializers.CharField(source='get_knowledge_type_display', read_only=True)
    access_level_display = serializers.CharField(source='get_access_level_display', read_only=True)
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'name', 'knowledge_type', 'knowledge_type_display',
            'description', 'access_level', 'access_level_display', 
            'is_active', 'enable_version_control', 'enable_ai_enhancement',
            'auto_extract_keywords', 'total_documents', 'total_qa_pairs',
            'total_views', 'embedding_model', 'search_config', 'permissions',
            'created_by', 'document_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'total_documents', 'total_qa_pairs', 'total_views', 
            'created_by', 'document_count', 'created_at', 'updated_at'
        ]
    
    def get_document_count(self, obj):
        return obj.get_document_count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class ScriptSerializer(serializers.ModelSerializer):
    """话术序列化器"""
    
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    script_type_display = serializers.CharField(source='get_script_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Script
        fields = [
            'id', 'knowledge_base', 'category', 'tags', 'tag_ids',
            'name', 'script_type', 'script_type_display', 'content',
            'variables', 'placeholders', 'conditions', 'triggers',
            'status', 'status_display', 'priority', 'is_active',
            'usage_count', 'success_rate', 'ai_optimized',
            'sentiment_score', 'effectiveness_score',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'usage_count', 'success_rate', 'ai_optimized',
            'sentiment_score', 'effectiveness_score',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['created_by'] = self.context['request'].user
        
        script = super().create(validated_data)
        
        if tag_ids:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=script.knowledge_base
            )
            script.tags.set(tags)
        
        return script
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        validated_data['updated_by'] = self.context['request'].user
        
        script = super().update(instance, validated_data)
        
        if tag_ids is not None:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=script.knowledge_base
            )
            script.tags.set(tags)
        
        return script

class ProductSerializer(serializers.ModelSerializer):
    """产品序列化器"""
    
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'knowledge_base', 'category', 'tags', 'tag_ids',
            'sku', 'name', 'product_category', 'brand',
            'price', 'original_price', 'cost_price', 'discount_percentage',
            'stock_quantity', 'min_stock_level', 'max_stock_level',
            'is_in_stock', 'status', 'status_display',
            'description', 'short_description', 'specifications',
            'attributes', 'variants', 'images', 'videos', 'documents',
            'sales_points', 'keywords', 'sales_count', 'view_count',
            'meta_title', 'meta_description', 'meta_keywords',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'is_in_stock', 'discount_percentage', 'sales_count',
            'view_count', 'created_by', 'updated_by', 
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['created_by'] = self.context['request'].user
        
        product = super().create(validated_data)
        
        if tag_ids:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=product.knowledge_base
            )
            product.tags.set(tags)
        
        return product
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        validated_data['updated_by'] = self.context['request'].user
        
        product = super().update(instance, validated_data)
        
        if tag_ids is not None:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=product.knowledge_base
            )
            product.tags.set(tags)
        
        return product

class DocumentSerializer(serializers.ModelSerializer):
    """文档序列化器"""
    
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    process_status_display = serializers.CharField(source='get_process_status_display', read_only=True)
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'knowledge_base', 'category', 'tags', 'tag_ids',
            'title', 'slug', 'document_type', 'document_type_display',
            'file_path', 'content', 'summary', 'file_size', 'file_size_display',
            'file_hash', 'language', 'keywords', 'metadata',
            'process_status', 'process_status_display', 'process_message',
            'extracted_text', 'view_count', 'download_count',
            'rating', 'rating_count', 'is_active', 'is_featured', 'is_public',
            'version', 'parent_document', 'created_by', 'updated_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'file_size', 'file_hash', 'process_status', 'process_message',
            'extracted_text', 'view_count', 'download_count',
            'rating', 'rating_count', 'created_by', 'updated_by',
            'created_at', 'updated_at'
        ]
    
    def get_file_size_display(self, obj):
        """格式化文件大小显示"""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['created_by'] = self.context['request'].user
        
        document = super().create(validated_data)
        
        if tag_ids:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=document.knowledge_base
            )
            document.tags.set(tags)
        
        return document
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        validated_data['updated_by'] = self.context['request'].user
        
        document = super().update(instance, validated_data)
        
        if tag_ids is not None:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=document.knowledge_base
            )
            document.tags.set(tags)
        
        return document

class FAQSerializer(serializers.ModelSerializer):
    """FAQ序列化器"""
    
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    helpfulness_ratio = serializers.FloatField(read_only=True)
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'knowledge_base', 'category', 'tags', 'tag_ids',
            'question', 'answer', 'answer_html', 'faq_category',
            'keywords', 'related_questions', 'priority',
            'status', 'status_display', 'is_active', 'is_featured',
            'view_count', 'helpful_count', 'unhelpful_count', 'helpfulness_ratio',
            'auto_generated', 'confidence_score', 'source_documents',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'view_count', 'helpful_count', 'unhelpful_count', 'helpfulness_ratio',
            'auto_generated', 'confidence_score', 'source_documents',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['created_by'] = self.context['request'].user
        
        faq = super().create(validated_data)
        
        if tag_ids:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=faq.knowledge_base
            )
            faq.tags.set(tags)
        
        return faq
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        validated_data['updated_by'] = self.context['request'].user
        
        faq = super().update(instance, validated_data)
        
        if tag_ids is not None:
            tags = DocumentTag.objects.filter(
                id__in=tag_ids,
                knowledge_base=faq.knowledge_base
            )
            faq.tags.set(tags)
        
        return faq

class KnowledgeSearchSerializer(serializers.Serializer):
    """知识搜索序列化器"""
    
    query = serializers.CharField(max_length=500, help_text="搜索查询")
    knowledge_base_id = serializers.IntegerField(help_text="知识库ID")
    content_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['script', 'product', 'document', 'faq']),
        required=False,
        help_text="内容类型过滤"
    )
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=50, help_text="返回结果数量")
    similarity_threshold = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0, help_text="相似度阈值")

class BatchImportSerializer(serializers.Serializer):
    """批量导入序列化器"""
    
    knowledge_base_id = serializers.IntegerField(help_text="知识库ID")
    content_type = serializers.ChoiceField(
        choices=['scripts', 'products'],
        help_text="导入内容类型"
    )
    file = serializers.FileField(help_text="导入文件")
    
    def validate_file(self, value):
        """验证上传文件"""
        allowed_extensions = ['csv', 'json', 'xlsx', 'xls']
        file_ext = value.name.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 检查文件大小 (50MB)
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(f"文件大小超过限制: {value.size / (1024*1024):.1f}MB > 50MB")
        
        return value
    
    def validate_knowledge_base_id(self, value):
        """验证知识库ID"""
        try:
            kb = KnowledgeBase.objects.get(id=value)
            if not kb.is_active:
                raise serializers.ValidationError("知识库未激活")
        except KnowledgeBase.DoesNotExist:
            raise serializers.ValidationError("知识库不存在")
        
        return value

class KnowledgeStatsSerializer(serializers.Serializer):
    """知识库统计序列化器"""
    
    knowledge_base_id = serializers.IntegerField(read_only=True)
    knowledge_base_name = serializers.CharField(read_only=True)
    total_scripts = serializers.IntegerField(read_only=True)
    total_products = serializers.IntegerField(read_only=True)
    total_documents = serializers.IntegerField(read_only=True)
    total_faqs = serializers.IntegerField(read_only=True)
    total_vectors = serializers.IntegerField(read_only=True)
    last_sync_time = serializers.DateTimeField(read_only=True)
    sync_status = serializers.CharField(read_only=True) 