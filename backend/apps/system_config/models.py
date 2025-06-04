from django.db import models
from django.conf import settings
from django.core.validators import validate_email
import json


class ConfigCategory(models.Model):
    """配置分类"""
    name = models.CharField(max_length=100, unique=True, verbose_name='分类名称')
    display_name = models.CharField(max_length=100, verbose_name='显示名称')
    description = models.TextField(blank=True, verbose_name='描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'config_categories'
        verbose_name = '配置分类'
        verbose_name_plural = '配置分类'
        ordering = ['order', 'name']

    def __str__(self):
        return self.display_name


class SystemConfig(models.Model):
    """系统配置"""
    CONFIG_TYPES = [
        ('string', '字符串'),
        ('integer', '整数'),
        ('float', '浮点数'),
        ('boolean', '布尔值'),
        ('json', 'JSON'),
        ('password', '密码'),
        ('email', '邮箱'),
        ('url', 'URL'),
        ('text', '长文本'),
        ('choice', '选择'),
    ]

    category = models.ForeignKey(ConfigCategory, on_delete=models.CASCADE, verbose_name='配置分类')
    key = models.CharField(max_length=200, unique=True, verbose_name='配置键')
    display_name = models.CharField(max_length=200, verbose_name='显示名称')
    description = models.TextField(blank=True, verbose_name='描述')
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='string', verbose_name='配置类型')
    value = models.TextField(blank=True, verbose_name='配置值')
    default_value = models.TextField(blank=True, verbose_name='默认值')
    choices = models.JSONField(default=list, blank=True, verbose_name='选择项')
    is_required = models.BooleanField(default=False, verbose_name='是否必填')
    is_encrypted = models.BooleanField(default=False, verbose_name='是否加密')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='创建者')

    class Meta:
        db_table = 'system_configs'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        ordering = ['category__order', 'order', 'key']

    def __str__(self):
        return f"{self.category.display_name} - {self.display_name}"

    def get_value(self):
        """获取配置值，根据类型转换"""
        if not self.value:
            return self.get_default_value()
        
        try:
            if self.config_type == 'boolean':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == 'integer':
                return int(self.value)
            elif self.config_type == 'float':
                return float(self.value)
            elif self.config_type == 'json':
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.get_default_value()

    def get_default_value(self):
        """获取默认值"""
        if not self.default_value:
            return None
        
        try:
            if self.config_type == 'boolean':
                return self.default_value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == 'integer':
                return int(self.default_value)
            elif self.config_type == 'float':
                return float(self.default_value)
            elif self.config_type == 'json':
                return json.loads(self.default_value)
            else:
                return self.default_value
        except (ValueError, json.JSONDecodeError):
            return None

    def set_value(self, value):
        """设置配置值"""
        if self.config_type == 'json' and isinstance(value, (dict, list)):
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)
        self.save()


class ConfigGroup(models.Model):
    """配置组（用于界面分组显示）"""
    category = models.ForeignKey(ConfigCategory, on_delete=models.CASCADE, verbose_name='配置分类')
    name = models.CharField(max_length=100, verbose_name='组名')
    display_name = models.CharField(max_length=100, verbose_name='显示名称')
    description = models.TextField(blank=True, verbose_name='描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_collapsible = models.BooleanField(default=True, verbose_name='是否可折叠')
    is_expanded = models.BooleanField(default=True, verbose_name='默认展开')

    class Meta:
        db_table = 'config_groups'
        verbose_name = '配置组'
        verbose_name_plural = '配置组'
        ordering = ['category__order', 'order', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.category.display_name} - {self.display_name}"


# 将配置项关联到组
SystemConfig.add_to_class('group', models.ForeignKey(ConfigGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='配置组')) 