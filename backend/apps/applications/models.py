"""
应用管理模块模型
对接多个应用（如微信公众号、小程序、Web端等）
统一管理接入参数、回调地址、鉴权规则
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator
import json


class Application(models.Model):
    """应用配置"""
    PLATFORM_CHOICES = [
        ('wechat', '微信公众号'),
        ('wechat_mini', '微信小程序'),
        ('xiaohongshu', '小红书'),
        ('taobao', '淘宝'),
        ('jingdong', '京东'),
        ('pinduoduo', '拼多多'),
        ('webchat', 'Web聊天'),
        ('app', '移动应用'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '激活'),
        ('inactive', '停用'),
        ('error', '错误'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='应用名称')
    description = models.TextField(blank=True, verbose_name='应用描述')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, verbose_name='平台类型')
    app_id = models.CharField(max_length=100, unique=True, verbose_name='应用ID')
    app_secret = models.CharField(max_length=200, verbose_name='应用密钥')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 时间字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    activated_at = models.DateTimeField(null=True, blank=True, verbose_name='激活时间')
    last_callback_at = models.DateTimeField(null=True, blank=True, verbose_name='最后回调时间')
    
    # 关联字段
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    
    class Meta:
        db_table = 'app_applications'
        verbose_name = '应用配置'
        verbose_name_plural = '应用配置'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"


class AppConfig(models.Model):
    """应用配置详情"""
    CONFIG_TYPE_CHOICES = [
        ('basic', '基础配置'),
        ('webhook', 'Webhook配置'),
        ('oauth', 'OAuth配置'),
        ('api', 'API配置'),
        ('custom', '自定义配置'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='configs', verbose_name='应用')
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES, verbose_name='配置类型')
    config_key = models.CharField(max_length=100, verbose_name='配置键')
    config_value = models.TextField(verbose_name='配置值')
    is_encrypted = models.BooleanField(default=False, verbose_name='是否加密')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'app_configs'
        verbose_name = '应用配置详情'
        verbose_name_plural = '应用配置详情'
        unique_together = ['app', 'config_key']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.app.name} - {self.config_key}"
    
    def get_config_value(self):
        """获取配置值（处理加密）"""
        if self.is_encrypted:
            # TODO: 实现解密逻辑
            return self.config_value
        return self.config_value
    
    def set_config_value(self, value, encrypt=False):
        """设置配置值（处理加密）"""
        if encrypt:
            # TODO: 实现加密逻辑
            self.config_value = value
            self.is_encrypted = True
        else:
            self.config_value = value
            self.is_encrypted = False


class AppCallback(models.Model):
    """应用回调记录"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('error', '错误'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='callbacks', verbose_name='应用')
    method = models.CharField(max_length=10, verbose_name='请求方法')
    headers = models.JSONField(default=dict, verbose_name='请求头')
    body = models.TextField(blank=True, verbose_name='请求体')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    
    # 处理结果
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    response_data = models.JSONField(null=True, blank=True, verbose_name='响应数据')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    
    class Meta:
        db_table = 'app_callbacks'
        verbose_name = '应用回调记录'
        verbose_name_plural = '应用回调记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.app.name} - {self.method} - {self.status}"


class AppAuth(models.Model):
    """应用认证配置"""
    AUTH_TYPE_CHOICES = [
        ('token', 'Token认证'),
        ('signature', '签名认证'),
        ('oauth2', 'OAuth2认证'),
        ('basic', 'Basic认证'),
        ('custom', '自定义认证'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='auth_configs', verbose_name='应用')
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE_CHOICES, verbose_name='认证类型')
    auth_key = models.CharField(max_length=100, verbose_name='认证键')
    auth_value = models.TextField(verbose_name='认证值')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 额外配置
    extra_config = models.JSONField(default=dict, blank=True, verbose_name='额外配置')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'app_auth'
        verbose_name = '应用认证配置'
        verbose_name_plural = '应用认证配置'
        unique_together = ['app', 'auth_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.app.name} - {self.get_auth_type_display()}"


class AppStatistics(models.Model):
    """应用统计数据"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='statistics', verbose_name='应用')
    date = models.DateField(verbose_name='统计日期')
    
    # 统计数据
    message_count = models.IntegerField(default=0, verbose_name='消息数量')
    session_count = models.IntegerField(default=0, verbose_name='会话数量')
    user_count = models.IntegerField(default=0, verbose_name='用户数量')
    error_count = models.IntegerField(default=0, verbose_name='错误数量')
    
    # 响应时间统计
    avg_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间(秒)')
    max_response_time = models.FloatField(default=0.0, verbose_name='最大响应时间(秒)')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'app_statistics'
        verbose_name = '应用统计数据'
        verbose_name_plural = '应用统计数据'
        unique_together = ['app', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.app.name} - {self.date}" 