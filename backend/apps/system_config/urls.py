from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfigCategoryViewSet, SystemConfigViewSet, ConfigGroupViewSet

router = DefaultRouter()
router.register(r'categories', ConfigCategoryViewSet)
router.register(r'configs', SystemConfigViewSet)
router.register(r'groups', ConfigGroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 