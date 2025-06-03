"""
知识库API URL路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    KnowledgeBaseViewSet,
    ScriptViewSet,
    ProductViewSet,
    DocumentViewSet,
    FAQViewSet,
    DocumentCategoryViewSet,
    DocumentTagViewSet,
    KnowledgeSearchView,
    BatchImportView,
    KnowledgeSyncView
)

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'knowledge-bases', KnowledgeBaseViewSet, basename='knowledgebase')
router.register(r'scripts', ScriptViewSet, basename='script')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'tags', DocumentTagViewSet, basename='tag')
router.register(r'search', KnowledgeSearchView, basename='search')
router.register(r'import', BatchImportView, basename='import')
router.register(r'sync', KnowledgeSyncView, basename='sync')

# URL模式
urlpatterns = [
    path('api/v1/', include(router.urls)),
]

# 为方便使用，也可以直接暴露路由器的URLs
app_name = 'knowledge'
urlpatterns = router.urls 