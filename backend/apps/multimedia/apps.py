from django.apps import AppConfig


class MultimediaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.multimedia'
    verbose_name = '多媒体处理'
    
    def ready(self):
        """应用启动时的初始化"""
        pass 