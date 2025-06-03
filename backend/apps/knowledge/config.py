"""
知识库系统配置文件
"""
import os
from django.conf import settings

# 向量数据库配置
VECTOR_DB_CONFIG = {
    'type': os.getenv('VECTOR_DB_TYPE', 'milvus'),  # milvus, pinecone, qdrant, chroma
    'milvus': {
        'host': os.getenv('MILVUS_HOST', 'localhost'),
        'port': os.getenv('MILVUS_PORT', '19530'),
        'user': os.getenv('MILVUS_USER', ''),
        'password': os.getenv('MILVUS_PASSWORD', ''),
        'secure': os.getenv('MILVUS_SECURE', 'False').lower() == 'true',
        'collection_prefix': os.getenv('MILVUS_COLLECTION_PREFIX', 'kb_'),
    },
    'pinecone': {
        'api_key': os.getenv('PINECONE_API_KEY', ''),
        'environment': os.getenv('PINECONE_ENVIRONMENT', 'us-east1-gcp'),
        'index_prefix': os.getenv('PINECONE_INDEX_PREFIX', 'kb-'),
    },
    'qdrant': {
        'url': os.getenv('QDRANT_URL', 'http://localhost:6333'),
        'api_key': os.getenv('QDRANT_API_KEY', ''),
        'collection_prefix': os.getenv('QDRANT_COLLECTION_PREFIX', 'kb_'),
    },
    'chroma': {
        'host': os.getenv('CHROMA_HOST', 'localhost'),
        'port': os.getenv('CHROMA_PORT', '8000'),
        'collection_prefix': os.getenv('CHROMA_COLLECTION_PREFIX', 'kb_'),
    }
}

# 预训练模型配置
EMBEDDING_MODELS = {
    'default': {
        'name': 'text2vec-base-chinese',
        'model_name': 'shibing624/text2vec-base-chinese',
        'dimension': 768,
        'max_seq_length': 512,
        'device': 'auto',  # auto, cpu, cuda
    },
    'multilingual': {
        'name': 'text2vec-base-multilingual',
        'model_name': 'sentence-transformers/distiluse-base-multilingual-cased',
        'dimension': 512,
        'max_seq_length': 512,
        'device': 'auto',
    },
    'large': {
        'name': 'text2vec-large-chinese',
        'model_name': 'GanymedeNil/text2vec-large-chinese',
        'dimension': 1024,
        'max_seq_length': 512,
        'device': 'auto',
    },
    'bge_large': {
        'name': 'bge-large-zh-v1.5',
        'model_name': 'BAAI/bge-large-zh-v1.5',
        'dimension': 1024,
        'max_seq_length': 512,
        'device': 'auto',
    }
}

# RAGFlow配置
RAGFLOW_CONFIG = {
    'enabled': os.getenv('RAGFLOW_ENABLED', 'True').lower() == 'true',
    'base_url': os.getenv('RAGFLOW_BASE_URL', 'http://localhost:9380'),
    'api_key': os.getenv('RAGFLOW_API_KEY', ''),
    'user_id': os.getenv('RAGFLOW_USER_ID', ''),
    'dataset_prefix': os.getenv('RAGFLOW_DATASET_PREFIX', 'ShopTalk_'),
    'chunk_size': int(os.getenv('RAGFLOW_CHUNK_SIZE', '512')),
    'chunk_overlap': int(os.getenv('RAGFLOW_CHUNK_OVERLAP', '50')),
    'auto_sync': os.getenv('RAGFLOW_AUTO_SYNC', 'True').lower() == 'true',
    'sync_interval': int(os.getenv('RAGFLOW_SYNC_INTERVAL', '300')),  # 秒
}

# 知识库分块配置
CHUNKING_CONFIG = {
    'scripts': {
        'chunk_size': 256,
        'chunk_overlap': 50,
        'separators': ['\n\n', '\n', '。', '！', '？', ';', ','],
        'min_chunk_size': 50,
        'max_chunk_size': 1000,
    },
    'products': {
        'chunk_size': 512,
        'chunk_overlap': 100,
        'separators': ['\n\n', '\n', '。', '！', '？'],
        'min_chunk_size': 100,
        'max_chunk_size': 2000,
    },
    'documents': {
        'chunk_size': 1024,
        'chunk_overlap': 200,
        'separators': ['\n\n', '\n', '。'],
        'min_chunk_size': 200,
        'max_chunk_size': 4000,
    },
    'faqs': {
        'chunk_size': 512,
        'chunk_overlap': 100,
        'separators': ['\n\n', '\n', '。', '！', '？'],
        'min_chunk_size': 100,
        'max_chunk_size': 1500,
    }
}

# 搜索配置
SEARCH_CONFIG = {
    'default_top_k': 10,
    'max_top_k': 50,
    'similarity_threshold': 0.7,
    'rerank_enabled': True,
    'rerank_top_k': 20,
    'hybrid_search': True,
    'semantic_weight': 0.7,
    'keyword_weight': 0.3,
}

# 缓存配置
CACHE_CONFIG = {
    'enabled': os.getenv('KNOWLEDGE_CACHE_ENABLED', 'True').lower() == 'true',
    'backend': os.getenv('CACHE_BACKEND', 'redis'),
    'ttl': int(os.getenv('KNOWLEDGE_CACHE_TTL', '3600')),  # 秒
    'prefix': 'kb:',
    'vector_cache_ttl': int(os.getenv('VECTOR_CACHE_TTL', '86400')),  # 24小时
}

# 导数据配置
IMPORT_CONFIG = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'allowed_formats': {
        'scripts': ['csv', 'json', 'xlsx', 'txt'],
        'products': ['csv', 'json', 'xlsx'],
        'documents': ['pdf', 'docx', 'txt', 'md', 'html'],
    },
    'batch_size': 100,
    'concurrent_workers': 4,
    'encoding_detection': True,
    'auto_tag_extraction': True,
}

# 监控配置
MONITORING_CONFIG = {
    'enabled': os.getenv('KNOWLEDGE_MONITORING_ENABLED', 'True').lower() == 'true',
    'metrics_retention_days': int(os.getenv('METRICS_RETENTION_DAYS', '30')),
    'log_slow_queries': True,
    'slow_query_threshold': 2.0,  # 秒
    'alert_thresholds': {
        'error_rate': 0.05,  # 5%
        'response_time_p95': 5.0,  # 5秒
        'vector_sync_failure_rate': 0.1,  # 10%
    }
}

# 任务队列配置
TASK_CONFIG = {
    'broker': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    'task_routes': {
        'knowledge.tasks.process_document': {'queue': 'knowledge_processing'},
        'knowledge.tasks.generate_embeddings': {'queue': 'embedding_generation'},
        'knowledge.tasks.sync_to_ragflow': {'queue': 'ragflow_sync'},
        'knowledge.tasks.batch_import': {'queue': 'data_import'},
    },
    'task_time_limit': 300,  # 5分钟
    'task_soft_time_limit': 240,  # 4分钟
}

# AI增强配置
AI_CONFIG = {
    'enabled': os.getenv('AI_ENHANCEMENT_ENABLED', 'True').lower() == 'true',
    'auto_tag_generation': True,
    'auto_summary_generation': True,
    'quality_scoring': True,
    'content_classification': True,
    'duplicate_detection': True,
    'language_detection': True,
    'sentiment_analysis': True,
}

# 获取配置辅助函数
def get_vector_db_config():
    """获取向量数据库配置"""
    db_type = VECTOR_DB_CONFIG['type']
    return VECTOR_DB_CONFIG.get(db_type, {})

def get_embedding_model_config(model_name='default'):
    """获取embedding模型配置"""
    return EMBEDDING_MODELS.get(model_name, EMBEDDING_MODELS['default'])

def get_chunking_config(content_type='documents'):
    """获取分块配置"""
    return CHUNKING_CONFIG.get(content_type, CHUNKING_CONFIG['documents'])

def is_ragflow_enabled():
    """检查RAGFlow是否启用"""
    return RAGFLOW_CONFIG['enabled']

def get_ragflow_config():
    """获取RAGFlow配置"""
    return RAGFLOW_CONFIG

def get_import_config():
    """获取导入配置"""
    return IMPORT_CONFIG

def get_search_config():
    """获取搜索配置"""
    return SEARCH_CONFIG 