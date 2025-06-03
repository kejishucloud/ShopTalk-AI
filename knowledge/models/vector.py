"""向量模型"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class KnowledgeVector:
    id: str
    content_id: str
    content_type: str
    text_chunk: str
    vector_data: List[float]
    knowledge_base_id: str = ""
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now() 