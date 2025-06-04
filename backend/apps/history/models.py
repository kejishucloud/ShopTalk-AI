from django.db import models
from django.conf import settings
import uuid


class ChatHistory(models.Model):
    """聊天历史记录模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户', null=True, blank=True)
    session_id = models.CharField(max_length=100, verbose_name='会话ID')
    message = models.TextField(verbose_name='消息内容')
    response = models.TextField(verbose_name='回复内容')
    is_user_message = models.BooleanField(default=True, verbose_name='是否为用户消息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'chat_history'
        verbose_name = '聊天历史'
        verbose_name_plural = '聊天历史'
        ordering = ['-created_at']

    def __str__(self):
        return f"会话{self.session_id} - {self.created_at}"


class ChatMessage(models.Model):
    """聊天消息模型"""
    MESSAGE_TYPE_CHOICES = [
        ('user', '用户消息'),
        ('bot', '机器人消息'),
        ('human', '人工消息'),
        ('system', '系统消息'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        'chatbot.ChatSession', 
        on_delete=models.CASCADE, 
        verbose_name='会话',
        related_name='messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, verbose_name='消息类型')
    content = models.TextField(verbose_name='消息内容')
    
    # 发送者信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='发送用户'
    )
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'chat_messages'
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['message_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..." 