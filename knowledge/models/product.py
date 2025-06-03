"""商品模型"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Product:
    id: str
    name: str
    description: str = ""
    price: float = 0.0
    knowledge_base_id: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now() 