"""
智能客服聊天机器人数据模型
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class ChatbotConfig(models.Model):
    """聊天机器人配置"""
    PLATFORM_CHOICES = [
        ('web', '网页'),
        ('wechat', '微信'),
        ('qq', 'QQ'),
        ('weibo', '微博'),
        ('xiaohongshu', '小红书'),
        ('taobao', '淘宝'),
        ('api', 'API接口'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='配置名称')
    description = models.TextField(blank=True, verbose_name='配置描述')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, verbose_name='平台')
    
    # 消息配置
    welcome_message = models.TextField(verbose_name='欢迎消息')
    default_response = models.TextField(verbose_name='默认回复')
    max_session_duration = models.IntegerField(
        default=3600, 
        validators=[MinValueValidator(60), MaxValueValidator(86400)],
        verbose_name='最大会话时长(秒)'
    )
    
    # 智能体配置
    primary_agent = models.ForeignKey(
        'agents_mgmt.Agent', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='primary_configs',
        verbose_name='主要智能体'
    )
    fallback_agent = models.ForeignKey(
        'agents_mgmt.Agent', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='fallback_configs',
        verbose_name='后备智能体'
    )
    
    # 人工转接配置
    auto_handoff_enabled = models.BooleanField(default=False, verbose_name='启用自动转人工')
    handoff_keywords = models.JSONField(default=list, verbose_name='转人工关键词')
    handoff_threshold = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='转人工置信度阈值'
    )
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 管理信息
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'chatbot_configs'
        verbose_name = '聊天机器人配置'
        verbose_name_plural = '聊天机器人配置'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"


class ChatSession(models.Model):
    """聊天会话"""
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('waiting_human', '等待人工'),
        ('human_handling', '人工处理中'),
        ('completed', '已完成'),
        ('timeout', '超时'),
        ('error', '错误'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    platform = models.CharField(max_length=20, verbose_name='平台')
    app_name = models.CharField(max_length=100, verbose_name='应用名称')
    platform_user_id = models.CharField(max_length=200, verbose_name='平台用户ID')
    
    # 关联信息
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='用户')
    config = models.ForeignKey(ChatbotConfig, on_delete=models.SET_NULL, null=True, verbose_name='配置')
    assigned_agent = models.ForeignKey(
        'agents_mgmt.Agent', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='分配的智能体'
    )
    
    # 会话状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    message_count = models.IntegerField(default=0, verbose_name='消息数量')
    last_message_at = models.DateTimeField(null=True, blank=True, verbose_name='最后消息时间')
    
    # 会话数据
    session_data = models.JSONField(default=dict, verbose_name='会话数据')
    user_info = models.JSONField(default=dict, verbose_name='用户信息')
    
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    class Meta:
        db_table = 'chat_sessions'
        verbose_name = '聊天会话'
        verbose_name_plural = '聊天会话'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['platform', 'platform_user_id']),
            models.Index(fields=['status', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.platform}:{self.platform_user_id} - {self.status}"
    
    def is_active(self):
        """检查会话是否活跃"""
        return self.status in ['active', 'waiting_human', 'human_handling']


class HumanHandoff(models.Model):
    """人工接入请求"""
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('assigned', '已分配'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    TRIGGER_REASON_CHOICES = [
        ('user_request', '用户请求'),
        ('keyword_trigger', '关键词触发'),
        ('confidence_low', '置信度过低'),
        ('agent_error', '智能体错误'),
        ('timeout', '响应超时'),
        ('manual', '手动转接'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, verbose_name='会话')
    
    # 触发信息
    trigger_reason = models.CharField(max_length=20, choices=TRIGGER_REASON_CHOICES, verbose_name='触发原因')
    trigger_message = models.TextField(blank=True, verbose_name='触发消息')
    trigger_context = models.JSONField(default=dict, verbose_name='触发上下文')
    
    # 处理状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    
    # 分配信息
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='triggered_handoffs',
        verbose_name='触发者'
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_handoffs',
        verbose_name='分配的客服'
    )
    
    # 处理结果
    resolution_notes = models.TextField(blank=True, verbose_name='处理记录')
    customer_satisfaction = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='客户满意度'
    )
    
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='分配时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始处理时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        db_table = 'human_handoffs'
        verbose_name = '人工接入'
        verbose_name_plural = '人工接入'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority', '-created_at']),
            models.Index(fields=['assigned_agent', '-created_at']),
        ]

    def __str__(self):
        return f"转人工-{self.session} ({self.get_status_display()})"
    
    def waiting_time(self):
        """等待时间（秒）"""
        if self.assigned_at:
            return (self.assigned_at - self.created_at).total_seconds()
        elif self.status == 'pending':
            return (timezone.now() - self.created_at).total_seconds()
        return 0
    
    def handling_time(self):
        """处理时间（秒）"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.status == 'in_progress' and self.started_at:
            return (timezone.now() - self.started_at).total_seconds()
        return 0


class ChatStatistics(models.Model):
    """聊天统计数据"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(verbose_name='统计日期')
    platform = models.CharField(max_length=20, verbose_name='平台')
    
    # 会话统计
    total_sessions = models.IntegerField(default=0, verbose_name='总会话数')
    active_sessions = models.IntegerField(default=0, verbose_name='活跃会话数')
    completed_sessions = models.IntegerField(default=0, verbose_name='完成会话数')
    
    # 消息统计
    total_messages = models.IntegerField(default=0, verbose_name='总消息数')
    bot_messages = models.IntegerField(default=0, verbose_name='机器人消息数')
    user_messages = models.IntegerField(default=0, verbose_name='用户消息数')
    human_messages = models.IntegerField(default=0, verbose_name='人工消息数')
    
    # 人工接入统计
    handoff_requests = models.IntegerField(default=0, verbose_name='转人工请求数')
    handoff_completed = models.IntegerField(default=0, verbose_name='转人工完成数')
    avg_handoff_wait_time = models.FloatField(default=0.0, verbose_name='平均等待时间(秒)')
    avg_handoff_handle_time = models.FloatField(default=0.0, verbose_name='平均处理时间(秒)')
    
    # 满意度统计
    satisfaction_ratings = models.JSONField(default=dict, verbose_name='满意度评分分布')
    avg_satisfaction = models.FloatField(default=0.0, verbose_name='平均满意度')
    
    # 性能统计
    bot_success_rate = models.FloatField(default=0.0, verbose_name='机器人成功率')
    avg_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间(毫秒)')
    
    # 管理信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'chat_statistics'
        verbose_name = '聊天统计'
        verbose_name_plural = '聊天统计'
        ordering = ['-date']
        unique_together = ['date', 'platform']

    def __str__(self):
        return f"{self.date} - {self.platform}"


class AgentPerformance(models.Model):
    """智能体性能监控"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey('agents_mgmt.Agent', on_delete=models.CASCADE, verbose_name='智能体')
    date = models.DateField(verbose_name='统计日期')
    
    # 请求统计
    total_requests = models.IntegerField(default=0, verbose_name='总请求数')
    successful_requests = models.IntegerField(default=0, verbose_name='成功请求数')
    failed_requests = models.IntegerField(default=0, verbose_name='失败请求数')
    
    # 响应时间统计
    avg_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间(毫秒)')
    max_response_time = models.FloatField(default=0.0, verbose_name='最大响应时间(毫秒)')
    min_response_time = models.FloatField(default=0.0, verbose_name='最小响应时间(毫秒)')
    
    # 准确性统计
    accuracy_score = models.FloatField(default=0.0, verbose_name='准确性得分')
    confidence_avg = models.FloatField(default=0.0, verbose_name='平均置信度')
    
    # 资源使用统计
    cpu_usage_avg = models.FloatField(default=0.0, verbose_name='平均CPU使用率')
    memory_usage_avg = models.FloatField(default=0.0, verbose_name='平均内存使用率')
    
    # 错误统计
    timeout_count = models.IntegerField(default=0, verbose_name='超时次数')
    error_count = models.IntegerField(default=0, verbose_name='错误次数')
    
    # 管理信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'agent_performance'
        verbose_name = '智能体性能'
        verbose_name_plural = '智能体性能'
        ordering = ['-date', '-total_requests']
        unique_together = ['agent', 'date']

    def __str__(self):
        return f"{self.agent.name} - {self.date}"
    
    def success_rate(self):
        """成功率"""
        if self.total_requests > 0:
            return (self.successful_requests / self.total_requests) * 100
        return 0.0
    
    def error_rate(self):
        """错误率"""
        if self.total_requests > 0:
            return (self.failed_requests / self.total_requests) * 100
        return 0.0 