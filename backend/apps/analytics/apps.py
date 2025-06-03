from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = '数据分析'
    
    def ready(self):
        """应用启动时的初始化"""
        pass 