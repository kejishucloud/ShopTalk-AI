import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.db.models import Q, Count, F
from django.core.cache import cache

from .models import Keyword, KeywordCategory, KeywordRule, KeywordMatch
from apps.sentiment.models import SentimentAnalysis

logger = logging.getLogger(__name__)


class KeywordMatchingService:
    """关键词匹配服务"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5分钟缓存
    
    def check_human_handoff(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """检查是否需要人工介入"""
        try:
            # 获取人工介入关键词
            handoff_keywords = self._get_cached_keywords('human_handoff')
            
            matched_keywords = []
            total_confidence = 0.0
            
            for keyword in handoff_keywords:
                match_result = self._match_keyword(keyword, text)
                if match_result['is_match'] and match_result['confidence'] >= threshold:
                    matched_keywords.append({
                        'keyword_id': keyword.id,
                        'word': keyword.word,
                        'confidence': match_result['confidence'],
                        'priority_level': keyword.priority_level,
                        'category': keyword.category.name if keyword.category else None
                    })
                    total_confidence += match_result['confidence']
            
            # 计算整体置信度
            overall_confidence = min(total_confidence, 1.0) if matched_keywords else 0.0
            need_handoff = overall_confidence >= threshold and len(matched_keywords) > 0
            
            return {
                'need_human_handoff': need_handoff,
                'confidence': overall_confidence,
                'matched_keywords': matched_keywords,
                'threshold': threshold,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Human handoff check failed: {e}")
            return {
                'need_human_handoff': False,
                'confidence': 0.0,
                'matched_keywords': [],
                'error': str(e)
            }
    
    def check_sentiment_keywords(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """检查情感关键词"""
        try:
            # 获取情感关键词
            sentiment_keywords = self._get_cached_keywords('sentiment')
            
            positive_matches = []
            negative_matches = []
            neutral_matches = []
            
            for keyword in sentiment_keywords:
                match_result = self._match_keyword(keyword, text)
                if match_result['is_match'] and match_result['confidence'] >= threshold:
                    match_info = {
                        'keyword_id': keyword.id,
                        'word': keyword.word,
                        'confidence': match_result['confidence'],
                        'weight': keyword.weight
                    }
                    
                    # 根据关键词情感分类
                    if hasattr(keyword, 'sentiment_type'):
                        if keyword.sentiment_type == 'positive':
                            positive_matches.append(match_info)
                        elif keyword.sentiment_type == 'negative':
                            negative_matches.append(match_info)
                        else:
                            neutral_matches.append(match_info)
                    else:
                        neutral_matches.append(match_info)
            
            # 计算情感得分
            positive_score = sum(m['confidence'] * m['weight'] for m in positive_matches)
            negative_score = sum(m['confidence'] * m['weight'] for m in negative_matches)
            
            # 确定整体情感
            if positive_score > negative_score:
                overall_sentiment = 'positive'
                sentiment_confidence = positive_score / (positive_score + negative_score + 0.1)
            elif negative_score > positive_score:
                overall_sentiment = 'negative'
                sentiment_confidence = negative_score / (positive_score + negative_score + 0.1)
            else:
                overall_sentiment = 'neutral'
                sentiment_confidence = 0.5
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_confidence': sentiment_confidence,
                'positive_matches': positive_matches,
                'negative_matches': negative_matches,
                'neutral_matches': neutral_matches,
                'positive_score': positive_score,
                'negative_score': negative_score,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment keyword check failed: {e}")
            return {
                'overall_sentiment': 'neutral',
                'sentiment_confidence': 0.0,
                'error': str(e)
            }
    
    def classify_text(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """文本分类"""
        try:
            # 获取分类关键词
            category_keywords = self._get_cached_keywords('category')
            
            category_scores = {}
            matched_keywords = []
            
            for keyword in category_keywords:
                match_result = self._match_keyword(keyword, text)
                if match_result['is_match'] and match_result['confidence'] >= threshold:
                    category_name = keyword.category.name if keyword.category else 'uncategorized'
                    
                    if category_name not in category_scores:
                        category_scores[category_name] = []
                    
                    match_info = {
                        'keyword_id': keyword.id,
                        'word': keyword.word,
                        'confidence': match_result['confidence'],
                        'weight': keyword.weight,
                        'category': category_name
                    }
                    
                    category_scores[category_name].append(match_info)
                    matched_keywords.append(match_info)
            
            # 计算每个分类的总分
            category_totals = {}
            for category, matches in category_scores.items():
                total_score = sum(m['confidence'] * m['weight'] for m in matches)
                category_totals[category] = {
                    'score': total_score,
                    'matches': matches,
                    'count': len(matches)
                }
            
            # 找出最可能的分类
            predicted_category = None
            max_score = 0.0
            
            if category_totals:
                predicted_category = max(category_totals.keys(), key=lambda k: category_totals[k]['score'])
                max_score = category_totals[predicted_category]['score']
            
            return {
                'predicted_category': predicted_category,
                'confidence': min(max_score, 1.0),
                'category_scores': category_totals,
                'matched_keywords': matched_keywords,
                'threshold': threshold,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Text classification failed: {e}")
            return {
                'predicted_category': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def match_all_types(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """全类型关键词匹配"""
        try:
            handoff_result = self.check_human_handoff(text, threshold)
            sentiment_result = self.check_sentiment_keywords(text, threshold)
            classification_result = self.classify_text(text, threshold)
            
            return {
                'human_handoff': handoff_result,
                'sentiment_analysis': sentiment_result,
                'text_classification': classification_result,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Full keyword matching failed: {e}")
            return {'error': str(e)}
    
    def test_keyword_match(self, keyword: Keyword, text: str) -> Dict[str, Any]:
        """测试单个关键词匹配"""
        return self._match_keyword(keyword, text)
    
    def _match_keyword(self, keyword: Keyword, text: str) -> Dict[str, Any]:
        """执行关键词匹配"""
        try:
            word = keyword.word.lower()
            text_lower = text.lower()
            
            # 精确匹配
            exact_match = word in text_lower
            
            # 正则匹配
            regex_match = False
            if hasattr(keyword, 'regex_pattern') and keyword.regex_pattern:
                try:
                    regex_match = bool(re.search(keyword.regex_pattern, text, re.IGNORECASE))
                except re.error:
                    regex_match = False
            
            # 模糊匹配（简单的字符相似度）
            fuzzy_confidence = self._calculate_fuzzy_similarity(word, text_lower)
            
            # 综合判断
            is_match = exact_match or regex_match or fuzzy_confidence > 0.8
            
            # 计算置信度
            if exact_match:
                confidence = 1.0
            elif regex_match:
                confidence = 0.9
            else:
                confidence = fuzzy_confidence
            
            # 根据关键词配置调整置信度
            confidence *= (keyword.weight / 10.0)  # 权重调整
            confidence = min(confidence, 1.0)
            
            return {
                'is_match': is_match,
                'confidence': confidence,
                'details': {
                    'exact_match': exact_match,
                    'regex_match': regex_match,
                    'fuzzy_confidence': fuzzy_confidence,
                    'weight_adjusted': confidence
                }
            }
            
        except Exception as e:
            logger.error(f"Keyword matching error: {e}")
            return {
                'is_match': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_fuzzy_similarity(self, word: str, text: str) -> float:
        """计算模糊相似度"""
        if word in text:
            return 1.0
        
        # 简单的字符匹配算法
        word_chars = set(word)
        text_chars = set(text)
        
        if not word_chars:
            return 0.0
        
        common_chars = word_chars.intersection(text_chars)
        similarity = len(common_chars) / len(word_chars)
        
        return similarity
    
    def _get_cached_keywords(self, keyword_type: str) -> List[Keyword]:
        """获取缓存的关键词"""
        cache_key = f"keywords_{keyword_type}"
        keywords = cache.get(cache_key)
        
        if keywords is None:
            keywords = list(Keyword.objects.filter(
                keyword_type=keyword_type,
                is_active=True
            ).select_related('category').order_by('-priority_level', '-weight'))
            
            cache.set(cache_key, keywords, self.cache_timeout)
        
        return keywords


class SentimentAnalysisService:
    """情感分析服务"""
    
    def __init__(self):
        self.keyword_service = KeywordMatchingService()
    
    def analyze_sentiment(self, text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """分析文本情感"""
        try:
            # 使用关键词匹配进行情感分析
            keyword_result = self.keyword_service.check_sentiment_keywords(text)
            
            # 创建分析记录
            if user_id:
                sentiment_record = SentimentAnalysis.objects.create(
                    text=text[:500],  # 限制长度
                    sentiment_label=keyword_result['overall_sentiment'],
                    confidence=keyword_result['sentiment_confidence'],
                    analysis_method='keyword_matching',
                    raw_result=keyword_result,
                    analyzed_by_id=user_id
                )
                
                result = {
                    'analysis_id': sentiment_record.id,
                    'sentiment': keyword_result['overall_sentiment'],
                    'confidence': keyword_result['sentiment_confidence'],
                    'details': keyword_result,
                    'created_at': sentiment_record.created_at.isoformat()
                }
            else:
                result = {
                    'sentiment': keyword_result['overall_sentiment'],
                    'confidence': keyword_result['sentiment_confidence'],
                    'details': keyword_result
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_sentiment_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户情感分析历史"""
        try:
            analyses = SentimentAnalysis.objects.filter(
                analyzed_by_id=user_id
            ).order_by('-created_at')[:limit]
            
            return [{
                'id': analysis.id,
                'text': analysis.text,
                'sentiment': analysis.sentiment_label,
                'confidence': analysis.confidence,
                'created_at': analysis.created_at.isoformat()
            } for analysis in analyses]
            
        except Exception as e:
            logger.error(f"Get sentiment history failed: {e}")
            return [] 