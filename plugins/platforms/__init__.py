"""
平台适配器插件模块
==================

支持的电商和社交平台：
- 淘宝 (Taobao)
- 京东 (JingDong)  
- 拼多多 (PinDuoDuo)
- 小红书 (XiaoHongShu)
- 抖音 (DouYin)
- 微信 (WeChat)
"""

from .base import BasePlatformPlugin
from .factory import PlatformPluginFactory
from .registry import register_platform_plugin

# 自动导入所有平台插件
from .taobao import TaobaoPlatformPlugin
from .jingdong import JingDongPlatformPlugin
from .pinduoduo import PinDuoDuoPlatformPlugin
from .xiaohongshu import XiaoHongShuPlatformPlugin
from .douyin import DouYinPlatformPlugin
from .wechat import WeChatPlatformPlugin

__all__ = [
    'BasePlatformPlugin',
    'PlatformPluginFactory',
    'register_platform_plugin',
    'TaobaoPlatformPlugin',
    'JingDongPlatformPlugin',
    'PinDuoDuoPlatformPlugin',
    'XiaoHongShuPlatformPlugin',
    'DouYinPlatformPlugin',
    'WeChatPlatformPlugin',
] 