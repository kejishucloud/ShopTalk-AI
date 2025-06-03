"""知识库服务模块"""

from .knowledge_service import KnowledgeService
from .search_service import SearchService
from .vector_service import VectorService

# 基础服务类
class DocumentService:
    pass

class FAQService:
    pass

class ProductService:
    pass

class ScriptService:
    pass

__all__ = [
    'KnowledgeService',
    'DocumentService',
    'FAQService', 
    'ProductService',
    'ScriptService',
    'VectorService',
    'SearchService',
] 