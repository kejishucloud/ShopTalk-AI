"""
知识库API URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    KnowledgeBaseViewSet,
    ScriptViewSet,
    ProductViewSet,
    DocumentCategoryViewSet,
    DocumentTagViewSet
)

# 创建API路由器
router = DefaultRouter()

# 注册视图集
router.register(r'knowledge-bases', KnowledgeBaseViewSet, basename='knowledgebase')
router.register(r'scripts', ScriptViewSet, basename='script')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'tags', DocumentTagViewSet, basename='tag')

# URL模式
urlpatterns = [
    path('api/v1/', include(router.urls)),
]

app_name = 'knowledge_api' 