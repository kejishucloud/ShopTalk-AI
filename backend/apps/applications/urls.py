"""
应用管理模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'applications', views.ApplicationViewSet, basename='application')
router.register(r'configs', views.AppConfigViewSet, basename='app-config')
router.register(r'callbacks', views.AppCallbackViewSet, basename='app-callback')
router.register(r'auth', views.AppAuthViewSet, basename='app-auth')

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 