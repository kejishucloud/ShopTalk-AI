"""
智能体管理模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'agents', views.AgentViewSet, basename='agent')
router.register(r'configs', views.AgentConfigViewSet, basename='agent-config')
router.register(r'executions', views.AgentExecutionViewSet, basename='agent-execution')
router.register(r'logs', views.AgentLogViewSet, basename='agent-log')

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 