"""
文本处理工具函数
提供文本清洗、分词、关键词提取、相似度计算等功能
"""

import re
import jieba
import logging
from typing import List, Dict, Tuple, Set
from collections import Counter
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# 停用词列表
STOP_WORDS = {
    '的', '了', '和', '是', '在', '有', '我', '你', '他', '她', '它', '们', '这', '那',
    '一个', '一些', '什么', '怎么', '为什么', '哪里', '什么时候', '如何', '可以', '能够',
    '应该', '需要', '想要', '希望', '觉得', '认为', '知道', '明白', '理解', '看到',
    '听到', '说', '讲', '告诉', '问', '回答', '解释', '描述', '介绍', '展示',
    '但是', '然而', '不过', '虽然', '尽管', '因为', '所以', '因此', '由于', '如果',
    '假如', '要是', '除非', '无论', '不管', '无论如何', '总之', '总的来说', '一般来说'
}


def clean_text(text: str) -> str:
    """清洗文本
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符，保留中文、英文、数字和基本标点
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,!?;:()（）。，！？；：]', '', text)
    
    # 移除连续的标点符号
    text = re.sub(r'[.,!?;:]{2,}', '.', text)
    
    return text.strip()


def segment_text(text: str, use_jieba: bool = True) -> List[str]:
    """文本分词
    
    Args:
        text: 待分词的文本
        use_jieba: 是否使用jieba分词
        
    Returns:
        List[str]: 分词结果
    """
    if not text:
        return []
    
    # 清洗文本
    cleaned_text = clean_text(text)
    
    if use_jieba:
        # 使用jieba分词
        words = list(jieba.cut(cleaned_text))
    else:
        # 简单的空格分词
        words = cleaned_text.split()
    
    # 过滤停用词和短词
    filtered_words = [
        word.strip() for word in words
        if word.strip() and len(word.strip()) > 1 and word.strip() not in STOP_WORDS
    ]
    
    return filtered_words


def extract_keywords(text: str, top_k: int = 10, min_freq: int = 1) -> List[Tuple[str, int]]:
    """提取关键词
    
    Args:
        text: 文本内容
        top_k: 返回前k个关键词
        min_freq: 最小词频
        
    Returns:
        List[Tuple[str, int]]: 关键词及其频次列表
    """
    if not text:
        return []
    
    # 分词
    words = segment_text(text)
    
    if not words:
        return []
    
    # 统计词频
    word_count = Counter(words)
    
    # 过滤低频词
    filtered_words = {
        word: count for word, count in word_count.items()
        if count >= min_freq
    }
    
    # 按频次排序
    sorted_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_words[:top_k]


def calculate_text_similarity(text1: str, text2: str, method: str = 'sequence') -> float:
    """计算文本相似度
    
    Args:
        text1: 文本1
        text2: 文本2
        method: 相似度计算方法 ('sequence', 'jaccard', 'cosine')
        
    Returns:
        float: 相似度分数 (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    if method == 'sequence':
        return _sequence_similarity(text1, text2)
    elif method == 'jaccard':
        return _jaccard_similarity(text1, text2)
    elif method == 'cosine':
        return _cosine_text_similarity(text1, text2)
    else:
        logger.warning(f"未知的相似度计算方法: {method}，使用默认方法")
        return _sequence_similarity(text1, text2)


def _sequence_similarity(text1: str, text2: str) -> float:
    """基于序列匹配的相似度"""
    return SequenceMatcher(None, text1, text2).ratio()


def _jaccard_similarity(text1: str, text2: str) -> float:
    """基于Jaccard系数的相似度"""
    words1 = set(segment_text(text1))
    words2 = set(segment_text(text2))
    
    if not words1 and not words2:
        return 1.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def _cosine_text_similarity(text1: str, text2: str) -> float:
    """基于余弦相似度的文本相似度"""
    words1 = segment_text(text1)
    words2 = segment_text(text2)
    
    if not words1 or not words2:
        return 0.0
    
    # 构建词汇表
    vocabulary = set(words1 + words2)
    
    # 构建词频向量
    vector1 = [words1.count(word) for word in vocabulary]
    vector2 = [words2.count(word) for word in vocabulary]
    
    # 计算余弦相似度
    dot_product = sum(a * b for a, b in zip(vector1, vector2))
    magnitude1 = sum(a * a for a in vector1) ** 0.5
    magnitude2 = sum(b * b for b in vector2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def extract_entities(text: str) -> Dict[str, List[str]]:
    """提取命名实体
    
    Args:
        text: 文本内容
        
    Returns:
        Dict[str, List[str]]: 实体类型及其实体列表
    """
    entities = {
        'products': [],
        'brands': [],
        'prices': [],
        'dates': [],
        'locations': []
    }
    
    # 简单的正则表达式实体识别
    # 价格识别
    price_pattern = r'(\d+(?:\.\d+)?)\s*(?:元|块|万|千|百)'
    prices = re.findall(price_pattern, text)
    entities['prices'] = [f"{price}元" for price in prices]
    
    # 日期识别
    date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|今天|明天|昨天|下周|上周)'
    dates = re.findall(date_pattern, text)
    entities['dates'] = dates
    
    # 品牌识别（示例）
    brand_keywords = ['苹果', '华为', '小米', '三星', '联想', '戴尔', '惠普']
    for brand in brand_keywords:
        if brand in text:
            entities['brands'].append(brand)
    
    return entities


def detect_intent(text: str) -> Dict[str, float]:
    """检测用户意图
    
    Args:
        text: 用户输入文本
        
    Returns:
        Dict[str, float]: 意图及其置信度
    """
    intents = {
        'greeting': 0.0,
        'question': 0.0,
        'complaint': 0.0,
        'purchase': 0.0,
        'consultation': 0.0,
        'goodbye': 0.0
    }
    
    # 简单的关键词匹配意图识别
    intent_keywords = {
        'greeting': ['你好', '您好', '早上好', '下午好', '晚上好', '嗨', 'hello', 'hi'],
        'question': ['什么', '怎么', '为什么', '哪里', '什么时候', '如何', '?', '？'],
        'complaint': ['投诉', '问题', '不满意', '差评', '退货', '退款', '故障', '坏了'],
        'purchase': ['购买', '买', '下单', '付款', '订单', '支付', '价格', '多少钱'],
        'consultation': ['咨询', '询问', '了解', '请问', '想知道', '能否', '可以'],
        'goodbye': ['再见', '拜拜', '谢谢', '感谢', 'bye', 'goodbye', '结束']
    }
    
    text_lower = text.lower()
    
    for intent, keywords in intent_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        if matches > 0:
            intents[intent] = min(matches / len(keywords), 1.0)
    
    return intents


def summarize_text(text: str, max_length: int = 100) -> str:
    """文本摘要
    
    Args:
        text: 原始文本
        max_length: 摘要最大长度
        
    Returns:
        str: 文本摘要
    """
    if not text or len(text) <= max_length:
        return text
    
    # 简单的摘要策略：提取关键句子
    sentences = re.split(r'[。！？.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return text[:max_length] + "..."
    
    # 选择最长的句子作为摘要
    best_sentence = max(sentences, key=len)
    
    if len(best_sentence) <= max_length:
        return best_sentence
    else:
        return best_sentence[:max_length] + "..."


def validate_text_quality(text: str) -> Dict[str, Any]:
    """验证文本质量
    
    Args:
        text: 待验证的文本
        
    Returns:
        Dict[str, Any]: 质量评估结果
    """
    quality_metrics = {
        'length': len(text) if text else 0,
        'word_count': len(segment_text(text)) if text else 0,
        'has_chinese': bool(re.search(r'[\u4e00-\u9fa5]', text)) if text else False,
        'has_english': bool(re.search(r'[a-zA-Z]', text)) if text else False,
        'has_numbers': bool(re.search(r'\d', text)) if text else False,
        'special_char_ratio': 0.0,
        'quality_score': 0.0
    }
    
    if not text:
        return quality_metrics
    
    # 计算特殊字符比例
    special_chars = len(re.findall(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', text))
    quality_metrics['special_char_ratio'] = special_chars / len(text)
    
    # 计算质量分数
    score = 0.0
    
    # 长度分数
    if 10 <= quality_metrics['length'] <= 500:
        score += 0.3
    elif quality_metrics['length'] > 5:
        score += 0.1
    
    # 词汇数量分数
    if quality_metrics['word_count'] >= 3:
        score += 0.3
    elif quality_metrics['word_count'] >= 1:
        score += 0.1
    
    # 语言多样性分数
    if quality_metrics['has_chinese']:
        score += 0.2
    if quality_metrics['has_english']:
        score += 0.1
    
    # 特殊字符惩罚
    if quality_metrics['special_char_ratio'] < 0.1:
        score += 0.1
    elif quality_metrics['special_char_ratio'] > 0.3:
        score -= 0.2
    
    quality_metrics['quality_score'] = max(0.0, min(1.0, score))
    
    return quality_metrics 