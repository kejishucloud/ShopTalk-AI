"""
ShopTalk-AI主URL配置
定义所有API路由和管理后台访问
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# 主路由配置
urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    
    # API文档
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API路由
    path('api/v1/', include([
        # 用户管理模块
        path('users/', include('apps.users.urls')),
        
        # 标签管理模块
        path('tags/', include('apps.tags.urls')),
        
        # 提示词管理模块
        path('prompts/', include('apps.prompts.urls')),
        
        # 智能体管理模块
        path('agents/', include('apps.agents_mgmt.urls')),
        
        # 话术管理模块
        path('knowledge/', include('apps.knowledge.urls')),
        
        # 智能客服管理模块
        path('chatbot/', include('apps.chatbot.urls')),
        
        # 不同应用管理模块
        path('applications/', include('apps.applications.urls')),
        
        # 关键词管理模块
        path('keywords/', include('apps.keywords.urls')),
        
        # 历史聊天记录管理模块
        path('history/', include('apps.history.urls')),
        
        # AI模型管理模块
        path('ai-models/', include('apps.ai_models.urls')),
        
        # 系统配置管理模块
        path('system-config/', include('apps.system_config.urls')),
    ])),
]

# 静态文件和媒体文件服务（开发环境）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 自定义管理后台配置
admin.site.site_header = 'ShopTalk-AI 智能客服管理后台'
admin.site.site_title = 'ShopTalk-AI'
admin.site.index_title = '系统管理' 