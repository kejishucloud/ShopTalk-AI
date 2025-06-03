"""
智能体服务配置管理模块
集中管理RAGFlow、Langflow、情感分析模型、Redis、数据库连接等配置项
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional
from django.conf import settings


@dataclass
class RAGFlowConfig:
    """RAGFlow配置类"""
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载RAGFlow配置"""
        return cls(
            base_url=getattr(settings, 'RAGFLOW_BASE_URL', 'http://localhost:9380'),
            api_key=getattr(settings, 'RAGFLOW_API_KEY', ''),
            timeout=getattr(settings, 'RAGFLOW_TIMEOUT', 30),
            max_retries=getattr(settings, 'RAGFLOW_MAX_RETRIES', 3)
        )


@dataclass
class LangflowConfig:
    """Langflow配置类"""
    base_url: str
    api_key: str
    flow_id: str
    timeout: int = 30
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载Langflow配置"""
        return cls(
            base_url=getattr(settings, 'LANGFLOW_BASE_URL', 'http://localhost:7860'),
            api_key=getattr(settings, 'LANGFLOW_API_KEY', ''),
            flow_id=getattr(settings, 'LANGFLOW_FLOW_ID', ''),
            timeout=getattr(settings, 'LANGFLOW_TIMEOUT', 30)
        )


@dataclass
class SentimentConfig:
    """情感分析配置类"""
    model_type: str  # 'snownlp', 'transformers', 'custom'
    model_path: Optional[str] = None
    model_name: Optional[str] = None
    threshold_positive: float = 0.6
    threshold_negative: float = 0.4
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存时间（秒）
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载情感分析配置"""
        return cls(
            model_type=getattr(settings, 'SENTIMENT_MODEL_TYPE', 'snownlp'),
            model_path=getattr(settings, 'SENTIMENT_MODEL_PATH', None),
            model_name=getattr(settings, 'SENTIMENT_MODEL_NAME', 'bert-base-chinese'),
            threshold_positive=getattr(settings, 'SENTIMENT_THRESHOLD_POSITIVE', 0.6),
            threshold_negative=getattr(settings, 'SENTIMENT_THRESHOLD_NEGATIVE', 0.4),
            cache_enabled=getattr(settings, 'SENTIMENT_CACHE_ENABLED', True),
            cache_ttl=getattr(settings, 'SENTIMENT_CACHE_TTL', 3600)
        )


@dataclass
class RedisConfig:
    """Redis配置类"""
    host: str
    port: int
    db: int
    password: Optional[str] = None
    max_connections: int = 10
    decode_responses: bool = True
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载Redis配置"""
        return cls(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            password=getattr(settings, 'REDIS_PASSWORD', None),
            max_connections=getattr(settings, 'REDIS_MAX_CONNECTIONS', 10),
            decode_responses=getattr(settings, 'REDIS_DECODE_RESPONSES', True)
        )


@dataclass
class ContextConfig:
    """上下文管理配置类"""
    max_history_length: int = 10  # 最大历史消息数量
    context_window_hours: int = 24  # 上下文窗口时间（小时）
    cleanup_interval_hours: int = 6  # 清理间隔时间（小时）
    summary_enabled: bool = True  # 是否启用上下文摘要
    summary_threshold: int = 5  # 触发摘要的消息数量阈值
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载上下文配置"""
        return cls(
            max_history_length=getattr(settings, 'CONTEXT_MAX_HISTORY_LENGTH', 10),
            context_window_hours=getattr(settings, 'CONTEXT_WINDOW_HOURS', 24),
            cleanup_interval_hours=getattr(settings, 'CONTEXT_CLEANUP_INTERVAL_HOURS', 6),
            summary_enabled=getattr(settings, 'CONTEXT_SUMMARY_ENABLED', True),
            summary_threshold=getattr(settings, 'CONTEXT_SUMMARY_THRESHOLD', 5)
        )


@dataclass
class TagConfig:
    """标签管理配置类"""
    default_weight: float = 1.0  # 默认标签权重
    decay_factor: float = 0.95  # 权重衰减因子
    max_tags_per_user: int = 50  # 每个用户最大标签数
    min_weight_threshold: float = 0.1  # 最小权重阈值
    auto_cleanup_enabled: bool = True  # 是否启用自动清理
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载标签配置"""
        return cls(
            default_weight=getattr(settings, 'TAG_DEFAULT_WEIGHT', 1.0),
            decay_factor=getattr(settings, 'TAG_DECAY_FACTOR', 0.95),
            max_tags_per_user=getattr(settings, 'TAG_MAX_TAGS_PER_USER', 50),
            min_weight_threshold=getattr(settings, 'TAG_MIN_WEIGHT_THRESHOLD', 0.1),
            auto_cleanup_enabled=getattr(settings, 'TAG_AUTO_CLEANUP_ENABLED', True)
        )


@dataclass
class KnowledgeBaseConfig:
    """知识库配置类"""
    scripts_table: str = 'knowledge_scripts'  # 话术知识库表名
    products_table: str = 'knowledge_products'  # 产品知识库表名
    batch_size: int = 100  # 批量插入大小
    vector_db_enabled: bool = False  # 是否启用向量数据库
    vector_db_type: str = 'milvus'  # 向量数据库类型
    vector_dimension: int = 768  # 向量维度
    
    @classmethod
    def from_settings(cls):
        """从Django设置中加载知识库配置"""
        return cls(
            scripts_table=getattr(settings, 'KB_SCRIPTS_TABLE', 'knowledge_scripts'),
            products_table=getattr(settings, 'KB_PRODUCTS_TABLE', 'knowledge_products'),
            batch_size=getattr(settings, 'KB_BATCH_SIZE', 100),
            vector_db_enabled=getattr(settings, 'KB_VECTOR_DB_ENABLED', False),
            vector_db_type=getattr(settings, 'KB_VECTOR_DB_TYPE', 'milvus'),
            vector_dimension=getattr(settings, 'KB_VECTOR_DIMENSION', 768)
        )


class AgentConfigManager:
    """智能体配置管理器"""
    
    def __init__(self):
        self._configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置"""
        self._configs = {
            'ragflow': RAGFlowConfig.from_settings(),
            'langflow': LangflowConfig.from_settings(),
            'sentiment': SentimentConfig.from_settings(),
            'redis': RedisConfig.from_settings(),
            'context': ContextConfig.from_settings(),
            'tag': TagConfig.from_settings(),
            'knowledge_base': KnowledgeBaseConfig.from_settings()
        }
    
    def get_config(self, config_name: str):
        """获取指定配置"""
        return self._configs.get(config_name)
    
    def get_all_configs(self) -> Dict:
        """获取所有配置"""
        return self._configs.copy()
    
    def update_config(self, config_name: str, config_data: dict):
        """更新配置"""
        if config_name in self._configs:
            config_class = type(self._configs[config_name])
            self._configs[config_name] = config_class(**config_data)
    
    def reload_configs(self):
        """重新加载所有配置"""
        self._load_all_configs()


# 全局配置管理器实例
config_manager = AgentConfigManager()


def get_ragflow_config() -> RAGFlowConfig:
    """获取RAGFlow配置"""
    return config_manager.get_config('ragflow')


def get_langflow_config() -> LangflowConfig:
    """获取Langflow配置"""
    return config_manager.get_config('langflow')


def get_sentiment_config() -> SentimentConfig:
    """获取情感分析配置"""
    return config_manager.get_config('sentiment')


def get_redis_config() -> RedisConfig:
    """获取Redis配置"""
    return config_manager.get_config('redis')


def get_context_config() -> ContextConfig:
    """获取上下文配置"""
    return config_manager.get_config('context')


def get_tag_config() -> TagConfig:
    """获取标签配置"""
    return config_manager.get_config('tag')


def get_knowledge_base_config() -> KnowledgeBaseConfig:
    """获取知识库配置"""
    return config_manager.get_config('knowledge_base') 