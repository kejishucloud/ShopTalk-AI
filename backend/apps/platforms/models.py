from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Platform(models.Model):
    """平台配置"""
    
    class PlatformType(models.TextChoices):
        TAOBAO = 'taobao', '淘宝'
        JD = 'jd', '京东'
        PDD = 'pdd', '拼多多'
        DOUYIN = 'douyin', '抖音'
        XIAOHONGSHU = 'xiaohongshu', '小红书'
        WECHAT = 'wechat', '微信'
        WEIBO = 'weibo', '微博'
        QIANNIU = 'qianniu', '千牛'
        JINGMAI = 'jingmai', '京麦'
    
    name = models.CharField('平台名称', max_length=100)
    platform_type = models.CharField('平台类型', max_length=20, choices=PlatformType.choices)
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    api_config = models.JSONField('API配置', default=dict, blank=True)
    webhook_config = models.JSONField('Webhook配置', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'platforms'
        verbose_name = '平台'
        verbose_name_plural = '平台'
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_type_display()})"


class PlatformAccount(models.Model):
    """平台账号"""
    
    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', '正常'
        INACTIVE = 'inactive', '停用'
        SUSPENDED = 'suspended', '暂停'
        ERROR = 'error', '异常'
    
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='accounts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='platform_accounts')
    account_name = models.CharField('账号名称', max_length=100)
    account_id = models.CharField('账号ID', max_length=100)
    credentials = models.JSONField('认证信息', default=dict, blank=True)
    status = models.CharField('状态', max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    last_sync_at = models.DateTimeField('最后同步时间', blank=True, null=True)
    sync_error = models.TextField('同步错误', blank=True)
    settings = models.JSONField('账号设置', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'platform_accounts'
        verbose_name = '平台账号'
        verbose_name_plural = '平台账号'
        unique_together = ['platform', 'account_id']
    
    def __str__(self):
        return f"{self.platform.name} - {self.account_name}"


class AutoReplyRule(models.Model):
    """自动回复规则"""
    
    class RuleType(models.TextChoices):
        KEYWORD = 'keyword', '关键词匹配'
        INTENT = 'intent', '意图识别'
        TIME_BASED = 'time_based', '时间规则'
        CONDITION = 'condition', '条件规则'
    
    class MatchMode(models.TextChoices):
        EXACT = 'exact', '精确匹配'
        CONTAINS = 'contains', '包含匹配'
        REGEX = 'regex', '正则匹配'
        FUZZY = 'fuzzy', '模糊匹配'
    
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name='auto_reply_rules')
    name = models.CharField('规则名称', max_length=100)
    rule_type = models.CharField('规则类型', max_length=20, choices=RuleType.choices)
    keywords = models.JSONField('关键词列表', default=list, blank=True)
    match_mode = models.CharField('匹配模式', max_length=20, choices=MatchMode.choices, default=MatchMode.CONTAINS)
    conditions = models.JSONField('条件配置', default=dict, blank=True)
    reply_content = models.TextField('回复内容')
    reply_type = models.CharField('回复类型', max_length=20, default='text')  # text, image, template
    priority = models.IntegerField('优先级', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    usage_count = models.IntegerField('使用次数', default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_reply_rules')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'auto_reply_rules'
        verbose_name = '自动回复规则'
        verbose_name_plural = '自动回复规则'
        indexes = [
            models.Index(fields=['rule_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name} - {self.name}"


class MessageTemplate(models.Model):
    """消息模板"""
    
    class TemplateType(models.TextChoices):
        TEXT = 'text', '文本消息'
        IMAGE = 'image', '图片消息'
        LINK = 'link', '链接消息'
        CARD = 'card', '卡片消息'
        PRODUCT = 'product', '商品消息'
    
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name='message_templates')
    name = models.CharField('模板名称', max_length=100)
    template_type = models.CharField('模板类型', max_length=20, choices=TemplateType.choices)
    content = models.TextField('模板内容')
    variables = models.JSONField('变量定义', default=dict, blank=True)
    media_urls = models.JSONField('媒体链接', default=list, blank=True)
    category = models.CharField('分类', max_length=50, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    usage_count = models.IntegerField('使用次数', default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_templates')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'message_templates'
        verbose_name = '消息模板'
        verbose_name_plural = '消息模板'
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name} - {self.name}"


class PlatformWebhook(models.Model):
    """平台Webhook"""
    
    class WebhookStatus(models.TextChoices):
        ACTIVE = 'active', '正常'
        INACTIVE = 'inactive', '停用'
        ERROR = 'error', '异常'
    
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name='webhooks')
    webhook_url = models.URLField('Webhook URL')
    secret_token = models.CharField('密钥令牌', max_length=200, blank=True)
    events = models.JSONField('监听事件', default=list)
    status = models.CharField('状态', max_length=20, choices=WebhookStatus.choices, default=WebhookStatus.ACTIVE)
    last_received_at = models.DateTimeField('最后接收时间', blank=True, null=True)
    error_count = models.IntegerField('错误次数', default=0)
    last_error = models.TextField('最后错误', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'platform_webhooks'
        verbose_name = '平台Webhook'
        verbose_name_plural = '平台Webhook'
    
    def __str__(self):
        return f"{self.account.account_name} - Webhook"


class PlatformMessage(models.Model):
    """平台消息记录"""
    
    class MessageDirection(models.TextChoices):
        INBOUND = 'inbound', '接收'
        OUTBOUND = 'outbound', '发送'
    
    class MessageStatus(models.TextChoices):
        PENDING = 'pending', '待处理'
        PROCESSING = 'processing', '处理中'
        SENT = 'sent', '已发送'
        DELIVERED = 'delivered', '已送达'
        READ = 'read', '已读'
        FAILED = 'failed', '失败'
    
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name='messages')
    conversation_id = models.CharField('对话ID', max_length=100)
    message_id = models.CharField('消息ID', max_length=100)
    direction = models.CharField('方向', max_length=20, choices=MessageDirection.choices)
    message_type = models.CharField('消息类型', max_length=20, default='text')
    content = models.TextField('消息内容')
    media_urls = models.JSONField('媒体链接', default=list, blank=True)
    sender_id = models.CharField('发送者ID', max_length=100, blank=True)
    sender_name = models.CharField('发送者名称', max_length=100, blank=True)
    recipient_id = models.CharField('接收者ID', max_length=100, blank=True)
    recipient_name = models.CharField('接收者名称', max_length=100, blank=True)
    status = models.CharField('状态', max_length=20, choices=MessageStatus.choices, default=MessageStatus.PENDING)
    metadata = models.JSONField('元数据', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'platform_messages'
        verbose_name = '平台消息'
        verbose_name_plural = '平台消息'
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['message_id']),
            models.Index(fields=['direction']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name} - {self.message_id}" 