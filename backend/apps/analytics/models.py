from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ConversationMetrics(models.Model):
    """对话指标模型"""
    
    date = models.DateField(verbose_name='日期')
    platform = models.CharField(max_length=50, verbose_name='平台')
    
    # 对话统计
    total_conversations = models.IntegerField(default=0, verbose_name='总对话数')
    active_conversations = models.IntegerField(default=0, verbose_name='活跃对话数')
    completed_conversations = models.IntegerField(default=0, verbose_name='完成对话数')
    
    # 消息统计
    total_messages = models.IntegerField(default=0, verbose_name='总消息数')
    user_messages = models.IntegerField(default=0, verbose_name='用户消息数')
    bot_messages = models.IntegerField(default=0, verbose_name='机器人消息数')
    
    # 响应时间统计
    avg_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间(秒)')
    max_response_time = models.FloatField(default=0.0, verbose_name='最大响应时间(秒)')
    min_response_time = models.FloatField(default=0.0, verbose_name='最小响应时间(秒)')
    
    # 满意度统计
    satisfaction_score = models.FloatField(default=0.0, verbose_name='满意度评分')
    satisfaction_count = models.IntegerField(default=0, verbose_name='评分数量')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '对话指标'
        verbose_name_plural = '对话指标'
        unique_together = ['date', 'platform']
        ordering = ['-date']
    
    def __str__(self):
        return f'{self.platform} - {self.date}'


class UserBehaviorAnalytics(models.Model):
    """用户行为分析模型"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    date = models.DateField(verbose_name='日期')
    platform = models.CharField(max_length=50, verbose_name='平台')
    
    # 活动统计
    session_count = models.IntegerField(default=0, verbose_name='会话次数')
    total_duration = models.IntegerField(default=0, verbose_name='总时长(秒)')
    message_count = models.IntegerField(default=0, verbose_name='消息数量')
    
    # 行为特征
    most_active_hour = models.IntegerField(default=0, verbose_name='最活跃小时')
    preferred_features = models.JSONField(default=list, verbose_name='偏好功能')
    interaction_patterns = models.JSONField(default=dict, verbose_name='交互模式')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '用户行为分析'
        verbose_name_plural = '用户行为分析'
        unique_together = ['user', 'date', 'platform']
        ordering = ['-date']
    
    def __str__(self):
        return f'{self.user.username} - {self.platform} - {self.date}'


class SystemPerformance(models.Model):
    """系统性能监控模型"""
    
    timestamp = models.DateTimeField(verbose_name='时间戳')
    
    # 系统资源
    cpu_usage = models.FloatField(verbose_name='CPU使用率(%)')
    memory_usage = models.FloatField(verbose_name='内存使用率(%)')
    disk_usage = models.FloatField(verbose_name='磁盘使用率(%)')
    
    # 网络统计
    network_in = models.BigIntegerField(default=0, verbose_name='网络入流量(字节)')
    network_out = models.BigIntegerField(default=0, verbose_name='网络出流量(字节)')
    
    # 应用性能
    active_connections = models.IntegerField(default=0, verbose_name='活跃连接数')
    request_count = models.IntegerField(default=0, verbose_name='请求数量')
    error_count = models.IntegerField(default=0, verbose_name='错误数量')
    
    # 数据库性能
    db_query_count = models.IntegerField(default=0, verbose_name='数据库查询数')
    db_avg_query_time = models.FloatField(default=0.0, verbose_name='平均查询时间(ms)')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '系统性能'
        verbose_name_plural = '系统性能'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'系统性能 - {self.timestamp}' 