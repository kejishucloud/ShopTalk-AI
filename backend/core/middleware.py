import logging
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """请求日志中间件"""
    
    def process_request(self, request):
        logger.info(f"Request: {request.method} {request.get_full_path()}")
        return None


class AgentStatusMiddleware(MiddlewareMixin):
    """智能体状态中间件"""
    
    def process_request(self, request):
        # TODO: 实现智能体状态检查逻辑
        return None 