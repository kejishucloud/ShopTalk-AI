"""
ASGI配置文件，支持HTTP和WebSocket协议
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 获取Django ASGI应用
django_asgi_app = get_asgi_application()

# ASGI应用配置
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "websocket": AuthMiddlewareStack(
    #     URLRouter([
    #         # WebSocket URL路由将在这里定义
    #     ])
    # ),
}) 