"""
关键词管理模块数据模型
"""

from django.db import models
from django.conf import settings
import uuid


class KeywordCategory(models.Model):
    """关键词分类"""
    CATEGORY_TYPE_CHOICES = [
        ('handoff', '转人工'),
        ('sentiment', '情感分析'),
        ('product', '产品相关'),
        ('service', '服务相关'),
        ('complaint', '投诉相关'),
        ('praise', '表扬相关'),
        ('question', '问题相关'),
        ('other', '其他'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='分类描述')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, verbose_name='分类类型')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 管理信息
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'keyword_categories'
        verbose_name = '关键词分类'
        verbose_name_plural = '关键词分类'
        ordering = ['priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class KeywordMatch(models.Model):
    """关键词匹配记录"""
    MATCH_TYPE_CHOICES = [
        ('exact', '精确匹配'),
        ('fuzzy', '模糊匹配'),
        ('regex', '正则匹配'),
        ('semantic', '语义匹配'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keyword = models.CharField(max_length=200, verbose_name='关键词')
    matched_text = models.TextField(verbose_name='匹配文本')
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES, verbose_name='匹配类型')
    confidence = models.FloatField(default=1.0, verbose_name='匹配置信度')
    
    # 关联信息
    session = models.ForeignKey(
        'chatbot.ChatSession', 
        on_delete=models.CASCADE, 
        verbose_name='会话',
        null=True,
        blank=True
    )
    message = models.ForeignKey(
        'history.ChatMessage', 
        on_delete=models.CASCADE, 
        verbose_name='消息',
        null=True,
        blank=True
    )
    matched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='匹配用户')
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    matched_at = models.DateTimeField(auto_now_add=True, verbose_name='匹配时间')

    class Meta:
        db_table = 'keyword_matches'
        verbose_name = '关键词匹配'
        verbose_name_plural = '关键词匹配'
        ordering = ['-matched_at']
        indexes = [
            models.Index(fields=['keyword', '-matched_at']),
            models.Index(fields=['match_type', '-matched_at']),
        ]

    def __str__(self):
        return f"关键词匹配: {self.keyword} -> {self.matched_text[:50]}..."


class Keyword(models.Model):
    """关键词定义"""
    KEYWORD_TYPE_CHOICES = [
        ('handoff', '转人工'),
        ('sentiment', '情感分析'),
        ('product', '产品相关'),
        ('service', '服务相关'),
        ('complaint', '投诉相关'),
        ('praise', '表扬相关'),
        ('question', '问题相关'),
        ('other', '其他'),
    ]
    
    PRIORITY_LEVEL_CHOICES = [
        (1, '最低'),
        (3, '低'),
        (5, '中等'),
        (8, '高'),
        (10, '最高'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=200, verbose_name='关键词')
    category = models.ForeignKey(KeywordCategory, on_delete=models.CASCADE, verbose_name='分类')
    keyword_type = models.CharField(max_length=20, choices=KEYWORD_TYPE_CHOICES, verbose_name='关键词类型')
    description = models.TextField(blank=True, verbose_name='描述')
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签')
    
    # 匹配配置
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    match_type = models.CharField(max_length=20, choices=KeywordMatch.MATCH_TYPE_CHOICES, default='exact', verbose_name='匹配类型')
    weight = models.FloatField(default=1.0, verbose_name='权重')
    priority_level = models.IntegerField(choices=PRIORITY_LEVEL_CHOICES, default=5, verbose_name='优先级')
    
    # 响应配置
    auto_response = models.TextField(blank=True, verbose_name='自动回复')
    trigger_handoff = models.BooleanField(default=False, verbose_name='触发转人工')
    
    # 管理信息
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'keywords'
        verbose_name = '关键词'
        verbose_name_plural = '关键词'
        ordering = ['-priority_level', '-weight', '-created_at']
        unique_together = ['word', 'category']

    def __str__(self):
        return f"{self.word} ({self.get_keyword_type_display()})"


class KeywordRule(models.Model):
    """关键词规则"""
    RULE_TYPE_CHOICES = [
        ('single', '单关键词'),
        ('combination', '组合关键词'),
        ('sequence', '序列关键词'),
        ('context', '上下文关键词'),
    ]
    
    TRIGGER_ACTION_CHOICES = [
        ('handoff', '转人工'),
        ('auto_reply', '自动回复'),
        ('escalate', '升级处理'),
        ('tag', '添加标签'),
        ('notify', '通知管理员'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='规则名称')
    description = models.TextField(blank=True, verbose_name='规则描述')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, verbose_name='规则类型')
    
    # 规则配置
    keywords = models.ManyToManyField(Keyword, verbose_name='关键词')
    condition_logic = models.CharField(max_length=10, choices=[('AND', '且'), ('OR', '或')], default='OR', verbose_name='条件逻辑')
    threshold = models.FloatField(default=0.5, verbose_name='触发阈值')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    
    # 触发动作
    trigger_action = models.CharField(max_length=20, choices=TRIGGER_ACTION_CHOICES, verbose_name='触发动作')
    action_config = models.JSONField(default=dict, verbose_name='动作配置')
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 管理信息
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'keyword_rules'
        verbose_name = '关键词规则'
        verbose_name_plural = '关键词规则'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class KeywordStatistics(models.Model):
    """关键词统计"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE, verbose_name='关键词')
    date = models.DateField(verbose_name='统计日期')
    
    # 统计数据
    total_matches = models.IntegerField(default=0, verbose_name='总匹配次数')
    unique_users = models.IntegerField(default=0, verbose_name='独立用户数')
    handoff_triggered = models.IntegerField(default=0, verbose_name='触发转人工次数')
    auto_replies = models.IntegerField(default=0, verbose_name='自动回复次数')
    
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'keyword_statistics'
        verbose_name = '关键词统计'
        verbose_name_plural = '关键词统计'
        unique_together = ['keyword', 'date']
        ordering = ['-date', '-total_matches']

    def __str__(self):
        return f"{self.keyword.word} - {self.date} ({self.total_matches}次)" 