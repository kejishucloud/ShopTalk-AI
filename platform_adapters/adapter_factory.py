"""
平台适配器工厂
"""
import logging
from typing import Dict, Type, Optional, Any
from .base import BasePlatformAdapter, PlatformAccount
from .taobao import TaobaoAdapter
from .xiaohongshu import XiaohongshuAdapter
from .pinduoduo import PinduoduoAdapter
from .jingdong import JingdongAdapter
from .douyin import DouyinAdapter

logger = logging.getLogger(__name__)


class PlatformAdapterFactory:
    """平台适配器工厂"""

    # 注册的适配器类
    _adapters: Dict[str, Type[BasePlatformAdapter]] = {
        'taobao': TaobaoAdapter,
        'xiaohongshu': XiaohongshuAdapter,
        'pinduoduo': PinduoduoAdapter,
        'jingdong': JingdongAdapter,
        'douyin': DouyinAdapter,
    }

    # 活跃的适配器实例
    _active_adapters: Dict[str, BasePlatformAdapter] = {}

    @classmethod
    def register_adapter(cls, platform_type: str, adapter_class: Type[BasePlatformAdapter]):
        """
        注册新的适配器类
        
        Args:
            platform_type: 平台类型
            adapter_class: 适配器类
        """
        cls._adapters[platform_type] = adapter_class
        logger.info(f"注册平台适配器: {platform_type} -> {adapter_class.__name__}")

    @classmethod
    def get_supported_platforms(cls) -> list:
        """获取支持的平台列表"""
        return list(cls._adapters.keys())

    @classmethod
    def create_adapter(cls, account: PlatformAccount) -> Optional[BasePlatformAdapter]:
        """
        创建平台适配器实例
        
        Args:
            account: 平台账号信息
            
        Returns:
            BasePlatformAdapter: 适配器实例
        """
        platform_type = account.platform_type.lower()

        if platform_type not in cls._adapters:
            logger.error(f"不支持的平台类型: {platform_type}")
            return None

        try:
            adapter_class = cls._adapters[platform_type]
            adapter = adapter_class(account)

            # 缓存适配器实例
            adapter_key = f"{platform_type}_{account.account_id}"
            cls._active_adapters[adapter_key] = adapter

            logger.info(f"创建平台适配器: {platform_type} - {account.account_name}")
            return adapter

        except Exception as e:
            logger.error(f"创建平台适配器失败: {str(e)}", exc_info=True)
            return None

    @classmethod
    def get_adapter(cls, platform_type: str, account_id: str) -> Optional[BasePlatformAdapter]:
        """
        获取已创建的适配器实例
        
        Args:
            platform_type: 平台类型
            account_id: 账号ID
            
        Returns:
            BasePlatformAdapter: 适配器实例
        """
        adapter_key = f"{platform_type.lower()}_{account_id}"
        return cls._active_adapters.get(adapter_key)

    @classmethod
    async def connect_adapter(cls, account: PlatformAccount) -> Optional[BasePlatformAdapter]:
        """
        创建并连接适配器
        
        Args:
            account: 平台账号信息
            
        Returns:
            BasePlatformAdapter: 已连接的适配器实例
        """
        adapter = cls.create_adapter(account)
        if not adapter:
            return None

        try:
            success = await adapter.connect()
            if success:
                logger.info(f"平台适配器连接成功: {account.platform_type} - {account.account_name}")
                return adapter
            else:
                logger.error(f"平台适配器连接失败: {account.platform_type} - {account.account_name}")
                await cls.remove_adapter(account.platform_type, account.account_id)
                return None

        except Exception as e:
            logger.error(f"连接平台适配器时发生异常: {str(e)}", exc_info=True)
            await cls.remove_adapter(account.platform_type, account.account_id)
            return None

    @classmethod
    async def disconnect_adapter(cls, platform_type: str, account_id: str) -> bool:
        """
        断开并移除适配器
        
        Args:
            platform_type: 平台类型
            account_id: 账号ID
            
        Returns:
            bool: 是否成功断开
        """
        adapter = cls.get_adapter(platform_type, account_id)
        if not adapter:
            return True

        try:
            success = await adapter.disconnect()
            await cls.remove_adapter(platform_type, account_id)
            return success

        except Exception as e:
            logger.error(f"断开平台适配器时发生异常: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def remove_adapter(cls, platform_type: str, account_id: str):
        """
        移除适配器实例
        
        Args:
            platform_type: 平台类型
            account_id: 账号ID
        """
        adapter_key = f"{platform_type.lower()}_{account_id}"
        if adapter_key in cls._active_adapters:
            del cls._active_adapters[adapter_key]
            logger.info(f"移除平台适配器: {adapter_key}")

    @classmethod
    def get_active_adapters(cls) -> Dict[str, BasePlatformAdapter]:
        """获取所有活跃的适配器"""
        return cls._active_adapters.copy()

    @classmethod
    async def disconnect_all(cls):
        """断开所有适配器连接"""
        adapters = list(cls._active_adapters.items())

        for adapter_key, adapter in adapters:
            try:
                await adapter.disconnect()
                logger.info(f"断开适配器连接: {adapter_key}")
            except Exception as e:
                logger.error(f"断开适配器连接失败: {adapter_key} - {str(e)}")

        cls._active_adapters.clear()
        logger.info("所有平台适配器已断开连接")

    @classmethod
    async def health_check_all(cls) -> Dict[str, Dict[str, Any]]:
        """检查所有适配器的健康状态"""
        health_status = {}

        for adapter_key, adapter in cls._active_adapters.items():
            try:
                status = await adapter.health_check()
                health_status[adapter_key] = status
            except Exception as e:
                health_status[adapter_key] = {
                    'platform': adapter.platform_name,
                    'connected': False,
                    'error': str(e)
                }

        return health_status

    @classmethod
    def get_adapter_info(cls, platform_type: str) -> Optional[Dict[str, Any]]:
        """
        获取适配器信息
        
        Args:
            platform_type: 平台类型
            
        Returns:
            Dict: 适配器信息
        """
        platform_type = platform_type.lower()

        if platform_type not in cls._adapters:
            return None

        adapter_class = cls._adapters[platform_type]

        # 创建临时实例获取信息
        try:
            temp_account = PlatformAccount(
                account_id="temp",
                account_name="temp",
                platform_type=platform_type,
                credentials={}
            )
            temp_adapter = adapter_class(temp_account)

            return {
                'platform_name': temp_adapter.platform_name,
                'supported_message_types': [t.value for t in temp_adapter.supported_message_types],
                'class_name': adapter_class.__name__,
                'module': adapter_class.__module__
            }
        except Exception as e:
            logger.error(f"获取适配器信息失败: {platform_type} - {str(e)}")
            return None


class AdapterManager:
    """适配器管理器"""

    def __init__(self):
        self.factory = PlatformAdapterFactory()
        self.message_handlers = []
        self.error_handlers = []

    def add_message_handler(self, handler):
        """添加全局消息处理器"""
        self.message_handlers.append(handler)

    def add_error_handler(self, handler):
        """添加全局错误处理器"""
        self.error_handlers.append(handler)

    async def setup_adapter(self, account: PlatformAccount) -> Optional[BasePlatformAdapter]:
        """
        设置适配器（创建、连接、配置处理器）
        
        Args:
            account: 平台账号信息
            
        Returns:
            BasePlatformAdapter: 配置完成的适配器实例
        """
        adapter = await self.factory.connect_adapter(account)
        if not adapter:
            return None

        # 添加消息处理器
        for handler in self.message_handlers:
            adapter.add_message_handler(handler)

        # 添加错误处理器
        for handler in self.error_handlers:
            adapter.add_error_handler(handler)

        return adapter

    async def teardown_adapter(self, platform_type: str, account_id: str) -> bool:
        """
        拆除适配器
        
        Args:
            platform_type: 平台类型
            account_id: 账号ID
            
        Returns:
            bool: 是否成功拆除
        """
        return await self.factory.disconnect_adapter(platform_type, account_id)

    def get_supported_platforms(self) -> list:
        """获取支持的平台列表"""
        return self.factory.get_supported_platforms()

    def get_platform_info(self, platform_type: str) -> Optional[Dict[str, Any]]:
        """获取平台信息"""
        return self.factory.get_adapter_info(platform_type)

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        health_status = await self.factory.health_check_all()

        return {
            'supported_platforms': self.get_supported_platforms(),
            'active_adapters': len(self.factory.get_active_adapters()),
            'health_status': health_status,
            'message_handlers': len(self.message_handlers),
            'error_handlers': len(self.error_handlers)
        }


# 全局适配器管理器实例
adapter_manager = AdapterManager()
