from django.apps import AppConfig


class SentimentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sentiment'
    verbose_name = '情感分析'
    
    def ready(self):
        """应用启动时的初始化"""
        pass 