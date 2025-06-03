from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

User = get_user_model()


class KnowledgeBase(models.Model):
    """知识库"""
    
    class KnowledgeType(models.TextChoices):
        PRODUCT = 'product', '商品知识库'
        FAQ = 'faq', 'FAQ知识库'
        SCRIPT = 'script', '话术知识库'
        POLICY = 'policy', '政策知识库'
        TECHNICAL = 'technical', '技术文档'
        TRAINING = 'training', '培训资料'
        CUSTOM = 'custom', '自定义知识库'
    
    class AccessLevel(models.TextChoices):
        PUBLIC = 'public', '公开'
        INTERNAL = 'internal', '内部'
        RESTRICTED = 'restricted', '受限'
        PRIVATE = 'private', '私有'
    
    name = models.CharField('知识库名称', max_length=100)
    knowledge_type = models.CharField('知识库类型', max_length=20, choices=KnowledgeType.choices)
    description = models.TextField('描述', blank=True)
    access_level = models.CharField('访问级别', max_length=20, choices=AccessLevel.choices, default=AccessLevel.INTERNAL)
    is_active = models.BooleanField('是否启用', default=True)
    enable_version_control = models.BooleanField('启用版本控制', default=True)
    enable_ai_enhancement = models.BooleanField('启用AI增强', default=True)
    auto_extract_keywords = models.BooleanField('自动提取关键词', default=True)
    
    # RAGFlow集成配置
    ragflow_dataset_id = models.CharField('RAGFlow数据集ID', max_length=100, blank=True)
    ragflow_kb_id = models.CharField('RAGFlow知识库ID', max_length=100, blank=True)
    embedding_model = models.CharField('向量化模型', max_length=100, default='BAAI/bge-large-zh-v1.5')
    chunk_method = models.CharField('分块方法', max_length=50, default='intelligent')
    ragflow_config = models.JSONField('RAGFlow配置', default=dict, blank=True)
    
    # 统计信息
    total_documents = models.IntegerField('文档总数', default=0)
    total_qa_pairs = models.IntegerField('问答对总数', default=0)
    total_views = models.IntegerField('总访问次数', default=0)
    
    # 配置信息
    search_config = models.JSONField('搜索配置', default=dict, blank=True)
    permissions = models.JSONField('权限配置', default=dict, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_bases')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'knowledge_bases'
        verbose_name = '知识库'
        verbose_name_plural = '知识库'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_knowledge_type_display()})"

    def get_document_count(self):
        return self.documents.filter(is_active=True).count()
    
    def get_qa_count(self):
        return self.faqs.filter(is_active=True).count()
    
    def get_script_count(self):
        return self.scripts.filter(status='active').count()
    
    def get_product_count(self):
        return self.products.filter(status='active').count()


class DocumentCategory(models.Model):
    """文档分类"""
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField('分类名称', max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField('描述', blank=True)
    color = models.CharField('颜色标识', max_length=7, default='#007bff')
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'document_categories'
        verbose_name = '文档分类'
        verbose_name_plural = '文档分类'
        unique_together = ['knowledge_base', 'name', 'parent']
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class DocumentTag(models.Model):
    """文档标签"""
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField('标签名称', max_length=50)
    color = models.CharField('颜色', max_length=7, default='#6c757d')
    description = models.TextField('描述', blank=True)
    usage_count = models.IntegerField('使用次数', default=0)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'document_tags'
        verbose_name = '文档标签'
        verbose_name_plural = '文档标签'
        unique_together = ['knowledge_base', 'name']
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name


class Document(models.Model):
    """文档"""
    
    class DocumentType(models.TextChoices):
        TEXT = 'text', '文本文档'
        MARKDOWN = 'markdown', 'Markdown文档'
        HTML = 'html', 'HTML文档'
        PDF = 'pdf', 'PDF文档'
        WORD = 'word', 'Word文档'
        EXCEL = 'excel', 'Excel文档'
        IMAGE = 'image', '图片'
        VIDEO = 'video', '视频'
        AUDIO = 'audio', '音频'
    
    class ProcessStatus(models.TextChoices):
        PENDING = 'pending', '待处理'
        PROCESSING = 'processing', '处理中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '处理失败'
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='documents')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(DocumentTag, blank=True)
    
    title = models.CharField('文档标题', max_length=200)
    slug = models.SlugField('URL别名', max_length=200, blank=True)
    document_type = models.CharField('文档类型', max_length=20, choices=DocumentType.choices)
    file_path = models.FileField('文件路径', upload_to='knowledge/documents/', blank=True)
    content = models.TextField('文档内容', blank=True)
    summary = models.TextField('文档摘要', blank=True)
    
    # 元数据
    file_size = models.BigIntegerField('文件大小(字节)', default=0)
    file_hash = models.CharField('文件哈希', max_length=64, blank=True)
    language = models.CharField('语言', max_length=10, default='zh-cn')
    keywords = models.JSONField('关键词', default=list, blank=True)
    metadata = models.JSONField('元数据', default=dict, blank=True)
    
    # 处理状态
    process_status = models.CharField('处理状态', max_length=20, choices=ProcessStatus.choices, default=ProcessStatus.PENDING)
    process_message = models.TextField('处理信息', blank=True)
    extracted_text = models.TextField('提取的文本', blank=True)
    
    # 统计信息
    view_count = models.IntegerField('查看次数', default=0)
    download_count = models.IntegerField('下载次数', default=0)
    rating = models.FloatField('评分', default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    rating_count = models.IntegerField('评分次数', default=0)
    
    # 状态控制
    is_active = models.BooleanField('是否启用', default=True)
    is_featured = models.BooleanField('是否推荐', default=False)
    is_public = models.BooleanField('是否公开', default=False)
    
    # 版本信息
    version = models.CharField('版本号', max_length=20, default='1.0')
    parent_document = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='versions')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_documents', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'documents'
        verbose_name = '文档'
        verbose_name_plural = '文档'
        indexes = [
            models.Index(fields=['document_type']),
            models.Index(fields=['process_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['view_count']),
            models.Index(fields=['rating']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def add_rating(self, rating_value):
        total_rating = self.rating * self.rating_count + rating_value
        self.rating_count += 1
        self.rating = total_rating / self.rating_count
        self.save(update_fields=['rating', 'rating_count'])


class FAQ(models.Model):
    """常见问题"""
    
    class FAQStatus(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PUBLISHED = 'published', '已发布'
        ARCHIVED = 'archived', '已归档'
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='faqs')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(DocumentTag, blank=True)
    
    question = models.TextField('问题')
    answer = models.TextField('答案')
    answer_html = models.TextField('答案HTML', blank=True)
    
    # 分类和标识
    faq_category = models.CharField('FAQ分类', max_length=100, blank=True)
    keywords = models.JSONField('关键词', default=list, blank=True)
    related_questions = models.JSONField('相关问题', default=list, blank=True)
    
    # 优先级和状态
    priority = models.IntegerField('优先级', default=0)
    status = models.CharField('状态', max_length=20, choices=FAQStatus.choices, default=FAQStatus.DRAFT)
    is_active = models.BooleanField('是否启用', default=True)
    is_featured = models.BooleanField('是否推荐', default=False)
    
    # 统计信息
    view_count = models.IntegerField('查看次数', default=0)
    helpful_count = models.IntegerField('有用次数', default=0)
    unhelpful_count = models.IntegerField('无用次数', default=0)
    
    # 智能增强
    auto_generated = models.BooleanField('AI自动生成', default=False)
    confidence_score = models.FloatField('置信度', default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    source_documents = models.JSONField('来源文档', default=list, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='faqs')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_faqs', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'faqs'
        verbose_name = '常见问题'
        verbose_name_plural = '常见问题'
        indexes = [
            models.Index(fields=['faq_category']),
            models.Index(fields=['priority']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['view_count']),
            models.Index(fields=['confidence_score']),
        ]
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.question[:100]

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def mark_helpful(self):
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])

    def mark_unhelpful(self):
        self.unhelpful_count += 1
        self.save(update_fields=['unhelpful_count'])

    @property
    def helpfulness_ratio(self):
        total = self.helpful_count + self.unhelpful_count
        return (self.helpful_count / total) if total > 0 else 0


class Product(models.Model):
    """商品信息"""
    
    class ProductStatus(models.TextChoices):
        ACTIVE = 'active', '在售'
        INACTIVE = 'inactive', '下架'
        OUT_OF_STOCK = 'out_of_stock', '缺货'
        DISCONTINUED = 'discontinued', '停产'
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(DocumentTag, blank=True)
    
    sku = models.CharField('商品SKU', max_length=100, unique=True)
    name = models.CharField('商品名称', max_length=200)
    product_category = models.CharField('商品分类', max_length=100, blank=True)
    brand = models.CharField('品牌', max_length=100, blank=True)
    
    # 价格信息
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    original_price = models.DecimalField('原价', max_digits=10, decimal_places=2, blank=True, null=True)
    cost_price = models.DecimalField('成本价', max_digits=10, decimal_places=2, blank=True, null=True)
    
    # 库存信息
    stock_quantity = models.IntegerField('库存数量', default=0)
    min_stock_level = models.IntegerField('最小库存', default=0)
    max_stock_level = models.IntegerField('最大库存', default=0)
    
    status = models.CharField('状态', max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    description = models.TextField('商品描述', blank=True)
    short_description = models.CharField('简短描述', max_length=500, blank=True)
    
    # 规格和属性
    specifications = models.JSONField('规格参数', default=dict, blank=True)
    attributes = models.JSONField('商品属性', default=dict, blank=True)
    variants = models.JSONField('规格变体', default=list, blank=True)
    
    # 媒体资源
    images = models.JSONField('商品图片', default=list, blank=True)
    videos = models.JSONField('商品视频', default=list, blank=True)
    documents = models.JSONField('相关文档', default=list, blank=True)
    
    # 销售信息
    sales_points = models.JSONField('卖点', default=list, blank=True)
    keywords = models.JSONField('关键词', default=list, blank=True)
    sales_count = models.IntegerField('销售数量', default=0)
    view_count = models.IntegerField('查看次数', default=0)
    
    # SEO优化
    meta_title = models.CharField('SEO标题', max_length=200, blank=True)
    meta_description = models.TextField('SEO描述', blank=True)
    meta_keywords = models.CharField('SEO关键词', max_length=500, blank=True)
    
    # RAGFlow集成字段
    ragflow_document_id = models.CharField('RAGFlow文档ID', max_length=100, blank=True)
    ragflow_chunk_ids = models.JSONField('RAGFlow块ID列表', default=list, blank=True)
    vector_synced = models.BooleanField('向量已同步', default=False)
    last_sync_time = models.DateTimeField('最后同步时间', null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_products', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = '商品'
        verbose_name_plural = '商品'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product_category']),
            models.Index(fields=['brand']),
            models.Index(fields=['status']),
            models.Index(fields=['price']),
            models.Index(fields=['stock_quantity']),
            models.Index(fields=['vector_synced']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0 and self.status == self.ProductStatus.ACTIVE

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return ((self.original_price - self.price) / self.original_price) * 100
        return 0
    
    def mark_vector_synced(self):
        """标记向量已同步"""
        self.vector_synced = True
        self.last_sync_time = timezone.now()
        self.save(update_fields=['vector_synced', 'last_sync_time'])
    
    def needs_sync(self):
        """检查是否需要同步"""
        if not self.vector_synced:
            return True
        return self.updated_at > self.last_sync_time if self.last_sync_time else True
    
    def get_text_for_vectorization(self):
        """获取用于向量化的文本内容"""
        text_parts = [
            f"商品名称: {self.name}",
            f"商品SKU: {self.sku}",
            f"品牌: {self.brand}" if self.brand else "",
            f"分类: {self.product_category}" if self.product_category else "",
            f"价格: {self.price}",
            f"描述: {self.description}" if self.description else "",
            f"简短描述: {self.short_description}" if self.short_description else "",
        ]
        
        # 添加卖点
        if self.sales_points:
            text_parts.append(f"卖点: {', '.join(self.sales_points)}")
        
        # 添加关键词
        if self.keywords:
            text_parts.append(f"关键词: {', '.join(self.keywords)}")
        
        # 添加规格参数
        if self.specifications:
            specs_text = ', '.join([f"{k}: {v}" for k, v in self.specifications.items()])
            text_parts.append(f"规格参数: {specs_text}")
        
        return '\n'.join(filter(None, text_parts))


class Script(models.Model):
    """话术模板"""
    
    class ScriptType(models.TextChoices):
        GREETING = 'greeting', '问候语'
        PRODUCT_INTRO = 'product_intro', '商品介绍'
        PRICE_NEGOTIATION = 'price_negotiation', '价格协商'
        ORDER_CONFIRMATION = 'order_confirmation', '订单确认'
        AFTER_SALES = 'after_sales', '售后服务'
        OBJECTION_HANDLING = 'objection_handling', '异议处理'
        CLOSING = 'closing', '结束语'
        UPSELLING = 'upselling', '追加销售'
        CROSS_SELLING = 'cross_selling', '交叉销售'
    
    class ScriptStatus(models.TextChoices):
        DRAFT = 'draft', '草稿'
        ACTIVE = 'active', '启用'
        TESTING = 'testing', '测试中'
        ARCHIVED = 'archived', '已归档'
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='scripts')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(DocumentTag, blank=True)
    
    name = models.CharField('话术名称', max_length=100)
    script_type = models.CharField('话术类型', max_length=20, choices=ScriptType.choices)
    content = models.TextField('话术内容')
    
    # RAGFlow集成字段
    ragflow_document_id = models.CharField('RAGFlow文档ID', max_length=100, blank=True)
    ragflow_chunk_ids = models.JSONField('RAGFlow块ID列表', default=list, blank=True)
    vector_synced = models.BooleanField('向量已同步', default=False)
    last_sync_time = models.DateTimeField('最后同步时间', null=True, blank=True)
    
    # 模板变量
    variables = models.JSONField('变量定义', default=dict, blank=True)
    placeholders = models.JSONField('占位符说明', default=dict, blank=True)
    
    # 使用条件
    conditions = models.JSONField('使用条件', default=dict, blank=True)
    triggers = models.JSONField('触发条件', default=list, blank=True)
    
    # 状态和优先级
    status = models.CharField('状态', max_length=20, choices=ScriptStatus.choices, default=ScriptStatus.DRAFT)
    priority = models.IntegerField('优先级', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    
    # 统计信息
    usage_count = models.IntegerField('使用次数', default=0)
    success_rate = models.FloatField('成功率', default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    # AI增强
    ai_optimized = models.BooleanField('AI优化', default=False)
    sentiment_score = models.FloatField('情感评分', default=0.0)
    effectiveness_score = models.FloatField('效果评分', default=0.0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scripts')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_scripts', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'scripts'
        verbose_name = '话术模板'
        verbose_name_plural = '话术模板'
        indexes = [
            models.Index(fields=['script_type']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_active']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['vector_synced']),
        ]
        ordering = ['-priority', '-usage_count']
    
    def __str__(self):
        return f"{self.name} ({self.get_script_type_display()})"

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def mark_vector_synced(self):
        """标记向量已同步"""
        self.vector_synced = True
        self.last_sync_time = timezone.now()
        self.save(update_fields=['vector_synced', 'last_sync_time'])
    
    def needs_sync(self):
        """检查是否需要同步"""
        if not self.vector_synced:
            return True
        return self.updated_at > self.last_sync_time if self.last_sync_time else True
    
    def get_text_for_vectorization(self):
        """获取用于向量化的文本内容"""
        text_parts = [
            f"话术名称: {self.name}",
            f"话术类型: {self.get_script_type_display()}",
            f"话术内容: {self.content}",
        ]
        
        # 添加变量定义
        if self.variables:
            vars_text = ', '.join([f"{k}: {v}" for k, v in self.variables.items()])
            text_parts.append(f"变量定义: {vars_text}")
        
        # 添加使用条件
        if self.conditions:
            conditions_text = ', '.join([f"{k}: {v}" for k, v in self.conditions.items()])
            text_parts.append(f"使用条件: {conditions_text}")
        
        # 添加触发条件
        if self.triggers:
            text_parts.append(f"触发条件: {', '.join(self.triggers)}")
            
        return '\n'.join(filter(None, text_parts))


class KnowledgeVector(models.Model):
    """知识向量"""
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='vectors')
    content_type = models.CharField('内容类型', max_length=20)  # document, faq, product, script
    content_id = models.IntegerField('内容ID')
    
    text_chunk = models.TextField('文本片段')
    chunk_index = models.IntegerField('片段索引', default=0)
    chunk_size = models.IntegerField('片段大小', default=0)
    
    # 向量数据
    embedding_model = models.CharField('向量模型', max_length=100)
    vector_data = models.JSONField('向量数据')
    vector_dimension = models.IntegerField('向量维度')
    
    # 元数据
    metadata = models.JSONField('元数据', default=dict, blank=True)
    keywords = models.JSONField('关键词', default=list, blank=True)
    language = models.CharField('语言', max_length=10, default='zh-cn')
    
    # 质量评分
    quality_score = models.FloatField('质量评分', default=0.0)
    relevance_score = models.FloatField('相关性评分', default=0.0)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'knowledge_vectors'
        verbose_name = '知识向量'
        verbose_name_plural = '知识向量'
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['knowledge_base']),
            models.Index(fields=['embedding_model']),
            models.Index(fields=['quality_score']),
        ]
        unique_together = ['knowledge_base', 'content_type', 'content_id', 'chunk_index']
    
    def __str__(self):
        return f"{self.content_type}:{self.content_id}:{self.chunk_index} - {self.text_chunk[:50]}"


class KnowledgeAccessRecord(models.Model):
    """知识访问记录"""
    
    class AccessType(models.TextChoices):
        VIEW = 'view', '查看'
        SEARCH = 'search', '搜索'
        DOWNLOAD = 'download', '下载'
        SHARE = 'share', '分享'
        FEEDBACK = 'feedback', '反馈'
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='access_records')
    content_type = models.CharField('内容类型', max_length=20, blank=True)
    content_id = models.IntegerField('内容ID', null=True, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField('会话ID', max_length=100, blank=True)
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.TextField('用户代理', blank=True)
    
    access_type = models.CharField('访问类型', max_length=20, choices=AccessType.choices)
    query_text = models.TextField('查询文本', blank=True)
    search_results_count = models.IntegerField('搜索结果数', default=0)
    
    # 响应信息
    response_time = models.FloatField('响应时间(秒)', default=0.0)
    success = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True)
    
    # 用户行为
    time_spent = models.IntegerField('停留时间(秒)', default=0)
    scroll_depth = models.FloatField('滚动深度', default=0.0)
    feedback_rating = models.IntegerField('反馈评分', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback_comment = models.TextField('反馈意见', blank=True)
    
    created_at = models.DateTimeField('访问时间', auto_now_add=True)
    
    class Meta:
        db_table = 'knowledge_access_records'
        verbose_name = '知识访问记录'
        verbose_name_plural = '知识访问记录'
        indexes = [
            models.Index(fields=['knowledge_base', 'created_at']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['access_type']),
            models.Index(fields=['session_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_access_type_display()} - {self.knowledge_base.name} - {self.created_at}"


class KnowledgeRecommendation(models.Model):
    """知识推荐"""
    
    class RecommendationType(models.TextChoices):
        SIMILAR = 'similar', '相似内容'
        RELATED = 'related', '相关内容'
        POPULAR = 'popular', '热门内容'
        PERSONALIZED = 'personalized', '个性化推荐'
        AI_GENERATED = 'ai_generated', 'AI生成推荐'
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='recommendations')
    source_content_type = models.CharField('源内容类型', max_length=20)
    source_content_id = models.IntegerField('源内容ID')
    
    target_content_type = models.CharField('目标内容类型', max_length=20)
    target_content_id = models.IntegerField('目标内容ID')
    
    recommendation_type = models.CharField('推荐类型', max_length=20, choices=RecommendationType.choices)
    similarity_score = models.FloatField('相似度评分', validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    confidence_score = models.FloatField('置信度', validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # 推荐算法信息
    algorithm = models.CharField('推荐算法', max_length=100, blank=True)
    features_used = models.JSONField('使用特征', default=list, blank=True)
    
    # 效果统计
    view_count = models.IntegerField('查看次数', default=0)
    click_count = models.IntegerField('点击次数', default=0)
    conversion_count = models.IntegerField('转化次数', default=0)
    
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'knowledge_recommendations'
        verbose_name = '知识推荐'
        verbose_name_plural = '知识推荐'
        indexes = [
            models.Index(fields=['source_content_type', 'source_content_id']),
            models.Index(fields=['target_content_type', 'target_content_id']),
            models.Index(fields=['recommendation_type']),
            models.Index(fields=['similarity_score']),
            models.Index(fields=['is_active']),
        ]
        unique_together = [
            'knowledge_base', 'source_content_type', 'source_content_id',
            'target_content_type', 'target_content_id', 'recommendation_type'
        ]
        ordering = ['-similarity_score', '-confidence_score']
    
    def __str__(self):
        return f"{self.source_content_type}:{self.source_content_id} -> {self.target_content_type}:{self.target_content_id}"

    @property
    def click_through_rate(self):
        return (self.click_count / self.view_count) if self.view_count > 0 else 0

    @property
    def conversion_rate(self):
        return (self.conversion_count / self.click_count) if self.click_count > 0 else 0 