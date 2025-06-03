"""
AI模型管理URL路由配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIModelProviderViewSet, AIModelViewSet, ModelCallRecordViewSet,
    ModelPerformanceViewSet, ModelLoadBalancerViewSet, ModelQuotaViewSet
)

router = DefaultRouter()
router.register(r'providers', AIModelProviderViewSet, basename='aimodel-providers')
router.register(r'models', AIModelViewSet, basename='aimodels')
router.register(r'call-records', ModelCallRecordViewSet, basename='model-call-records')
router.register(r'performance', ModelPerformanceViewSet, basename='model-performance')
router.register(r'load-balancers', ModelLoadBalancerViewSet, basename='model-load-balancers')
router.register(r'quotas', ModelQuotaViewSet, basename='model-quotas')

app_name = 'ai_models'

urlpatterns = [
    path('', include(router.urls)),
] 