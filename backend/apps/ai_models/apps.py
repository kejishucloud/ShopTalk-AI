from django.apps import AppConfig


class AiModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_models'
    verbose_name = 'AI模型管理'
    
    def ready(self):
        """应用启动时执行的初始化操作"""
        pass 