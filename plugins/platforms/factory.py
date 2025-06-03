"""
平台插件工厂
============

负责创建和管理平台适配器插件实例。
"""

import logging
from typing import Dict, Type, Optional, List
from .base import BasePlatformPlugin, PlatformConfig

logger = logging.getLogger(__name__)


class PlatformPluginFactory:
    """平台插件工厂类"""
    
    _plugins: Dict[str, Type[BasePlatformPlugin]] = {}
    _instances: Dict[str, BasePlatformPlugin] = {}
    
    @classmethod
    def register_plugin(cls, platform_name: str, plugin_class: Type[BasePlatformPlugin]):
        """
        注册平台插件
        
        Args:
            platform_name: 平台名称
            plugin_class: 插件类
        """
        cls._plugins[platform_name] = plugin_class
        logger.info(f"注册平台插件: {platform_name} -> {plugin_class.__name__}")
    
    @classmethod
    def create_plugin(cls, platform_name: str, config: PlatformConfig) -> Optional[BasePlatformPlugin]:
        """
        创建平台插件实例
        
        Args:
            platform_name: 平台名称
            config: 平台配置
            
        Returns:
            BasePlatformPlugin: 插件实例
        """
        if platform_name not in cls._plugins:
            logger.error(f"未找到平台插件: {platform_name}")
            return None
        
        try:
            plugin_class = cls._plugins[platform_name]
            instance = plugin_class(config)
            cls._instances[platform_name] = instance
            logger.info(f"创建平台插件实例: {platform_name}")
            return instance
        except Exception as e:
            logger.error(f"创建平台插件失败: {platform_name} - {e}")
            return None
    
    @classmethod
    def get_plugin(cls, platform_name: str) -> Optional[BasePlatformPlugin]:
        """
        获取平台插件实例
        
        Args:
            platform_name: 平台名称
            
        Returns:
            BasePlatformPlugin: 插件实例
        """
        return cls._instances.get(platform_name)
    
    @classmethod
    def list_plugins(cls) -> List[str]:
        """
        列出所有已注册的插件
        
        Returns:
            List[str]: 插件名称列表
        """
        return list(cls._plugins.keys())
    
    @classmethod
    def remove_plugin(cls, platform_name: str) -> bool:
        """
        移除平台插件
        
        Args:
            platform_name: 平台名称
            
        Returns:
            bool: 是否成功移除
        """
        try:
            # 清理实例
            if platform_name in cls._instances:
                instance = cls._instances[platform_name]
                if hasattr(instance, 'cleanup'):
                    instance.cleanup()
                del cls._instances[platform_name]
            
            # 移除注册
            if platform_name in cls._plugins:
                del cls._plugins[platform_name]
            
            logger.info(f"移除平台插件: {platform_name}")
            return True
        except Exception as e:
            logger.error(f"移除平台插件失败: {platform_name} - {e}")
            return False
    
    @classmethod
    def cleanup_all(cls):
        """清理所有插件实例"""
        for platform_name in list(cls._instances.keys()):
            cls.remove_plugin(platform_name)
        logger.info("清理所有平台插件完成") 