"""
标签管理模块数据模型
支持给用户、聊天历史、产品等打标签
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json


class TagCategory(models.Model):
    """标签分类"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='描述')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='显示颜色')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tag_categories'
        verbose_name = '标签分类'
        verbose_name_plural = '标签分类'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """标签定义"""
    name = models.CharField(max_length=100, verbose_name='标签名称')
    category = models.ForeignKey(TagCategory, on_delete=models.CASCADE, verbose_name='所属分类')
    description = models.TextField(blank=True, verbose_name='标签描述')
    color = models.CharField(max_length=7, default='#6c757d', verbose_name='显示颜色')
    is_system = models.BooleanField(default=False, verbose_name='是否系统标签')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tags'
        verbose_name = '标签'
        verbose_name_plural = '标签'
        unique_together = ['name', 'category']

    def __str__(self):
        return f"{self.category.name}/{self.name}"


class TagRule(models.Model):
    """标签规则配置"""
    RULE_TYPES = [
        ('keyword', '关键词匹配'),
        ('intent', '意图识别'),
        ('sentiment', '情感分析'),
        ('pattern', '正则表达式'),
    ]

    name = models.CharField(max_length=100, verbose_name='规则名称')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, verbose_name='规则类型')
    conditions = models.JSONField(default=dict, verbose_name='匹配条件')
    target_tags = models.ManyToManyField(Tag, verbose_name='目标标签')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tag_rules'
        verbose_name = '标签规则'
        verbose_name_plural = '标签规则'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"

    def match_text(self, text):
        """检查文本是否匹配此规则"""
        if not self.is_active:
            return False
        
        text = text.lower()
        conditions = self.conditions
        
        if self.rule_type == 'keyword':
            keywords = conditions.get('keywords', [])
            return any(keyword.lower() in text for keyword in keywords)
        
        elif self.rule_type == 'pattern':
            import re
            pattern = conditions.get('pattern', '')
            return bool(re.search(pattern, text, re.IGNORECASE))
        
        # 其他规则类型需要外部智能体处理
        return False


class TagAssignment(models.Model):
    """标签分配记录"""
    ASSIGNMENT_TYPES = [
        ('manual', '手动分配'),
        ('auto', '自动分配'),
        ('agent', '智能体分配'),
    ]

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='标签')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='对象类型')
    object_id = models.PositiveIntegerField(verbose_name='对象ID')
    content_object = GenericForeignKey('content_type', 'object_id')
    
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='manual', verbose_name='分配类型')
    confidence = models.FloatField(default=1.0, verbose_name='置信度')
    rule = models.ForeignKey(TagRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='触发规则')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='分配者')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='分配时间')

    class Meta:
        db_table = 'tag_assignments'
        verbose_name = '标签分配'
        verbose_name_plural = '标签分配'
        unique_together = ['tag', 'content_type', 'object_id']

    def __str__(self):
        return f"{self.tag.name} -> {self.content_type.model}({self.object_id})"


class TagStatistics(models.Model):
    """标签统计数据"""
    tag = models.OneToOneField(Tag, on_delete=models.CASCADE, verbose_name='标签')
    total_assignments = models.IntegerField(default=0, verbose_name='总分配次数')
    active_assignments = models.IntegerField(default=0, verbose_name='活跃分配数')
    last_assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='最后分配时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tag_statistics'
        verbose_name = '标签统计'
        verbose_name_plural = '标签统计'

    def __str__(self):
        return f"{self.tag.name} 统计" 