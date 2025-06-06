from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.login_view, name='login'),
    path('auth/captcha/', views.generate_captcha, name='captcha'),
    path('auth/user-info/', views.get_user_info, name='user-info'),
    # 注释掉不存在的view，避免导入错误
    # path('login/', views.LoginView.as_view(), name='login'),
    # path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('register/', views.RegisterView.as_view(), name='register'),
    # path('profile/', views.CurrentUserProfileView.as_view(), name='current-profile'),
] 