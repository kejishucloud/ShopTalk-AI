# -*- coding: utf-8 -*-

"""
提示词管理模块
将所有智能体的提示词统一管理，与智能体逻辑分离
"""

from .chat_prompts import ChatPrompts
from .knowledge_prompts import KnowledgePrompts
from .sentiment_prompts import SentimentPrompts
from .memory_prompts import MemoryPrompts
from .tag_prompts import TagPrompts

__all__ = [
    'ChatPrompts',
    'KnowledgePrompts', 
    'SentimentPrompts',
    'MemoryPrompts',
    'TagPrompts'
]
