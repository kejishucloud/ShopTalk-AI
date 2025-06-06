#!/usr/bin/env python
"""
创建管理员测试账号脚本
使用方法：python manage.py shell < create_admin_user.py
"""

import os
import sys
import django

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import UserProfile

User = get_user_model()

def create_admin_user():
    """创建管理员用户"""
    username = 'kejishu'
    password = 'kejishu'
    email = 'admin@kejishu.com'
    
    # 检查用户是否已存在
    if User.objects.filter(username=username).exists():
        print(f"用户 {username} 已存在")
        user = User.objects.get(username=username)
        
        # 更新密码和权限
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        print(f"已更新用户 {username} 的密码和权限")
    else:
        # 创建新用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f"已创建管理员用户: {username}")
    
    # 创建或更新用户资料
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'nickname': '科技树管理员',
            'phone': '13800138000',
        }
    )
    
    if not created:
        profile.nickname = '科技树管理员'
        profile.phone = '13800138000'
        profile.save()
        print("已更新用户资料")
    else:
        print("已创建用户资料")
    
    print(f"""
===========================================
管理员账号创建成功！
用户名: {username}
密码: {password}
邮箱: {email}
权限: 超级管理员
===========================================
    """)

if __name__ == '__main__':
    create_admin_user() 