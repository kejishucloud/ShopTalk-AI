"""
知识库管理URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    KnowledgeBaseViewSet, DocumentCategoryViewSet, DocumentTagViewSet,
    DocumentViewSet, FAQViewSet, ProductViewSet, ScriptViewSet,
    KnowledgeSearchView, BatchOperationView, KnowledgeAccessRecordViewSet,
    KnowledgeRecommendationViewSet
)

app_name = 'knowledge'

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'knowledge-bases', KnowledgeBaseViewSet, basename='knowledge-base')
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'tags', DocumentTagViewSet, basename='tag')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'scripts', ScriptViewSet, basename='script')
router.register(r'search', KnowledgeSearchView, basename='search')
router.register(r'batch-operations', BatchOperationView, basename='batch-operation')
router.register(r'access-records', KnowledgeAccessRecordViewSet, basename='access-record')
router.register(r'recommendations', KnowledgeRecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('api/v1/knowledge/', include(router.urls)),
] 