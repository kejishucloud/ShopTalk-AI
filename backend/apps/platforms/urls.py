from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlatformViewSet, PlatformAccountViewSet, PlatformConfigurationViewSet

router = DefaultRouter()
router.register(r'platforms', PlatformViewSet)
router.register(r'accounts', PlatformAccountViewSet)
router.register(r'configurations', PlatformConfigurationViewSet)

app_name = 'platforms'

urlpatterns = [
    path('', include(router.urls)),
] 