from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'conversations', views.ConversationViewSet)
# router.register(r'messages', views.MessageViewSet)

app_name = 'history'

urlpatterns = [
    path('', include(router.urls)),
    # 临时路由，直接返回成功状态
    path('test/', views.test_view, name='test'),
] 