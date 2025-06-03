"""
知识库数据模型
==============

定义知识库相关的数据模型和结构。
"""

from .knowledge_base import KnowledgeBase
from .document import Document
from .faq import FAQ
from .product import Product
from .script import Script
from .vector import KnowledgeVector

__all__ = [
    'KnowledgeBase',
    'Document', 
    'FAQ',
    'Product',
    'Script',
    'KnowledgeVector',
] 