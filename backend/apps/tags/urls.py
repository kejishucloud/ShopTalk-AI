"""
标签管理模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'categories', views.TagCategoryViewSet, basename='tag-category')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'rules', views.TagRuleViewSet, basename='tag-rule')
router.register(r'assignments', views.TagAssignmentViewSet, basename='tag-assignment')
router.register(r'statistics', views.TagStatisticsViewSet, basename='tag-statistics')

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 