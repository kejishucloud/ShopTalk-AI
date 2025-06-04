"""
AI模型管理数据模型
支持多种AI模型的配置、调用记录、性能监控
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from decimal import Decimal


class AIModelProvider(models.Model):
    """AI模型提供商"""
    PROVIDER_TYPES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('azure', 'Azure OpenAI'),
        ('google', 'Google AI'),
        ('baidu', '百度千帆'),
        ('alibaba', '阿里云通义千问'),
        ('tencent', '腾讯混元'),
        ('local', '本地部署'),
        ('custom', '自定义API'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='提供商名称')
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES, verbose_name='提供商类型')
    description = models.TextField(blank=True, verbose_name='描述')
    base_url = models.URLField(blank=True, verbose_name='基础API地址')
    api_version = models.CharField(max_length=20, blank=True, verbose_name='API版本')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ai_model_providers'
        verbose_name = 'AI模型提供商'
        verbose_name_plural = 'AI模型提供商'

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class AIModel(models.Model):
    """AI模型配置"""
    MODEL_TYPES = [
        ('chat', '对话模型'),
        ('completion', '文本生成'),
        ('embedding', '向量化模型'),
        ('image', '图像生成'),
        ('audio', '语音处理'),
        ('multimodal', '多模态'),
    ]
    
    CAPABILITY_CHOICES = [
        ('text_generation', '文本生成'),
        ('conversation', '对话'),
        ('code_generation', '代码生成'),
        ('translation', '翻译'),
        ('summarization', '摘要'),
        ('sentiment_analysis', '情感分析'),
        ('question_answering', '问答'),
        ('embedding', '向量化'),
        ('image_generation', '图像生成'),
        ('speech_to_text', '语音转文字'),
        ('text_to_speech', '文字转语音'),
    ]
    
    provider = models.ForeignKey(AIModelProvider, on_delete=models.CASCADE, verbose_name='提供商')
    name = models.CharField(max_length=100, verbose_name='模型名称')
    model_id = models.CharField(max_length=200, verbose_name='模型ID')
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, verbose_name='模型类型')
    capabilities = models.JSONField(default=list, verbose_name='支持能力')
    
    # 模型参数配置
    max_tokens = models.IntegerField(default=4096, verbose_name='最大Token数')
    context_window = models.IntegerField(default=4096, verbose_name='上下文窗口')
    default_temperature = models.FloatField(
        default=0.7, 
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        verbose_name='默认温度参数'
    )
    default_top_p = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='默认Top-p参数'
    )
    
    # 定价信息
    input_price_per_1k = models.DecimalField(
        max_digits=10, decimal_places=6, default=0,
        verbose_name='输入Token价格/1K'
    )
    output_price_per_1k = models.DecimalField(
        max_digits=10, decimal_places=6, default=0,
        verbose_name='输出Token价格/1K'
    )
    
    # 状态和配置
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    api_key = models.TextField(blank=True, verbose_name='API密钥')
    additional_config = models.JSONField(default=dict, verbose_name='额外配置')
    
    # 限制配置
    rate_limit_rpm = models.IntegerField(default=60, verbose_name='每分钟请求限制')
    rate_limit_tpm = models.IntegerField(default=40000, verbose_name='每分钟Token限制')
    daily_quota = models.IntegerField(default=0, verbose_name='每日配额(0=无限制)')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ai_models'
        verbose_name = 'AI模型'
        verbose_name_plural = 'AI模型'
        unique_together = ['provider', 'model_id']
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.provider.name}/{self.name}"

    def get_capabilities_display(self):
        """获取能力列表的显示文本"""
        capability_dict = dict(self.CAPABILITY_CHOICES)
        return [capability_dict.get(cap, cap) for cap in self.capabilities]

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """计算调用成本"""
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost


class ModelCallRecord(models.Model):
    """模型调用记录"""
    CALL_STATUS = [
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
        ('rate_limited', '限流'),
        ('quota_exceeded', '配额超限'),
    ]
    
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, verbose_name='使用模型')
    session_id = models.CharField(max_length=100, blank=True, verbose_name='会话ID')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='调用用户')
    
    # 请求参数
    input_text = models.TextField(verbose_name='输入文本')
    parameters = models.JSONField(default=dict, verbose_name='调用参数')
    
    # 响应数据
    output_text = models.TextField(blank=True, verbose_name='输出文本')
    status = models.CharField(max_length=20, choices=CALL_STATUS, verbose_name='调用状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 性能指标
    input_tokens = models.IntegerField(default=0, verbose_name='输入Token数')
    output_tokens = models.IntegerField(default=0, verbose_name='输出Token数')
    total_tokens = models.IntegerField(default=0, verbose_name='总Token数')
    response_time = models.FloatField(default=0.0, verbose_name='响应时间(秒)')
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0, verbose_name='调用成本')
    
    # 元数据
    request_id = models.CharField(max_length=100, blank=True, verbose_name='请求ID')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='调用时间')

    class Meta:
        db_table = 'model_call_records'
        verbose_name = '模型调用记录'
        verbose_name_plural = '模型调用记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"{self.model.name} - {self.get_status_display()} - {self.created_at}"

    def save(self, *args, **kwargs):
        # 自动计算总Token数和成本
        self.total_tokens = self.input_tokens + self.output_tokens
        if self.status == 'success':
            self.cost = self.model.calculate_cost(self.input_tokens, self.output_tokens)
        super().save(*args, **kwargs)


class ModelPerformance(models.Model):
    """模型性能统计"""
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, verbose_name='模型')
    date = models.DateField(verbose_name='统计日期')
    
    # 调用统计
    total_calls = models.IntegerField(default=0, verbose_name='总调用次数')
    successful_calls = models.IntegerField(default=0, verbose_name='成功调用次数')
    failed_calls = models.IntegerField(default=0, verbose_name='失败调用次数')
    
    # Token统计
    total_input_tokens = models.BigIntegerField(default=0, verbose_name='总输入Token')
    total_output_tokens = models.BigIntegerField(default=0, verbose_name='总输出Token')
    total_tokens = models.BigIntegerField(default=0, verbose_name='总Token数')
    
    # 性能指标
    average_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间')
    success_rate = models.FloatField(default=0.0, verbose_name='成功率')
    
    # 成本统计
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0, verbose_name='总成本')
    average_cost_per_call = models.DecimalField(max_digits=10, decimal_places=6, default=0, verbose_name='平均每次调用成本')
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'model_performance'
        verbose_name = '模型性能统计'
        verbose_name_plural = '模型性能统计'
        unique_together = ['model', 'date']
        ordering = ['-date', 'model']

    def __str__(self):
        return f"{self.model.name} - {self.date}"

    def calculate_metrics(self):
        """计算性能指标"""
        if self.total_calls > 0:
            self.success_rate = (self.successful_calls / self.total_calls) * 100
            self.average_cost_per_call = self.total_cost / self.total_calls
        else:
            self.success_rate = 0.0
            self.average_cost_per_call = 0


class ModelLoadBalancer(models.Model):
    """模型负载均衡配置"""
    BALANCE_STRATEGIES = [
        ('round_robin', '轮询'),
        ('weighted', '加权轮询'),
        ('random', '随机'),
        ('least_connections', '最少连接'),
        ('response_time', '响应时间优先'),
        ('cost_optimized', '成本优化'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='负载均衡名称')
    strategy = models.CharField(max_length=20, choices=BALANCE_STRATEGIES, default='round_robin', verbose_name='均衡策略')
    ai_models = models.ManyToManyField(AIModel, through='ModelWeight', verbose_name='参与模型')
    
    # 故障转移配置
    enable_fallback = models.BooleanField(default=True, verbose_name='启用故障转移')
    max_retries = models.IntegerField(default=3, verbose_name='最大重试次数')
    retry_delay = models.IntegerField(default=1, verbose_name='重试延迟(秒)')
    
    # 健康检查
    health_check_enabled = models.BooleanField(default=True, verbose_name='启用健康检查')
    health_check_interval = models.IntegerField(default=60, verbose_name='健康检查间隔(秒)')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'model_load_balancers'
        verbose_name = '模型负载均衡'
        verbose_name_plural = '模型负载均衡'

    def __str__(self):
        return f"{self.name} ({self.get_strategy_display()})"


class ModelWeight(models.Model):
    """模型权重配置"""
    load_balancer = models.ForeignKey(ModelLoadBalancer, on_delete=models.CASCADE, verbose_name='负载均衡器')
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, verbose_name='模型')
    weight = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='权重')
    is_healthy = models.BooleanField(default=True, verbose_name='健康状态')
    last_health_check = models.DateTimeField(null=True, blank=True, verbose_name='最后健康检查时间')

    class Meta:
        db_table = 'model_weights'
        verbose_name = '模型权重'
        verbose_name_plural = '模型权重'
        unique_together = ['load_balancer', 'model']

    def __str__(self):
        return f"{self.load_balancer.name} - {self.model.name} (权重: {self.weight})"


class ModelQuota(models.Model):
    """模型配额管理"""
    QUOTA_TYPES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('total', '总计'),
    ]
    
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, verbose_name='模型')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='用户')
    quota_type = models.CharField(max_length=10, choices=QUOTA_TYPES, verbose_name='配额类型')
    
    # 配额限制
    max_calls = models.IntegerField(default=0, verbose_name='最大调用次数')
    max_tokens = models.BigIntegerField(default=0, verbose_name='最大Token数')
    max_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='最大成本')
    
    # 当前使用量
    used_calls = models.IntegerField(default=0, verbose_name='已使用调用次数')
    used_tokens = models.BigIntegerField(default=0, verbose_name='已使用Token数')
    used_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='已使用成本')
    
    # 重置时间
    reset_at = models.DateTimeField(verbose_name='重置时间')
    last_reset = models.DateTimeField(auto_now_add=True, verbose_name='上次重置时间')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'model_quotas'
        verbose_name = '模型配额'
        verbose_name_plural = '模型配额'
        unique_together = ['model', 'user', 'quota_type']

    def __str__(self):
        user_part = f" - {self.user.username}" if self.user else ""
        return f"{self.model.name}{user_part} ({self.get_quota_type_display()})"

    def is_exceeded(self) -> bool:
        """检查是否超出配额"""
        if self.max_calls > 0 and self.used_calls >= self.max_calls:
            return True
        if self.max_tokens > 0 and self.used_tokens >= self.max_tokens:
            return True
        if self.max_cost > 0 and self.used_cost >= self.max_cost:
            return True
        return False

    def get_usage_percentage(self) -> dict:
        """获取使用率百分比"""
        return {
            'calls': (self.used_calls / self.max_calls * 100) if self.max_calls > 0 else 0,
            'tokens': (self.used_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            'cost': (float(self.used_cost) / float(self.max_cost) * 100) if self.max_cost > 0 else 0,
        } 