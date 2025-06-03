from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型"""
    
    class UserType(models.TextChoices):
        ADMIN = 'admin', '管理员'
        OPERATOR = 'operator', '操作员'
        VIEWER = 'viewer', '查看者'
    
    phone = models.CharField('手机号', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True)
    user_type = models.CharField(
        '用户类型', 
        max_length=20, 
        choices=UserType.choices, 
        default=UserType.OPERATOR
    )
    company = models.CharField('公司名称', max_length=100, blank=True)
    department = models.CharField('部门', max_length=50, blank=True)
    is_active = models.BooleanField('是否激活', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class UserProfile(models.Model):
    """用户配置文件"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    timezone = models.CharField('时区', max_length=50, default='Asia/Shanghai')
    language = models.CharField('语言', max_length=10, default='zh-hans')
    notification_email = models.BooleanField('邮件通知', default=True)
    notification_sms = models.BooleanField('短信通知', default=False)
    auto_reply_enabled = models.BooleanField('自动回复启用', default=True)
    max_concurrent_conversations = models.IntegerField('最大并发对话数', default=10)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'
    
    def __str__(self):
        return f"{self.user.username}的配置" 