# 知识库管理模块

## 概述

知识库管理模块是ShopTalk-AI智能客服系统的核心组件之一，提供企业级的知识内容管理、智能检索、自动化处理等功能。该模块支持多种类型的知识内容管理，包括文档、FAQ、商品信息、话术模板等。

## 主要功能

### 🏗️ 核心功能

1. **知识库管理**
   - 支持多种知识库类型（商品、FAQ、话术、政策、技术文档等）
   - 灵活的访问权限控制
   - 版本控制和AI增强功能
   - 统计分析和性能监控

2. **文档管理**
   - 支持多种文件格式（PDF、Word、Excel、文本、Markdown等）
   - 自动文本提取和内容分析
   - 文档版本管理和变更追踪
   - 智能关键词提取和摘要生成

3. **FAQ管理**
   - 问答对的创建、编辑和分类
   - 智能问答匹配和推荐
   - 用户反馈和评分系统
   - AI自动生成FAQ功能

4. **商品信息管理**
   - 完整的商品信息库
   - 库存管理和价格跟踪
   - 多媒体资源管理
   - SEO优化支持

5. **话术模板管理**
   - 多场景话术模板
   - 变量和占位符支持
   - 使用统计和效果分析
   - AI话术优化建议

### 🔍 智能检索

1. **多维度搜索**
   - 全文搜索和关键词匹配
   - 向量化语义搜索
   - 分类和标签筛选
   - 权限过滤和个性化排序

2. **智能推荐**
   - 基于相似度的内容推荐
   - 用户行为分析推荐
   - 热门内容推荐
   - AI算法优化推荐

### 📊 分析统计

1. **访问统计**
   - 内容访问量分析
   - 用户行为追踪
   - 搜索热词统计
   - 响应时间监控

2. **内容分析**
   - 内容质量评估
   - 更新频率分析
   - 用户满意度统计
   - 知识覆盖度分析

### 🤖 AI增强

1. **自动化处理**
   - 文档内容自动提取
   - 关键词智能提取
   - 摘要自动生成
   - 分类自动推荐

2. **向量化处理**
   - 文本向量化存储
   - 语义相似度计算
   - 智能聚类分析
   - 质量评分优化

## 技术架构

### 数据模型

```python
# 核心模型关系图
KnowledgeBase (知识库)
├── Document (文档)
├── FAQ (问答)
├── Product (商品)
├── Script (话术)
├── KnowledgeVector (向量)
├── KnowledgeAccessRecord (访问记录)
└── KnowledgeRecommendation (推荐)

# 辅助模型
DocumentCategory (分类)
DocumentTag (标签)
```

### 服务架构

```python
# 服务层结构
DocumentProcessorService    # 文档处理服务
VectorizeService           # 向量化服务
KnowledgeSearchService     # 搜索服务
RecommendationService      # 推荐服务
KnowledgeAnalyticsService  # 分析统计服务
```

### API接口

```
# RESTful API 端点
GET    /api/v1/knowledge/knowledge-bases/          # 获取知识库列表
POST   /api/v1/knowledge/knowledge-bases/          # 创建知识库
GET    /api/v1/knowledge/knowledge-bases/{id}/     # 获取知识库详情
PUT    /api/v1/knowledge/knowledge-bases/{id}/     # 更新知识库
DELETE /api/v1/knowledge/knowledge-bases/{id}/     # 删除知识库

GET    /api/v1/knowledge/documents/               # 获取文档列表
POST   /api/v1/knowledge/documents/upload/        # 上传文档
GET    /api/v1/knowledge/documents/{id}/          # 获取文档详情
POST   /api/v1/knowledge/documents/{id}/process/  # 处理文档
GET    /api/v1/knowledge/documents/{id}/download/ # 下载文档

POST   /api/v1/knowledge/search/search/           # 智能搜索
POST   /api/v1/knowledge/batch-operations/        # 批量操作
```

## 安装部署

### 1. 环境要求

- Python 3.8+
- Django 4.2+
- PostgreSQL 12+
- Redis 6.0+
- Celery 5.0+

### 2. 依赖安装

```bash
# 核心依赖
pip install Django>=4.2.7
pip install djangorestframework>=3.14.0
pip install psycopg2-binary>=2.9.7
pip install celery>=5.3.4
pip install redis>=5.0.1

# 文档处理依赖
pip install PyPDF2>=3.0.1
pip install python-docx>=1.1.0
pip install openpyxl>=3.1.2

# AI处理依赖
pip install sentence-transformers>=2.2.2
pip install jieba>=0.42.1
pip install numpy>=1.24.3

# 向量数据库
pip install faiss-cpu>=1.7.4
# 或
pip install chromadb>=0.4.15
```

### 3. 数据库配置

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'shoptalk_ai',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 知识库配置
KNOWLEDGE_EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
KNOWLEDGE_CHUNK_SIZE = 512
KNOWLEDGE_CHUNK_OVERLAP = 50
```

### 4. 初始化数据库

```bash
python manage.py makemigrations knowledge
python manage.py migrate
```

### 5. 启动服务

```bash
# 启动Django服务
python manage.py runserver

# 启动Celery任务队列
celery -A core worker -l info

# 启动Celery定时任务
celery -A core beat -l info
```

## 使用指南

### 创建知识库

```python
from apps.knowledge.models import KnowledgeBase

# 创建知识库
kb = KnowledgeBase.objects.create(
    name="商品知识库",
    knowledge_type="product",
    description="包含所有商品信息的知识库",
    access_level="internal",
    enable_ai_enhancement=True,
    auto_extract_keywords=True,
    created_by=user
)
```

### 上传文档

```python
from apps.knowledge.services import DocumentProcessorService

# 上传并处理文档
processor = DocumentProcessorService()
result = processor.process_document(document)

if result['success']:
    print(f"文档处理成功: {result['summary']}")
else:
    print(f"处理失败: {result['error']}")
```

### 智能搜索

```python
from apps.knowledge.services import KnowledgeSearchService

# 执行搜索
search_service = KnowledgeSearchService()
results = search_service.search(
    query="如何退货",
    knowledge_base_id=1,
    content_types=['document', 'faq'],
    limit=10,
    include_vectors=True
)

for result in results['results']:
    print(f"标题: {result['title']}")
    print(f"摘要: {result['summary']}")
    print(f"评分: {result['score']}")
```

### 生成推荐

```python
from apps.knowledge.services import RecommendationService

# 生成推荐
rec_service = RecommendationService()
recommendations = rec_service.generate_recommendations(
    'document', document_id, knowledge_base_id, limit=5
)

for rec in recommendations:
    print(f"推荐内容: {rec['content_type']}:{rec['content_id']}")
    print(f"相似度: {rec['score']}")
```

## API使用示例

### 1. 创建知识库

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/knowledge-bases/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "name": "FAQ知识库",
    "knowledge_type": "faq",
    "description": "常见问题解答",
    "access_level": "public",
    "enable_ai_enhancement": true
  }'
```

### 2. 上传文档

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/documents/upload/ \
  -H "Authorization: Bearer your_token" \
  -F "knowledge_base_id=1" \
  -F "title=产品手册" \
  -F "file=@product_manual.pdf" \
  -F "auto_extract=true" \
  -F "auto_vectorize=true"
```

### 3. 智能搜索

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search/search/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "query": "退货政策",
    "knowledge_base_id": 1,
    "content_types": ["document", "faq"],
    "limit": 10,
    "include_vectors": true,
    "similarity_threshold": 0.7
  }'
```

### 4. 获取分析数据

```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/knowledge-bases/1/analytics/?date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer your_token"
```

## 定时任务

系统提供多个定时任务来维护知识库的健康状态：

### 配置定时任务

```python
# celery_beat_schedule.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # 每日统计更新
    'update-knowledge-statistics': {
        'task': 'apps.knowledge.tasks.update_knowledge_base_statistics',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
    
    # 文档处理
    'process-pending-documents': {
        'task': 'apps.knowledge.tasks.process_pending_documents',
        'schedule': crontab(minute='*/10'),  # 每10分钟
    },
    
    # 自动向量化
    'auto-vectorize-content': {
        'task': 'apps.knowledge.tasks.auto_vectorize_content',
        'schedule': crontab(minute='*/30'),  # 每30分钟
    },
    
    # 健康检查
    'health-check': {
        'task': 'apps.knowledge.tasks.health_check_knowledge_system',
        'schedule': crontab(minute='*/5'),  # 每5分钟
    },
    
    # 清理任务
    'cleanup-old-records': {
        'task': 'apps.knowledge.tasks.cleanup_old_access_records',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点
        'kwargs': {'days_to_keep': 90}
    },
}
```

## 性能优化

### 1. 数据库优化

```python
# 索引优化
class Document(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['document_type']),
            models.Index(fields=['process_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['view_count']),
        ]
```

### 2. 缓存配置

```python
# Redis缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 缓存使用示例
from django.core.cache import cache

def get_popular_documents(knowledge_base_id):
    cache_key = f"popular_docs_{knowledge_base_id}"
    result = cache.get(cache_key)
    
    if result is None:
        result = Document.objects.filter(
            knowledge_base_id=knowledge_base_id,
            is_active=True
        ).order_by('-view_count')[:10]
        
        cache.set(cache_key, result, 3600)  # 缓存1小时
    
    return result
```

### 3. 向量搜索优化

```python
# FAISS索引优化
import faiss
import numpy as np

class OptimizedVectorService:
    def __init__(self):
        self.index = None
        self.dimension = 384
    
    def build_index(self, vectors):
        """构建FAISS索引"""
        vectors_array = np.array(vectors).astype('float32')
        
        # 使用IVF索引提高搜索速度
        nlist = 100
        quantizer = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        # 训练索引
        self.index.train(vectors_array)
        self.index.add(vectors_array)
    
    def search(self, query_vector, k=10):
        """快速向量搜索"""
        query_array = np.array([query_vector]).astype('float32')
        scores, indices = self.index.search(query_array, k)
        return scores[0], indices[0]
```

## 监控和日志

### 1. 日志配置

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'knowledge_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/knowledge.log',
        },
    },
    'loggers': {
        'knowledge': {
            'handlers': ['knowledge_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. 性能监控

```python
import time
import logging
from functools import wraps

logger = logging.getLogger('knowledge')

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {str(e)}")
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            logger.info(f"函数 {func.__name__} 执行时间: {execution_time:.2f}秒, 成功: {success}")
        
        return result
    return wrapper
```

## 故障排除

### 常见问题

1. **文档处理失败**
   ```python
   # 检查文档状态
   failed_docs = Document.objects.filter(process_status='failed')
   for doc in failed_docs:
       print(f"失败文档: {doc.title}, 错误: {doc.process_message}")
   ```

2. **向量化失败**
   ```python
   # 检查向量模型
   from apps.knowledge.services import VectorizeService
   
   try:
       service = VectorizeService()
       model = service.get_embedding_model()
       print("向量模型加载成功")
   except Exception as e:
       print(f"向量模型加载失败: {e}")
   ```

3. **搜索性能问题**
   ```python
   # 检查索引状态
   from django.db import connection
   
   with connection.cursor() as cursor:
       cursor.execute("SELECT indexname, tablename FROM pg_indexes WHERE tablename LIKE 'knowledge_%'")
       indexes = cursor.fetchall()
       print("数据库索引:", indexes)
   ```

### 性能调优建议

1. **数据库优化**
   - 定期更新表统计信息
   - 适当设置数据库连接池
   - 使用读写分离

2. **缓存策略**
   - 热门内容缓存
   - 搜索结果缓存
   - 向量计算结果缓存

3. **异步处理**
   - 文档处理异步化
   - 向量计算异步化
   - 推荐生成异步化

## 版本历史

### v1.0.0 (2024-01-15)
- 初始版本发布
- 基础知识库管理功能
- 文档上传和处理
- 简单搜索功能

### v1.1.0 (2024-01-20)
- 添加向量化搜索
- 智能推荐功能
- 分析统计模块

### v1.2.0 (2024-01-25)
- 完善管理后台
- 添加定时任务
- 性能优化

## 贡献指南

欢迎为知识库管理模块贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 联系方式

如有问题或建议，请联系开发团队：
- 邮箱：dev@shoptalk-ai.com
- 文档：https://docs.shoptalk-ai.com
- 问题反馈：https://github.com/shoptalk-ai/issues 