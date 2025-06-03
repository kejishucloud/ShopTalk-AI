"""
平台适配器基础类
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    LINK = "link"
    PRODUCT = "product"
    SYSTEM = "system"


class MessageDirection(Enum):
    """消息方向"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass
class PlatformMessage:
    """平台消息"""
    message_id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    recipient_id: str
    recipient_name: str
    message_type: MessageType
    content: str
    direction: MessageDirection
    timestamp: float
    media_urls: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.media_urls is None:
            self.media_urls = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PlatformAccount:
    """平台账号信息"""
    account_id: str
    account_name: str
    platform_type: str
    credentials: Dict[str, Any]
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}


class BasePlatformAdapter(ABC):
    """平台适配器基础类"""
    
    def __init__(self, account: PlatformAccount):
        """
        初始化平台适配器
        
        Args:
            account: 平台账号信息
        """
        self.account = account
        self.is_connected = False
        self.message_handlers: List[Callable] = []
        self.error_handlers: List[Callable] = []
        
        logger.info(f"初始化 {self.platform_name} 适配器: {account.account_name}")
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称"""
        pass
    
    @property
    @abstractmethod
    def supported_message_types(self) -> List[MessageType]:
        """支持的消息类型"""
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
    async def send_message(self, message: PlatformMessage) -> bool:
        """
        发送消息
        
        Args:
            message: 要发送的消息
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    async def get_conversations(self, limit: int = 50) -> List[Dict]:
        """
        获取对话列表
        
        Args:
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 对话列表
        """
        pass
    
    @abstractmethod
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[PlatformMessage]:
        """
        获取对话消息
        
        Args:
            conversation_id: 对话ID
            limit: 获取数量限制
            
        Returns:
            List[PlatformMessage]: 消息列表
        """
        pass
    
    @abstractmethod
    async def mark_message_read(self, message_id: str) -> bool:
        """
        标记消息为已读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 操作是否成功
        """
        pass
    
    def add_message_handler(self, handler: Callable[[PlatformMessage], None]):
        """
        添加消息处理器
        
        Args:
            handler: 消息处理函数
        """
        self.message_handlers.append(handler)
        logger.debug(f"添加消息处理器: {handler.__name__}")
    
    def add_error_handler(self, handler: Callable[[Exception], None]):
        """
        添加错误处理器
        
        Args:
            handler: 错误处理函数
        """
        self.error_handlers.append(handler)
        logger.debug(f"添加错误处理器: {handler.__name__}")
    
    async def _handle_message(self, message: PlatformMessage):
        """
        处理接收到的消息
        
        Args:
            message: 接收到的消息
        """
        logger.debug(f"处理消息: {message.message_id}")
        
        for handler in self.message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"消息处理器执行失败: {str(e)}", exc_info=True)
                await self._handle_error(e)
    
    async def _handle_error(self, error: Exception):
        """
        处理错误
        
        Args:
            error: 错误对象
        """
        logger.error(f"平台适配器错误: {str(error)}")
        
        for handler in self.error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    handler(error)
            except Exception as e:
                logger.error(f"错误处理器执行失败: {str(e)}", exc_info=True)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {
            'platform': self.platform_name,
            'account': self.account.account_name,
            'connected': self.is_connected,
            'supported_types': [t.value for t in self.supported_message_types]
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账号信息
        
        Returns:
            Dict[str, Any]: 账号信息
        """
        return {
            'account_id': self.account.account_id,
            'account_name': self.account.account_name,
            'platform_type': self.account.platform_type,
            'settings': self.account.settings
        }


class EcommercePlatformAdapter(BasePlatformAdapter):
    """电商平台适配器基础类"""
    
    @abstractmethod
    async def get_product_info(self, product_id: str) -> Optional[Dict]:
        """
        获取商品信息
        
        Args:
            product_id: 商品ID
            
        Returns:
            Optional[Dict]: 商品信息
        """
        pass
    
    @abstractmethod
    async def get_order_info(self, order_id: str) -> Optional[Dict]:
        """
        获取订单信息
        
        Args:
            order_id: 订单ID
            
        Returns:
            Optional[Dict]: 订单信息
        """
        pass
    
    @abstractmethod
    async def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """
        搜索商品
        
        Args:
            query: 搜索关键词
            limit: 结果数量限制
            
        Returns:
            List[Dict]: 商品列表
        """
        pass
    
    @abstractmethod
    async def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """
        获取客户订单列表
        
        Args:
            customer_id: 客户ID
            
        Returns:
            List[Dict]: 订单列表
        """
        pass


class SocialPlatformAdapter(BasePlatformAdapter):
    """社交平台适配器基础类"""
    
    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict]: 用户资料
        """
        pass
    
    @abstractmethod
    async def get_followers_count(self, user_id: str) -> int:
        """
        获取粉丝数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 粉丝数量
        """
        pass
    
    @abstractmethod
    async def post_content(self, content: str, media_urls: List[str] = None) -> bool:
        """
        发布内容
        
        Args:
            content: 内容文本
            media_urls: 媒体文件URL列表
            
        Returns:
            bool: 发布是否成功
        """
        pass 