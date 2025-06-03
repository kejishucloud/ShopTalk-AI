"""
ShopTalk-AI 知识库模块
=====================

知识库模块提供企业级的知识内容管理、智能检索、自动化处理等功能。

主要功能模块：
- models: 数据模型定义
- services: 业务逻辑服务
- api: API接口
- storage: 存储引擎
- search: 搜索引擎

支持的知识类型：
- 文档 (Documents)
- FAQ (常见问题)
- 商品信息 (Products)
- 话术模板 (Scripts)
- 政策文档 (Policies)
- 技术文档 (Technical)
"""

from .models import (
    KnowledgeBase,
    Document,
    FAQ,
    Product,
    Script,
    KnowledgeVector
)

from .services import (
    KnowledgeService,
    DocumentService,
    FAQService,
    ProductService,
    ScriptService,
    VectorService,
    SearchService
)

from .api import (
    KnowledgeAPI,
    DocumentAPI,
    FAQAPI,
    ProductAPI,
    ScriptAPI
)

__version__ = '1.0.0'
__author__ = 'ShopTalk-AI Team'

__all__ = [
    # Models
    'KnowledgeBase',
    'Document',
    'FAQ',
    'Product',
    'Script',
    'KnowledgeVector',
    
    # Services
    'KnowledgeService',
    'DocumentService',
    'FAQService',
    'ProductService',
    'ScriptService',
    'VectorService',
    'SearchService',
    
    # APIs
    'KnowledgeAPI',
    'DocumentAPI',
    'FAQAPI',
    'ProductAPI',
    'ScriptAPI',
] 