"""
智能体API URL配置
"""

from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    # 核心智能体API
    path('chat/', views.chat_api, name='chat'),
    path('analyze/tags/', views.analyze_tags_api, name='analyze_tags'),
    path('analyze/sentiment/', views.analyze_sentiment_api, name='analyze_sentiment'),
    path('knowledge/query/', views.knowledge_query_api, name='knowledge_query'),
    
    # 智能体管理API
    path('status/', views.agent_status_api, name='agent_status'),
    path('control/', views.agent_control_api, name='agent_control'),
    path('pipeline/', views.agent_pipeline_api, name='agent_pipeline'),
    path('cleanup/', views.cleanup_agents_api, name='cleanup_agents'),
    
    # Webhook接口
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
    
    # 公开展示API
    path('capabilities/', views.agent_capabilities_api, name='capabilities'),
] 