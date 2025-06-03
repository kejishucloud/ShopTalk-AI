"""FAQ模型"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class FAQ:
    id: str
    question: str
    answer: str
    knowledge_base_id: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now() 