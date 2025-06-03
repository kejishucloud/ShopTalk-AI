"""
平台适配器插件基类
==================

定义了所有平台适配器插件的基础接口和通用功能。
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """平台类型枚举"""
    ECOMMERCE = "ecommerce"  # 电商平台
    SOCIAL = "social"        # 社交平台
    MESSAGING = "messaging"   # 消息平台
    OTHER = "other"          # 其他


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    LINK = "link"
    LOCATION = "location"
    CONTACT = "contact"


@dataclass
class PlatformConfig:
    """平台配置数据类"""
    platform_name: str
    enabled: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    headless: bool = True
    user_data_dir: Optional[str] = None
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    anti_detection: bool = True
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}


@dataclass
class Message:
    """消息数据类"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: str
    timestamp: int
    platform: str
    extra_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


@dataclass
class User:
    """用户数据类"""
    id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None
    platform: str = ""
    extra_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


class BasePlatformPlugin(ABC):
    """平台适配器插件基类"""
    
    def __init__(self, config: PlatformConfig):
        """
        初始化平台适配器插件
        
        Args:
            config: 平台配置对象
        """
        self.config = config
        self.platform_name = config.platform_name
        self.logger = logging.getLogger(f"{__name__}.{self.platform_name}")
        self.is_initialized = False
        self.is_connected = False
        
    @property
    @abstractmethod
    def platform_type(self) -> PlatformType:
        """平台类型"""
        pass
    
    @property
    @abstractmethod
    def supported_message_types(self) -> List[MessageType]:
        """支持的消息类型"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化插件
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到平台
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开平台连接
        
        Returns:
            bool: 断开是否成功
        """
        pass
    
    @abstractmethod
    async def is_logged_in(self) -> bool:
        """
        检查是否已登录
        
        Returns:
            bool: 是否已登录
        """
        pass
    
    @abstractmethod
    async def send_message(self, user_id: str, message: str, 
                          message_type: MessageType = MessageType.TEXT,
                          **kwargs) -> bool:
        """
        发送消息
        
        Args:
            user_id: 接收用户ID
            message: 消息内容
            message_type: 消息类型
            **kwargs: 其他参数
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    async def get_messages(self, user_id: Optional[str] = None,
                          limit: int = 50) -> List[Message]:
        """
        获取消息列表
        
        Args:
            user_id: 用户ID，为None时获取所有消息
            limit: 消息数量限制
            
        Returns:
            List[Message]: 消息列表
        """
        pass
    
    @abstractmethod
    async def get_users(self, limit: int = 100) -> List[User]:
        """
        获取用户列表
        
        Args:
            limit: 用户数量限制
            
        Returns:
            List[User]: 用户列表
        """
        pass
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.disconnect()
            self.logger.info(f"{self.platform_name} 插件清理完成")
        except Exception as e:
            self.logger.error(f"{self.platform_name} 插件清理失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取插件状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            'platform_name': self.platform_name,
            'platform_type': self.platform_type.value,
            'is_initialized': self.is_initialized,
            'is_connected': self.is_connected,
            'config_enabled': self.config.enabled,
        }
    
    def validate_config(self) -> bool:
        """
        验证配置
        
        Returns:
            bool: 配置是否有效
        """
        if not self.config.enabled:
            return False
            
        # 子类可以重写此方法添加特定的验证逻辑
        return True
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.platform_name})"
    
    def __repr__(self):
        return self.__str__() 