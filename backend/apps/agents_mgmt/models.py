"""
智能体管理模块数据模型
支持多个智能体实例的管理和监控
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class AgentConfig(models.Model):
    """智能体配置"""
    name = models.CharField(max_length=100, verbose_name='配置名称')
    config_data = models.JSONField(default=dict, verbose_name='配置数据')
    description = models.TextField(blank=True, verbose_name='配置描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'agent_configs'
        verbose_name = '智能体配置'
        verbose_name_plural = '智能体配置'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Agent(models.Model):
    """智能体实例"""
    STATUS_CHOICES = [
        ('idle', '空闲'),
        ('running', '运行中'),
        ('stopping', '停止中'),
        ('stopped', '已停止'),
        ('error', '错误'),
    ]
    
    AGENT_TYPES = [
        ('tag_agent', '标签智能体'),
        ('sentiment_agent', '情感分析智能体'),
        ('keyword_agent', '关键词智能体'),
        ('custom_agent', '自定义智能体'),
    ]

    name = models.CharField(max_length=100, verbose_name='智能体名称')
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES, verbose_name='智能体类型')
    description = models.TextField(blank=True, verbose_name='智能体描述')
    config = models.ForeignKey(AgentConfig, on_delete=models.CASCADE, verbose_name='配置')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle', verbose_name='状态')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 运行时信息
    pid = models.IntegerField(null=True, blank=True, verbose_name='进程ID')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='启动时间')
    last_execution_at = models.DateTimeField(null=True, blank=True, verbose_name='最后执行时间')
    
    # 统计信息
    total_executions = models.IntegerField(default=0, verbose_name='总执行次数')
    successful_executions = models.IntegerField(default=0, verbose_name='成功执行次数')
    failed_executions = models.IntegerField(default=0, verbose_name='失败执行次数')
    
    # 管理信息
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'agents'
        verbose_name = '智能体'
        verbose_name_plural = '智能体'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_agent_type_display()})"
    
    @property
    def uptime(self):
        """运行时间"""
        if self.started_at and self.status == 'running':
            return timezone.now() - self.started_at
        return None
    
    @property
    def success_rate(self):
        """成功率"""
        if self.total_executions > 0:
            return self.successful_executions / self.total_executions
        return 0.0


class AgentExecution(models.Model):
    """智能体执行记录"""
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('timeout', '超时'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, verbose_name='智能体')
    execution_id = models.CharField(max_length=100, unique=True, verbose_name='执行ID')
    input_data = models.JSONField(default=dict, verbose_name='输入数据')
    output_data = models.JSONField(default=dict, verbose_name='输出数据')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间信息
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    duration = models.FloatField(null=True, blank=True, verbose_name='执行时长(秒)')

    class Meta:
        db_table = 'agent_executions'
        verbose_name = '智能体执行记录'
        verbose_name_plural = '智能体执行记录'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.agent.name} - {self.execution_id}"
    
    def save(self, *args, **kwargs):
        if not self.execution_id:
            import uuid
            self.execution_id = str(uuid.uuid4())
        
        # 计算执行时长
        if self.completed_at and self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
        
        super().save(*args, **kwargs)


class AgentLog(models.Model):
    """智能体日志"""
    LEVEL_CHOICES = [
        ('DEBUG', '调试'),
        ('INFO', '信息'),
        ('WARNING', '警告'),
        ('ERROR', '错误'),
        ('CRITICAL', '严重错误'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, verbose_name='智能体')
    execution = models.ForeignKey(
        AgentExecution, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='关联执行'
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name='日志级别')
    message = models.TextField(verbose_name='日志消息')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='额外数据')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'agent_logs'
        verbose_name = '智能体日志'
        verbose_name_plural = '智能体日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['level', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.level}] {self.agent.name}: {self.message[:50]}"


class AgentMetrics(models.Model):
    """智能体性能指标"""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, verbose_name='智能体')
    metrics_data = models.JSONField(default=dict, verbose_name='指标数据')
    
    # 系统资源指标
    cpu_usage = models.FloatField(default=0.0, verbose_name='CPU使用率')
    memory_usage = models.FloatField(default=0.0, verbose_name='内存使用率')
    
    # 业务指标
    requests_per_minute = models.IntegerField(default=0, verbose_name='每分钟请求数')
    average_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间')
    error_rate = models.FloatField(default=0.0, verbose_name='错误率')
    
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        db_table = 'agent_metrics'
        verbose_name = '智能体指标'
        verbose_name_plural = '智能体指标'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['agent', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.agent.name} - {self.recorded_at}" 