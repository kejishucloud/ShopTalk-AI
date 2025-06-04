"""
关键词管理模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'categories', views.KeywordCategoryViewSet, basename='keyword-category')
router.register(r'keywords', views.KeywordViewSet, basename='keyword')
router.register(r'rules', views.KeywordRuleViewSet, basename='keyword-rule')
router.register(r'matches', views.KeywordMatchViewSet, basename='keyword-match')
router.register(r'statistics', views.KeywordStatisticsViewSet, basename='keyword-statistics')

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 