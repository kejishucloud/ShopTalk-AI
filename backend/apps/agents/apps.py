"""
智能体应用配置
"""

from django.apps import AppConfig


class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.agents'
    verbose_name = '智能体'
    
    def ready(self):
        """应用启动时初始化智能体"""
        from .services import initialize_agents
        initialize_agents() 