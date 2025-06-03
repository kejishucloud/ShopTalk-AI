"""
智能体配置文件
配置各个智能体的参数和行为
"""

import os
from typing import Dict, Any

# 获取环境变量的辅助函数
def get_env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

# 智能体配置
AGENT_CONFIG: Dict[str, Any] = {
    
    # 标签智能体配置
    'tag_agent': {
        'confidence_threshold': get_env_float('TAG_AGENT_CONFIDENCE_THRESHOLD', 0.6),
        'max_tags_per_message': get_env_int('TAG_AGENT_MAX_TAGS', 10),
        'enable_behavior_analysis': get_env_bool('TAG_AGENT_BEHAVIOR_ANALYSIS', True),
        'custom_rules': {
            # 可以在这里添加自定义标签规则
            'vip_customer': {
                'keywords': ['VIP', '会员', '长期客户', '老客户'],
                'patterns': [r'VIP.*客户', r'会员.*级别']
            },
            'bargain_hunter': {
                'keywords': ['最低价', '能便宜点吗', '有没有折扣', '砍价'],
                'patterns': [r'.*便宜.*', r'.*折扣.*', r'.*优惠.*']
            }
        }
    },
    
    # 情感智能体配置
    'sentiment_agent': {
        'confidence_threshold': get_env_float('SENTIMENT_AGENT_THRESHOLD', 0.5),
        'enable_emotion_detection': get_env_bool('SENTIMENT_EMOTION_DETECTION', True),
        'context_window': get_env_int('SENTIMENT_CONTEXT_WINDOW', 3),
        'sentiment_history_length': get_env_int('SENTIMENT_HISTORY_LENGTH', 10),
        'custom_emotions': {
            'excited': [r'太棒了', r'真的吗', r'太好了', r'惊喜'],
            'confused': [r'不明白', r'搞不懂', r'什么意思', r'confused'],
            'impatient': [r'快点', r'赶时间', r'等不了', r'着急']
        }
    },
    
    # 记忆智能体配置
    'memory_agent': {
        'max_short_memory': get_env_int('MEMORY_AGENT_MAX_SHORT', 50),
        'max_long_memory': get_env_int('MEMORY_AGENT_MAX_LONG', 200),
        'context_window': get_env_int('MEMORY_AGENT_CONTEXT_WINDOW', 15),
        'memory_decay_hours': get_env_int('MEMORY_AGENT_DECAY_HOURS', 48),
        'importance_threshold': get_env_float('MEMORY_IMPORTANCE_THRESHOLD', 0.7),
        'enable_user_profiling': get_env_bool('MEMORY_USER_PROFILING', True),
        'profile_update_frequency': get_env_int('MEMORY_PROFILE_UPDATE_FREQ', 5)
    },
    
    # 知识库智能体配置
    'knowledge_agent': {
        'ragflow': {
            'api_endpoint': os.getenv('RAGFLOW_API_ENDPOINT', 'http://localhost:9380'),
            'api_key': os.getenv('RAGFLOW_API_KEY', ''),
            'dataset_id': os.getenv('RAGFLOW_DATASET_ID', ''),
            'timeout': get_env_int('RAGFLOW_TIMEOUT', 30)
        },
        'top_k': get_env_int('KNOWLEDGE_AGENT_TOP_K', 5),
        'similarity_threshold': get_env_float('KNOWLEDGE_AGENT_SIMILARITY_THRESHOLD', 0.7),
        'max_tokens': get_env_int('KNOWLEDGE_AGENT_MAX_TOKENS', 1000),
        'enable_local_fallback': get_env_bool('KNOWLEDGE_LOCAL_FALLBACK', True),
        'cache_results': get_env_bool('KNOWLEDGE_CACHE_RESULTS', True),
        'cache_ttl': get_env_int('KNOWLEDGE_CACHE_TTL', 3600),
        'knowledge_bases': {
            'product': {'weight': 1.0, 'boost': 1.2},
            'faq': {'weight': 0.9, 'boost': 1.1},
            'policy': {'weight': 0.8, 'boost': 1.0},
            'script': {'weight': 0.7, 'boost': 0.9}
        }
    },
    
    # 聊天智能体配置
    'chat_agent': {
        'langflow': {
            'endpoint': os.getenv('LANGFLOW_ENDPOINT', 'http://localhost:7860'),
            'api_key': os.getenv('LANGFLOW_API_KEY', ''),
            'flow_id': os.getenv('LANGFLOW_FLOW_ID', ''),
            'timeout': get_env_int('LANGFLOW_TIMEOUT', 60)
        },
        'llm': {
            'model': os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
            'temperature': get_env_float('LLM_TEMPERATURE', 0.7),
            'max_tokens': get_env_int('LLM_MAX_TOKENS', 1000),
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        },
        'conversation_flow': {
            'max_turns': get_env_int('CHAT_MAX_TURNS', 50),
            'state_timeout': get_env_int('CHAT_STATE_TIMEOUT', 1800),  # 30分钟
            'enable_context_compression': get_env_bool('CHAT_CONTEXT_COMPRESSION', True),
            'fallback_responses': get_env_bool('CHAT_FALLBACK_RESPONSES', True)
        },
        'personalization': {
            'adapt_to_user_style': get_env_bool('CHAT_ADAPT_STYLE', True),
            'remember_preferences': get_env_bool('CHAT_REMEMBER_PREFS', True),
            'use_user_history': get_env_bool('CHAT_USE_HISTORY', True)
        }
    }
}

# 全局智能体配置
GLOBAL_AGENT_CONFIG = {
    'enable_parallel_processing': get_env_bool('AGENT_PARALLEL_PROCESSING', True),
    'max_concurrent_agents': get_env_int('AGENT_MAX_CONCURRENT', 4),
    'default_timeout': get_env_int('AGENT_DEFAULT_TIMEOUT', 30),
    'retry_attempts': get_env_int('AGENT_RETRY_ATTEMPTS', 3),
    'enable_metrics': get_env_bool('AGENT_ENABLE_METRICS', True),
    'log_level': os.getenv('AGENT_LOG_LEVEL', 'INFO'),
    'enable_debugging': get_env_bool('AGENT_ENABLE_DEBUG', False)
}

# 智能体优先级配置
AGENT_PRIORITY = {
    'sentiment_agent': 1,    # 最高优先级
    'memory_agent': 2,       # 高优先级
    'tag_agent': 3,          # 中等优先级
    'knowledge_agent': 4,    # 中等优先级
    'chat_agent': 5          # 最低优先级（通常最后执行）
}

# 智能体依赖关系
AGENT_DEPENDENCIES = {
    'chat_agent': ['sentiment_agent', 'memory_agent', 'tag_agent', 'knowledge_agent'],
    'knowledge_agent': ['tag_agent'],
    'memory_agent': ['sentiment_agent', 'tag_agent'],
    'tag_agent': [],
    'sentiment_agent': []
}

# 性能配置
PERFORMANCE_CONFIG = {
    'enable_caching': get_env_bool('AGENT_ENABLE_CACHING', True),
    'cache_backend': os.getenv('AGENT_CACHE_BACKEND', 'redis'),
    'cache_prefix': os.getenv('AGENT_CACHE_PREFIX', 'agent:'),
    'cache_default_ttl': get_env_int('AGENT_CACHE_TTL', 3600),
    
    'enable_profiling': get_env_bool('AGENT_ENABLE_PROFILING', False),
    'profiling_sample_rate': get_env_float('AGENT_PROFILING_RATE', 0.1),
    
    'enable_rate_limiting': get_env_bool('AGENT_RATE_LIMITING', True),
    'rate_limit_requests': get_env_int('AGENT_RATE_LIMIT_REQUESTS', 100),
    'rate_limit_window': get_env_int('AGENT_RATE_LIMIT_WINDOW', 60),
    
    'memory_optimization': {
        'enable_gc': get_env_bool('AGENT_ENABLE_GC', True),
        'gc_threshold': get_env_int('AGENT_GC_THRESHOLD', 1000),
        'max_memory_mb': get_env_int('AGENT_MAX_MEMORY_MB', 1024)
    }
}

# 监控和告警配置
MONITORING_CONFIG = {
    'enable_health_checks': get_env_bool('AGENT_HEALTH_CHECKS', True),
    'health_check_interval': get_env_int('AGENT_HEALTH_CHECK_INTERVAL', 60),
    
    'enable_alerts': get_env_bool('AGENT_ENABLE_ALERTS', True),
    'alert_thresholds': {
        'response_time_ms': get_env_int('AGENT_ALERT_RESPONSE_TIME', 5000),
        'error_rate_percent': get_env_float('AGENT_ALERT_ERROR_RATE', 5.0),
        'memory_usage_percent': get_env_float('AGENT_ALERT_MEMORY_USAGE', 80.0)
    },
    
    'metrics_collection': {
        'enable_detailed_metrics': get_env_bool('AGENT_DETAILED_METRICS', True),
        'metrics_retention_days': get_env_int('AGENT_METRICS_RETENTION', 30),
        'export_format': os.getenv('AGENT_METRICS_FORMAT', 'prometheus')
    }
}

# 开发和调试配置
DEVELOPMENT_CONFIG = {
    'enable_debug_mode': get_env_bool('AGENT_DEBUG_MODE', False),
    'debug_log_requests': get_env_bool('AGENT_DEBUG_LOG_REQUESTS', False),
    'debug_log_responses': get_env_bool('AGENT_DEBUG_LOG_RESPONSES', False),
    'enable_test_mode': get_env_bool('AGENT_TEST_MODE', False),
    'mock_external_apis': get_env_bool('AGENT_MOCK_APIS', False),
    
    'development_shortcuts': {
        'skip_authentication': get_env_bool('AGENT_SKIP_AUTH', False),
        'use_dummy_data': get_env_bool('AGENT_USE_DUMMY_DATA', False),
        'enable_hot_reload': get_env_bool('AGENT_HOT_RELOAD', False)
    }
}

# 导出配置函数
def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """获取指定智能体的配置"""
    return AGENT_CONFIG.get(agent_name, {})

def get_global_config() -> Dict[str, Any]:
    """获取全局智能体配置"""
    return GLOBAL_AGENT_CONFIG

def get_performance_config() -> Dict[str, Any]:
    """获取性能配置"""
    return PERFORMANCE_CONFIG

def get_monitoring_config() -> Dict[str, Any]:
    """获取监控配置"""
    return MONITORING_CONFIG

def update_agent_config(agent_name: str, config_updates: Dict[str, Any]):
    """更新智能体配置"""
    if agent_name in AGENT_CONFIG:
        AGENT_CONFIG[agent_name].update(config_updates)
    else:
        AGENT_CONFIG[agent_name] = config_updates

def validate_config() -> bool:
    """验证配置的有效性"""
    required_keys = ['tag_agent', 'sentiment_agent', 'memory_agent', 'knowledge_agent', 'chat_agent']
    
    for key in required_keys:
        if key not in AGENT_CONFIG:
            return False
    
    # 验证RAGFlow配置
    ragflow_config = AGENT_CONFIG.get('knowledge_agent', {}).get('ragflow', {})
    if not ragflow_config.get('api_endpoint'):
        print("Warning: RAGFlow API endpoint not configured")
    
    # 验证Langflow配置
    langflow_config = AGENT_CONFIG.get('chat_agent', {}).get('langflow', {})
    if not langflow_config.get('endpoint'):
        print("Warning: Langflow endpoint not configured")
    
    # 验证LLM配置
    llm_config = AGENT_CONFIG.get('chat_agent', {}).get('llm', {})
    if not llm_config.get('api_key'):
        print("Warning: LLM API key not configured")
    
    return True 