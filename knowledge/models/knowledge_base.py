"""
知识库基础模型
==============

定义知识库的基础数据结构。
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class KnowledgeType(Enum):
    """知识库类型枚举"""
    PRODUCT = "product"
    FAQ = "faq"
    SCRIPT = "script"
    POLICY = "policy"
    TECHNICAL = "technical"
    TRAINING = "training"
    CUSTOM = "custom"


class AccessLevel(Enum):
    """访问级别枚举"""
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    PRIVATE = "private"


@dataclass
class KnowledgeBase:
    """知识库数据模型"""
    
    id: str
    name: str
    knowledge_type: KnowledgeType
    description: str = ""
    access_level: AccessLevel = AccessLevel.INTERNAL
    is_active: bool = True
    enable_version_control: bool = True
    enable_ai_enhancement: bool = True
    auto_extract_keywords: bool = True
    
    # 统计信息
    total_documents: int = 0
    total_qa_pairs: int = 0
    total_views: int = 0
    
    # 配置信息
    embedding_model: str = ""
    search_config: Dict[str, Any] = None
    permissions: Dict[str, Any] = None
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = ""
    
    def __post_init__(self):
        if self.search_config is None:
            self.search_config = {}
        if self.permissions is None:
            self.permissions = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'knowledge_type': self.knowledge_type.value,
            'description': self.description,
            'access_level': self.access_level.value,
            'is_active': self.is_active,
            'enable_version_control': self.enable_version_control,
            'enable_ai_enhancement': self.enable_ai_enhancement,
            'auto_extract_keywords': self.auto_extract_keywords,
            'total_documents': self.total_documents,
            'total_qa_pairs': self.total_qa_pairs,
            'total_views': self.total_views,
            'embedding_model': self.embedding_model,
            'search_config': self.search_config,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeBase':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            name=data['name'],
            knowledge_type=KnowledgeType(data['knowledge_type']),
            description=data.get('description', ''),
            access_level=AccessLevel(data.get('access_level', 'internal')),
            is_active=data.get('is_active', True),
            enable_version_control=data.get('enable_version_control', True),
            enable_ai_enhancement=data.get('enable_ai_enhancement', True),
            auto_extract_keywords=data.get('auto_extract_keywords', True),
            total_documents=data.get('total_documents', 0),
            total_qa_pairs=data.get('total_qa_pairs', 0),
            total_views=data.get('total_views', 0),
            embedding_model=data.get('embedding_model', ''),
            search_config=data.get('search_config', {}),
            permissions=data.get('permissions', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            created_by=data.get('created_by', ''),
        ) 