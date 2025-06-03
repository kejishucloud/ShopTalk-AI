from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomerService(models.Model):
    """客服配置"""
    
    class ServiceType(models.TextChoices):
        AI_ONLY = 'ai_only', '纯AI客服'
        HUMAN_ONLY = 'human_only', '纯人工客服'
        AI_HUMAN = 'ai_human', 'AI+人工客服'
    
    class ServiceStatus(models.TextChoices):
        ACTIVE = 'active', '运行中'
        PAUSED = 'paused', '暂停'
        STOPPED = 'stopped', '停止'
        ERROR = 'error', '异常'
    
    name = models.CharField('客服名称', max_length=100)
    service_type = models.CharField('服务类型', max_length=20, choices=ServiceType.choices)
    platform_account = models.ForeignKey(
        'platforms.PlatformAccount', 
        on_delete=models.CASCADE, 
        related_name='customer_services'
    )
    ai_model = models.ForeignKey(
        'ai_models.AIModel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='customer_services'
    )
    knowledge_bases = models.ManyToManyField(
        'knowledge.KnowledgeBase',
        blank=True,
        related_name='customer_services'
    )
    status = models.CharField('状态', max_length=20, choices=ServiceStatus.choices, default=ServiceStatus.ACTIVE)
    auto_reply_enabled = models.BooleanField('自动回复启用', default=True)
    human_takeover_enabled = models.BooleanField('人工接管启用', default=True)
    max_response_time = models.IntegerField('最大响应时间(秒)', default=30)
    greeting_message = models.TextField('欢迎语', blank=True)
    fallback_message = models.TextField('兜底回复', default='抱歉，我暂时无法理解您的问题，请稍后再试或联系人工客服。')
    settings = models.JSONField('配置参数', default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_services')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'customer_services'
        verbose_name = '客服配置'
        verbose_name_plural = '客服配置'
    
    def __str__(self):
        return f"{self.name} - {self.platform_account.account_name}"


class Conversation(models.Model):
    """对话会话"""
    
    class ConversationStatus(models.TextChoices):
        ACTIVE = 'active', '进行中'
        WAITING = 'waiting', '等待中'
        CLOSED = 'closed', '已结束'
        TRANSFERRED = 'transferred', '已转接'
    
    class ConversationSource(models.TextChoices):
        CUSTOMER_INITIATED = 'customer_initiated', '客户发起'
        SYSTEM_INITIATED = 'system_initiated', '系统发起'
        AGENT_INITIATED = 'agent_initiated', '客服发起'
    
    conversation_id = models.CharField('对话ID', max_length=100, unique=True)
    customer_service = models.ForeignKey(CustomerService, on_delete=models.CASCADE, related_name='conversations')
    customer_id = models.CharField('客户ID', max_length=100)
    customer_name = models.CharField('客户名称', max_length=100, blank=True)
    customer_info = models.JSONField('客户信息', default=dict, blank=True)
    status = models.CharField('状态', max_length=20, choices=ConversationStatus.choices, default=ConversationStatus.ACTIVE)
    source = models.CharField('来源', max_length=20, choices=ConversationSource.choices, default=ConversationSource.CUSTOMER_INITIATED)
    assigned_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_conversations')
    is_ai_handled = models.BooleanField('AI处理', default=True)
    priority = models.IntegerField('优先级', default=0)
    tags = models.JSONField('标签', default=list, blank=True)
    summary = models.TextField('对话摘要', blank=True)
    satisfaction_score = models.IntegerField('满意度评分', null=True, blank=True)
    started_at = models.DateTimeField('开始时间', auto_now_add=True)
    ended_at = models.DateTimeField('结束时间', null=True, blank=True)
    last_activity_at = models.DateTimeField('最后活动时间', auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        verbose_name = '对话会话'
        verbose_name_plural = '对话会话'
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['last_activity_at']),
        ]
    
    def __str__(self):
        return f"{self.conversation_id} - {self.customer_name}"


class Message(models.Model):
    """对话消息"""
    
    class MessageType(models.TextChoices):
        TEXT = 'text', '文本'
        IMAGE = 'image', '图片'
        AUDIO = 'audio', '音频'
        VIDEO = 'video', '视频'
        FILE = 'file', '文件'
        LINK = 'link', '链接'
        PRODUCT = 'product', '商品'
        SYSTEM = 'system', '系统消息'
    
    class SenderType(models.TextChoices):
        CUSTOMER = 'customer', '客户'
        AI_AGENT = 'ai_agent', 'AI客服'
        HUMAN_AGENT = 'human_agent', '人工客服'
        SYSTEM = 'system', '系统'
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message_id = models.CharField('消息ID', max_length=100)
    sender_type = models.CharField('发送者类型', max_length=20, choices=SenderType.choices)
    sender_id = models.CharField('发送者ID', max_length=100, blank=True)
    sender_name = models.CharField('发送者名称', max_length=100, blank=True)
    message_type = models.CharField('消息类型', max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField('消息内容')
    media_urls = models.JSONField('媒体链接', default=list, blank=True)
    metadata = models.JSONField('元数据', default=dict, blank=True)
    is_read = models.BooleanField('是否已读', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        verbose_name = '对话消息'
        verbose_name_plural = '对话消息'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['message_id']),
            models.Index(fields=['sender_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.conversation.conversation_id} - {self.sender_type} - {self.content[:50]}"


class AIAgent(models.Model):
    """AI智能客服代理"""
    
    class AgentStatus(models.TextChoices):
        ACTIVE = 'active', '运行中'
        PAUSED = 'paused', '暂停'
        TRAINING = 'training', '训练中'
        ERROR = 'error', '异常'
    
    name = models.CharField('代理名称', max_length=100)
    customer_service = models.OneToOneField(CustomerService, on_delete=models.CASCADE, related_name='ai_agent')
    system_prompt = models.TextField('系统提示词')
    personality = models.TextField('个性设置', blank=True)
    response_style = models.CharField('回复风格', max_length=50, default='professional')
    max_context_length = models.IntegerField('最大上下文长度', default=10)
    temperature = models.FloatField('创造性参数', default=0.7)
    confidence_threshold = models.FloatField('置信度阈值', default=0.8)
    enable_knowledge_search = models.BooleanField('启用知识库搜索', default=True)
    enable_intent_recognition = models.BooleanField('启用意图识别', default=True)
    enable_sentiment_analysis = models.BooleanField('启用情感分析', default=True)
    status = models.CharField('状态', max_length=20, choices=AgentStatus.choices, default=AgentStatus.ACTIVE)
    performance_metrics = models.JSONField('性能指标', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'ai_agents'
        verbose_name = 'AI智能代理'
        verbose_name_plural = 'AI智能代理'
    
    def __str__(self):
        return f"{self.name} - {self.customer_service.name}"


class IntentRecognition(models.Model):
    """意图识别"""
    
    class IntentType(models.TextChoices):
        PRODUCT_INQUIRY = 'product_inquiry', '商品咨询'
        PRICE_INQUIRY = 'price_inquiry', '价格咨询'
        ORDER_STATUS = 'order_status', '订单状态'
        COMPLAINT = 'complaint', '投诉建议'
        RETURN_REFUND = 'return_refund', '退换货'
        TECHNICAL_SUPPORT = 'technical_support', '技术支持'
        GREETING = 'greeting', '问候'
        GOODBYE = 'goodbye', '告别'
        OTHER = 'other', '其他'
    
    name = models.CharField('意图名称', max_length=100)
    intent_type = models.CharField('意图类型', max_length=20, choices=IntentType.choices)
    keywords = models.JSONField('关键词', default=list)
    patterns = models.JSONField('模式匹配', default=list, blank=True)
    examples = models.JSONField('示例语句', default=list, blank=True)
    confidence_threshold = models.FloatField('置信度阈值', default=0.8)
    response_templates = models.JSONField('回复模板', default=list, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='intent_recognitions')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'intent_recognitions'
        verbose_name = '意图识别'
        verbose_name_plural = '意图识别'
    
    def __str__(self):
        return f"{self.name} ({self.get_intent_type_display()})"


class ConversationContext(models.Model):
    """对话上下文"""
    
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name='context')
    current_intent = models.CharField('当前意图', max_length=50, blank=True)
    entities = models.JSONField('实体信息', default=dict, blank=True)
    session_data = models.JSONField('会话数据', default=dict, blank=True)
    conversation_history = models.JSONField('对话历史', default=list, blank=True)
    customer_profile = models.JSONField('客户画像', default=dict, blank=True)
    product_context = models.JSONField('商品上下文', default=dict, blank=True)
    last_ai_response = models.TextField('最后AI回复', blank=True)
    confidence_score = models.FloatField('置信度分数', default=0.0)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'conversation_contexts'
        verbose_name = '对话上下文'
        verbose_name_plural = '对话上下文'
    
    def __str__(self):
        return f"{self.conversation.conversation_id} - Context"


class AgentAction(models.Model):
    """代理动作记录"""
    
    class ActionType(models.TextChoices):
        KNOWLEDGE_SEARCH = 'knowledge_search', '知识库搜索'
        INTENT_RECOGNITION = 'intent_recognition', '意图识别'
        ENTITY_EXTRACTION = 'entity_extraction', '实体提取'
        SENTIMENT_ANALYSIS = 'sentiment_analysis', '情感分析'
        RESPONSE_GENERATION = 'response_generation', '回复生成'
        HUMAN_HANDOVER = 'human_handover', '人工接管'
        PRODUCT_RECOMMENDATION = 'product_recommendation', '商品推荐'
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='agent_actions')
    ai_agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField('动作类型', max_length=30, choices=ActionType.choices)
    input_data = models.JSONField('输入数据', default=dict, blank=True)
    output_data = models.JSONField('输出数据', default=dict, blank=True)
    confidence_score = models.FloatField('置信度', default=0.0)
    execution_time = models.FloatField('执行时间(毫秒)', default=0.0)
    success = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'agent_actions'
        verbose_name = '代理动作'
        verbose_name_plural = '代理动作'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.conversation.conversation_id} - {self.get_action_type_display()}" 