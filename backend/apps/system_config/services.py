from typing import Any, Optional, Dict, List
from django.core.cache import cache
from django.conf import settings
from .models import SystemConfig
import logging

logger = logging.getLogger(__name__)


class ConfigService:
    """系统配置服务类"""
    
    CACHE_PREFIX = 'system_config:'
    CACHE_TIMEOUT = 300  # 5分钟缓存
    
    @classmethod
    def get_config(cls, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            use_cache: 是否使用缓存
            
        Returns:
            配置值
        """
        cache_key = f"{cls.CACHE_PREFIX}{key}"
        
        # 尝试从缓存获取
        if use_cache:
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
        
        try:
            config = SystemConfig.objects.get(key=key, is_active=True)
            value = config.get_value()
            
            # 如果值为None，使用默认值
            if value is None:
                value = default
            
            # 缓存结果
            if use_cache:
                cache.set(cache_key, value, cls.CACHE_TIMEOUT)
            
            return value
            
        except SystemConfig.DoesNotExist:
            logger.warning(f"配置项 {key} 不存在，使用默认值: {default}")
            return default
        except Exception as e:
            logger.error(f"获取配置项 {key} 失败: {e}")
            return default
    
    @classmethod
    def set_config(cls, key: str, value: Any, clear_cache: bool = True) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            clear_cache: 是否清除缓存
            
        Returns:
            是否设置成功
        """
        try:
            config = SystemConfig.objects.get(key=key, is_active=True)
            config.set_value(value)
            
            # 清除缓存
            if clear_cache:
                cache_key = f"{cls.CACHE_PREFIX}{key}"
                cache.delete(cache_key)
            
            logger.info(f"配置项 {key} 已更新为: {value}")
            return True
            
        except SystemConfig.DoesNotExist:
            logger.error(f"配置项 {key} 不存在")
            return False
        except Exception as e:
            logger.error(f"设置配置项 {key} 失败: {e}")
            return False
    
    @classmethod
    def get_configs_by_category(cls, category_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        根据分类获取所有配置
        
        Args:
            category_name: 分类名称
            use_cache: 是否使用缓存
            
        Returns:
            配置字典
        """
        cache_key = f"{cls.CACHE_PREFIX}category:{category_name}"
        
        # 尝试从缓存获取
        if use_cache:
            cached_configs = cache.get(cache_key)
            if cached_configs is not None:
                return cached_configs
        
        try:
            configs = SystemConfig.objects.filter(
                category__name=category_name,
                is_active=True
            ).select_related('category')
            
            result = {}
            for config in configs:
                result[config.key] = config.get_value()
            
            # 缓存结果
            if use_cache:
                cache.set(cache_key, result, cls.CACHE_TIMEOUT)
            
            return result
            
        except Exception as e:
            logger.error(f"获取分类 {category_name} 的配置失败: {e}")
            return {}
    
    @classmethod
    def batch_set_configs(cls, configs: Dict[str, Any], clear_cache: bool = True) -> Dict[str, bool]:
        """
        批量设置配置
        
        Args:
            configs: 配置字典 {key: value}
            clear_cache: 是否清除缓存
            
        Returns:
            设置结果字典 {key: success}
        """
        results = {}
        
        for key, value in configs.items():
            results[key] = cls.set_config(key, value, clear_cache=False)
        
        # 统一清除缓存
        if clear_cache:
            cls.clear_cache()
        
        return results
    
    @classmethod
    def clear_cache(cls, key: Optional[str] = None):
        """
        清除配置缓存
        
        Args:
            key: 特定配置键，如果为None则清除所有配置缓存
        """
        if key:
            cache_key = f"{cls.CACHE_PREFIX}{key}"
            cache.delete(cache_key)
        else:
            # 清除所有配置缓存
            cache.delete_many([
                f"{cls.CACHE_PREFIX}*"
            ])
    
    @classmethod
    def get_ai_model_config(cls, model_provider: str) -> Dict[str, Any]:
        """
        获取AI模型配置
        
        Args:
            model_provider: 模型提供商 (openai, anthropic, zhipu, etc.)
            
        Returns:
            模型配置字典
        """
        config_keys = {
            'openai': ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL'],
            'anthropic': ['ANTHROPIC_API_KEY', 'ANTHROPIC_MODEL'],
            'zhipu': ['ZHIPU_API_KEY', 'ZHIPU_MODEL'],
            'qwen': ['QWEN_API_KEY', 'QWEN_MODEL'],
            'ernie': ['ERNIE_API_KEY', 'ERNIE_SECRET_KEY'],
            'local_ai': ['LOCAL_AI_ENABLED', 'LOCAL_AI_URL']
        }
        
        keys = config_keys.get(model_provider, [])
        result = {}
        
        for key in keys:
            result[key] = cls.get_config(key)
        
        return result
    
    @classmethod
    def get_platform_config(cls, platform_name: str) -> Dict[str, Any]:
        """
        获取平台配置
        
        Args:
            platform_name: 平台名称 (taobao, jingdong, etc.)
            
        Returns:
            平台配置字典
        """
        config_keys = {
            'taobao': ['TAOBAO_ENABLED', 'TAOBAO_USERNAME', 'TAOBAO_PASSWORD'],
            'jingdong': ['JINGDONG_ENABLED', 'JINGDONG_USERNAME', 'JINGDONG_PASSWORD'],
            'pinduoduo': ['PINDUODUO_ENABLED', 'PINDUODUO_USERNAME', 'PINDUODUO_PASSWORD'],
            'xiaohongshu': ['XIAOHONGSHU_ENABLED', 'XIAOHONGSHU_USERNAME', 'XIAOHONGSHU_PASSWORD'],
            'douyin': ['DOUYIN_ENABLED', 'DOUYIN_USERNAME', 'DOUYIN_PASSWORD'],
            'wechat': ['WECHAT_ENABLED', 'WECHAT_APP_ID', 'WECHAT_APP_SECRET']
        }
        
        keys = config_keys.get(platform_name, [])
        result = {}
        
        for key in keys:
            result[key] = cls.get_config(key)
        
        return result
    
    @classmethod
    def is_platform_enabled(cls, platform_name: str) -> bool:
        """
        检查平台是否启用
        
        Args:
            platform_name: 平台名称
            
        Returns:
            是否启用
        """
        enabled_key = f"{platform_name.upper()}_ENABLED"
        return cls.get_config(enabled_key, False)
    
    @classmethod
    def get_agent_config(cls, agent_type: str) -> Dict[str, Any]:
        """
        获取智能体配置
        
        Args:
            agent_type: 智能体类型 (sentiment, intent, etc.)
            
        Returns:
            智能体配置字典
        """
        config_keys = {
            'sentiment': ['SENTIMENT_ENABLED', 'SENTIMENT_MODEL', 'SENTIMENT_THRESHOLD'],
            'intent': ['INTENT_RECOGNITION_ENABLED', 'INTENT_MODEL'],
            'ocr': ['OCR_ENABLED', 'OCR_MODEL'],
            'speech': ['SPEECH_TO_TEXT_ENABLED', 'VIDEO_TRANSCRIPT_ENABLED']
        }
        
        keys = config_keys.get(agent_type, [])
        result = {}
        
        for key in keys:
            result[key] = cls.get_config(key)
        
        return result


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return ConfigService.get_config(key, default)


def set_config(key: str, value: Any) -> bool:
    """设置配置值的便捷函数"""
    return ConfigService.set_config(key, value)


def get_ai_config(provider: str) -> Dict[str, Any]:
    """获取AI模型配置的便捷函数"""
    return ConfigService.get_ai_model_config(provider)


def get_platform_config(platform: str) -> Dict[str, Any]:
    """获取平台配置的便捷函数"""
    return ConfigService.get_platform_config(platform)


def is_platform_enabled(platform: str) -> bool:
    """检查平台是否启用的便捷函数"""
    return ConfigService.is_platform_enabled(platform) 