from django.db import models
from django.conf import settings


class Prompt(models.Model):
    """提示词模型"""
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    category = models.CharField(max_length=100, verbose_name='分类', blank=True)
    tags = models.CharField(max_length=200, verbose_name='标签', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'prompts'
        verbose_name = '提示词'
        verbose_name_plural = '提示词'
        ordering = ['-created_at']

    def __str__(self):
        return self.title 