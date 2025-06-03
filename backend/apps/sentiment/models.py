from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SentimentAnalysis(models.Model):
    """情感分析结果模型"""
    
    SENTIMENT_CHOICES = [
        ('positive', '积极'),
        ('negative', '消极'),
        ('neutral', '中性'),
    ]
    
    MODEL_CHOICES = [
        ('transformer', 'Transformer模型'),
        ('baidu', '百度情感分析'),
        ('tencent', '腾讯情感分析'),
        ('openai', 'OpenAI'),
        ('local', '本地模型'),
    ]
    
    text = models.TextField(verbose_name='分析文本')
    sentiment = models.CharField(
        max_length=20, 
        choices=SENTIMENT_CHOICES,
        verbose_name='情感倾向'
    )
    confidence = models.FloatField(verbose_name='置信度')
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_CHOICES,
        verbose_name='使用模型'
    )
    
    # 详细分析结果
    positive_score = models.FloatField(default=0.0, verbose_name='积极分数')
    negative_score = models.FloatField(default=0.0, verbose_name='消极分数')
    neutral_score = models.FloatField(default=0.0, verbose_name='中性分数')
    
    # 关联信息
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='用户'
    )
    platform = models.CharField(max_length=50, blank=True, verbose_name='平台')
    conversation_id = models.CharField(max_length=100, blank=True, verbose_name='对话ID')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '情感分析'
        verbose_name_plural = '情感分析'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sentiment', 'created_at']),
            models.Index(fields=['platform', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.text[:50]}... - {self.get_sentiment_display()}'


class EmotionKeyword(models.Model):
    """情感关键词模型"""
    
    keyword = models.CharField(max_length=100, unique=True, verbose_name='关键词')
    sentiment = models.CharField(
        max_length=20,
        choices=SentimentAnalysis.SENTIMENT_CHOICES,
        verbose_name='情感倾向'
    )
    weight = models.FloatField(default=1.0, verbose_name='权重')
    category = models.CharField(max_length=50, blank=True, verbose_name='分类')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '情感关键词'
        verbose_name_plural = '情感关键词'
        ordering = ['keyword']
    
    def __str__(self):
        return f'{self.keyword} - {self.get_sentiment_display()}'


class SentimentReport(models.Model):
    """情感分析报告模型"""
    
    PERIOD_CHOICES = [
        ('daily', '日报'),
        ('weekly', '周报'),
        ('monthly', '月报'),
    ]
    
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        verbose_name='报告周期'
    )
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    
    # 统计数据
    total_analyses = models.IntegerField(default=0, verbose_name='总分析数')
    positive_count = models.IntegerField(default=0, verbose_name='积极数量')
    negative_count = models.IntegerField(default=0, verbose_name='消极数量')
    neutral_count = models.IntegerField(default=0, verbose_name='中性数量')
    
    positive_ratio = models.FloatField(default=0.0, verbose_name='积极比例')
    negative_ratio = models.FloatField(default=0.0, verbose_name='消极比例')
    neutral_ratio = models.FloatField(default=0.0, verbose_name='中性比例')
    
    # 平台统计
    platform_stats = models.JSONField(default=dict, verbose_name='平台统计')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '情感分析报告'
        verbose_name_plural = '情感分析报告'
        ordering = ['-start_date']
        unique_together = ['period_type', 'start_date', 'end_date']
    
    def __str__(self):
        return f'{self.get_period_type_display()} - {self.start_date} 到 {self.end_date}' 