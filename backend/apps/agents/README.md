# 智能体核心功能模块

基于Python和Django后端的智能体系统，实现用户标签管理、情感分析、上下文记忆、知识库响应和聊天数据处理等核心功能。

## 系统架构

```
backend/apps/agents/
├── services/
│   └── config.py              # 配置管理
├── utils/
│   ├── __init__.py
│   ├── text_processing.py     # 文本处理工具
│   ├── vector_utils.py        # 向量计算工具
│   ├── cache_utils.py         # 缓存工具
│   └── validation.py          # 验证工具
├── controllers.py             # 业务逻辑控制器
├── services.py                # 核心功能服务
├── tasks.py                   # 异步任务
├── examples.py                # 使用示例
└── README.md                  # 说明文档
```

## 核心功能模块

### 1. 用户标签管理 (TagManager)

**功能特性：**
- 基于关键词、模型预测、历史行为的多维度标签分析
- 支持标签权重管理和自动衰减
- 标签数量限制和低权重标签清理
- Redis缓存优化性能

**使用示例：**
```python
from agents.controllers import UserTagController

tag_controller = UserTagController()

# 分析消息并更新用户标签
result = tag_controller.analyze_and_update_tags(
    user_id="user_12345",
    message="我想买一个便宜的手机"
)

# 获取用户所有标签
tags_result = tag_controller.get_user_tags("user_12345")
```

**标签类型：**
- `price_sensitive`: 价格敏感
- `quality_focused`: 注重质量
- `service_oriented`: 关注服务
- `discount_seeker`: 寻求优惠
- `return_requester`: 退货倾向

### 2. 情感分析 (SentimentAnalyzer)

**支持模型：**
- SnowNLP：轻量级中文情感分析
- Transformers：基于BERT的深度学习模型
- 自定义模型：可扩展接入其他模型

**功能特性：**
- 实时情感极性分析（正面/中性/负面）
- 情感分数和置信度计算
- 批量分析和缓存优化
- 情感统计和趋势分析

**使用示例：**
```python
from agents.controllers import SentimentController

sentiment_controller = SentimentController()

# 单个文本情感分析
result = sentiment_controller.analyze_text_sentiment(
    text="这个产品真的很棒，我很满意！",
    user_id="user_12345"
)

# 批量情感分析
batch_result = sentiment_controller.batch_analyze_sentiment([
    "质量很好，推荐购买",
    "发货太慢了，不满意",
    "还可以吧，没有特别感觉"
])
```

### 3. 上下文记忆管理 (ContextManager)

**功能特性：**
- 基于会话ID的上下文追踪
- Redis缓存 + 数据库持久化
- 自动上下文摘要生成
- 过期上下文清理机制
- LLM友好的上下文格式化

**使用示例：**
```python
from agents.controllers import ContextController

context_controller = ContextController()

# 添加消息到上下文
result = context_controller.add_message_to_context(
    session_id="session_12345",
    message={
        "role": "user",
        "content": "你好，我想了解产品信息"
    }
)

# 获取LLM格式的上下文
context_result = context_controller.get_session_context(
    session_id="session_12345",
    format_for_llm=True
)
```

### 4. 知识库响应 (KBResponder)

**RAGFlow集成：**
- 支持向量检索和语义搜索
- 个性化检索（基于用户标签）
- 多种过滤条件支持
- 检索结果排序和评分

**Langflow集成：**
- 基于检索文档生成回答
- 上下文感知的答案生成
- 多轮对话支持
- 答案质量评估

**使用示例：**
```python
from agents.controllers import KnowledgeController

kb_controller = KnowledgeController()

# 查询知识库并生成回答
result = kb_controller.query_and_respond(
    query="笔记本电脑的保修期是多久？",
    user_id="user_12345",
    session_id="session_12345"
)

# 仅搜索知识库
search_result = kb_controller.search_knowledge_only(
    query="产品规格参数",
    top_k=5
)
```

**RAGFlow API调用流程：**
```python
# 1. 构造请求体
request_data = {
    'query': query,
    'top_k': 5,
    'include_metadata': True,
    'user_context': {
        'tags': ['price_sensitive', 'quality_focused']
    }
}

# 2. 发送请求
response = requests.post(
    f"{ragflow_config.base_url}/api/v1/retrieval",
    json=request_data,
    headers={'Authorization': f'Bearer {api_key}'}
)

# 3. 处理响应
documents = response.json()['documents']
for doc in documents:
    print(f"文档: {doc['title']}")
    print(f"内容: {doc['content']}")
    print(f"相似度: {doc['score']}")
```

### 5. 聊天数据入库 (ChatIngestor)

**数据处理流程：**
1. 对话内容分析（情感、关键词、意图）
2. 对话类型分类（话术/产品/服务/其他）
3. 知识点提取（问答对、实体、关系）
4. 质量评分和过滤
5. 分类存储到不同知识库

**支持的知识库类型：**
- 话术知识库：客服话术、应答模板
- 产品知识库：产品信息、规格参数
- 服务知识库：售后服务、常见问题

**使用示例：**
```python
from agents.controllers import ChatIngestionController

ingestion_controller = ChatIngestionController()

# 处理单个对话
conversation_data = {
    'conversation_id': 'conv_001',
    'user_id': 'user_001',
    'messages': [
        {'role': 'user', 'content': '你好，我想了解产品'},
        {'role': 'assistant', 'content': '您好！请问需要了解哪类产品？'}
    ],
    'created_at': timezone.now()
}

result = ingestion_controller.process_single_conversation(conversation_data)

# 批量入库
batch_result = ingestion_controller.batch_ingest_conversations([
    conversation_data1, conversation_data2, ...
])
```

## 异步任务

### 定时任务

**1. 每日对话数据入库**
```python
# 每天凌晨1点执行
@shared_task(bind=True, max_retries=3)
def daily_conversation_ingestion(self):
    """将昨天的对话数据批量写入知识库"""
    pass
```

**2. 数据清理任务**
```python
# 定时清理过期数据
@shared_task(bind=True, max_retries=2)
def cleanup_expired_data(self):
    """清理过期上下文、低权重标签、重复知识"""
    pass
```

### 批量处理任务

```python
# 批量处理对话
process_conversation_batch.delay(conversation_ids)

# 批量情感分析
analyze_user_sentiment_batch.delay(user_messages)

# 批量标签更新
update_user_tags_batch.delay(user_tag_updates)

# 知识库同步
knowledge_base_sync.delay(knowledge_items)
```

## 配置管理

### 环境变量配置

```python
# RAGFlow配置
RAGFLOW_BASE_URL = 'http://localhost:9380'
RAGFLOW_API_KEY = 'your_api_key'
RAGFLOW_TIMEOUT = 30

# Langflow配置
LANGFLOW_BASE_URL = 'http://localhost:7860'
LANGFLOW_API_KEY = 'your_api_key'
LANGFLOW_FLOW_ID = 'your_flow_id'

# 情感分析配置
SENTIMENT_MODEL_TYPE = 'snownlp'  # 'snownlp', 'transformers'
SENTIMENT_MODEL_NAME = 'bert-base-chinese'

# Redis配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 标签管理配置
TAG_DEFAULT_WEIGHT = 1.0
TAG_DECAY_FACTOR = 0.95
TAG_MAX_TAGS_PER_USER = 50
```

### 配置类使用

```python
from agents.services.config import get_ragflow_config, get_sentiment_config

# 获取RAGFlow配置
ragflow_config = get_ragflow_config()
print(f"RAGFlow URL: {ragflow_config.base_url}")

# 获取情感分析配置
sentiment_config = get_sentiment_config()
print(f"模型类型: {sentiment_config.model_type}")
```

## 综合处理流程

```python
from agents.controllers import ComprehensiveAgentController

controller = ComprehensiveAgentController()

# 处理用户消息的完整流程
result = controller.process_user_message(
    user_id="user_12345",
    session_id="session_12345",
    message="我想买一台笔记本电脑",
    enable_kb=True
)

# 处理步骤：
# 1. 情感分析
# 2. 标签分析和更新
# 3. 添加到上下文
# 4. 知识库查询
# 5. 生成回答
# 6. 更新上下文
```

## 部署和运行

### 1. 安装依赖

```bash
pip install django redis celery requests
pip install snownlp jieba transformers  # 可选
```

### 2. 配置Redis

```bash
# 启动Redis服务
redis-server

# 测试连接
redis-cli ping
```

### 3. 启动Celery

```bash
# 启动Celery Worker
celery -A your_project worker -l info

# 启动Celery Beat（定时任务）
celery -A your_project beat -l info
```

### 4. 运行示例

```python
# 在Django shell中运行
python manage.py shell

from agents.examples import run_all_examples
run_all_examples()
```

## 扩展和自定义

### 1. 添加新的情感分析模型

```python
class CustomSentimentAnalyzer(SentimentAnalyzer):
    def _load_model(self):
        # 加载自定义模型
        pass
    
    def _analyze_with_custom_model(self, text):
        # 自定义分析逻辑
        pass
```

### 2. 扩展标签分析规则

```python
class ExtendedTagManager(TagManager):
    def _predict_model_tags(self, message):
        # 添加更复杂的标签预测逻辑
        # 可以集成NLP模型、规则引擎等
        pass
```

### 3. 自定义知识库接口

```python
class CustomKBResponder(KBResponder):
    def query_knowledge_base(self, query, **kwargs):
        # 集成其他知识库系统
        # 如Elasticsearch、Milvus等
        pass
```

## 性能优化

### 1. 缓存策略
- Redis缓存用户标签和上下文
- 情感分析结果缓存
- 知识库查询结果缓存

### 2. 批量处理
- 异步任务处理大量数据
- 批量数据库操作
- 并发处理优化

### 3. 监控和日志
- 详细的日志记录
- 性能指标监控
- 错误追踪和报警

## 注意事项

1. **数据隐私**：确保用户数据的安全和隐私保护
2. **模型更新**：定期更新情感分析和标签预测模型
3. **资源管理**：合理配置Redis和数据库连接池
4. **错误处理**：完善的异常处理和重试机制
5. **扩展性**：模块化设计便于功能扩展和维护

## 联系和支持

如有问题或建议，请联系开发团队或查看项目文档。 