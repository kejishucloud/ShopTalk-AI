"""
平台插件注册器
==============

提供插件注册的装饰器和工具函数。
"""

import logging
from typing import Type, Callable
from .base import BasePlatformPlugin
from .factory import PlatformPluginFactory

logger = logging.getLogger(__name__)


def register_platform_plugin(platform_name: str):
    """
    平台插件注册装饰器
    
    Args:
        platform_name: 平台名称
        
    Returns:
        装饰器函数
    """
    def decorator(plugin_class: Type[BasePlatformPlugin]) -> Type[BasePlatformPlugin]:
        """
        装饰器函数
        
        Args:
            plugin_class: 插件类
            
        Returns:
            插件类
        """
        if not issubclass(plugin_class, BasePlatformPlugin):
            raise TypeError(f"插件类必须继承自 BasePlatformPlugin: {plugin_class}")
        
        PlatformPluginFactory.register_plugin(platform_name, plugin_class)
        logger.info(f"通过装饰器注册平台插件: {platform_name}")
        
        return plugin_class
    
    return decorator


def register_plugin_manually(platform_name: str, plugin_class: Type[BasePlatformPlugin]):
    """
    手动注册平台插件
    
    Args:
        platform_name: 平台名称
        plugin_class: 插件类
    """
    PlatformPluginFactory.register_plugin(platform_name, plugin_class)


def unregister_plugin(platform_name: str) -> bool:
    """
    注销平台插件
    
    Args:
        platform_name: 平台名称
        
    Returns:
        bool: 是否成功注销
    """
    return PlatformPluginFactory.remove_plugin(platform_name)


def get_registered_plugins() -> list:
    """
    获取所有已注册的插件
    
    Returns:
        list: 插件名称列表
    """
    return PlatformPluginFactory.list_plugins()


def is_plugin_registered(platform_name: str) -> bool:
    """
    检查插件是否已注册
    
    Args:
        platform_name: 平台名称
        
    Returns:
        bool: 是否已注册
    """
    return platform_name in PlatformPluginFactory.list_plugins() 