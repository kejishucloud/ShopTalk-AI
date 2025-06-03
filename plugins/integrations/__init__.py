"""第三方集成插件模块"""

class IntegrationPluginFactory:
    """集成插件工厂"""
    
    @classmethod
    def list_plugins(cls):
        return []

__all__ = ['IntegrationPluginFactory'] 