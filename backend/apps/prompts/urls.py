"""
提示词管理模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'prompts', views.PromptViewSet, basename='prompt')

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 