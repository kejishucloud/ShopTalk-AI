"""
智能客服管理模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'configs', views.ChatbotConfigViewSet, basename='chatbot-config')
router.register(r'sessions', views.ChatSessionViewSet, basename='chat-session')
router.register(r'handoffs', views.HumanHandoffViewSet, basename='human-handoff')
router.register(r'statistics', views.ChatStatisticsViewSet, basename='chat-statistics')
router.register(r'performance', views.AgentPerformanceViewSet, basename='agent-performance')

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 