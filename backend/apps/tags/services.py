"""
标签管理服务模块
提供标签匹配、推荐等业务逻辑
"""

import re
import logging
from typing import List, Tuple, Dict, Any
from django.db.models import Q
from .models import TagRule, Tag

logger = logging.getLogger(__name__)


class TagMatchingService:
    """标签匹配服务"""
    
    def __init__(self):
        self.cached_rules = None
        self.cache_timestamp = None
    
    def _get_active_rules(self):
        """获取活跃的标签规则"""
        # 简单缓存机制，避免频繁数据库查询
        import time
        current_time = time.time()
        
        if (self.cached_rules is None or 
            self.cache_timestamp is None or 
            current_time - self.cache_timestamp > 300):  # 5分钟缓存
            
            self.cached_rules = list(
                TagRule.objects.filter(is_active=True)
                .prefetch_related('target_tags')
                .order_by('-priority')
            )
            self.cache_timestamp = current_time
        
        return self.cached_rules
    
    def match_text(self, text: str) -> List[Tuple[TagRule, float]]:
        """
        匹配文本并返回匹配的规则和置信度
        
        Args:
            text: 待匹配的文本
            
        Returns:
            List[Tuple[TagRule, float]]: 匹配的规则和置信度列表
        """
        if not text or not text.strip():
            return []
        
        text = text.strip().lower()
        matched_rules = []
        
        try:
            rules = self._get_active_rules()
            
            for rule in rules:
                confidence = self._calculate_rule_confidence(rule, text)
                if confidence > 0:
                    matched_rules.append((rule, confidence))
            
            # 按置信度排序
            matched_rules.sort(key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"文本匹配失败: {str(e)}")
        
        return matched_rules
    
    def _calculate_rule_confidence(self, rule: TagRule, text: str) -> float:
        """
        计算规则匹配的置信度
        
        Args:
            rule: 标签规则
            text: 待匹配文本
            
        Returns:
            float: 置信度 (0-1)
        """
        try:
            if rule.rule_type == 'keyword':
                return self._match_keywords(rule.conditions, text)
            elif rule.rule_type == 'pattern':
                return self._match_pattern(rule.conditions, text)
            elif rule.rule_type == 'intent':
                return self._match_intent(rule.conditions, text)
            elif rule.rule_type == 'sentiment':
                return self._match_sentiment(rule.conditions, text)
            else:
                logger.warning(f"未知的规则类型: {rule.rule_type}")
                return 0.0
        except Exception as e:
            logger.error(f"规则匹配失败 (rule_id={rule.id}): {str(e)}")
            return 0.0
    
    def _match_keywords(self, conditions: Dict[str, Any], text: str) -> float:
        """关键词匹配"""
        keywords = conditions.get('keywords', [])
        if not keywords:
            return 0.0
        
        matched_count = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if isinstance(keyword, str) and keyword.lower() in text:
                matched_count += 1
        
        # 基础匹配率
        match_ratio = matched_count / total_keywords
        
        # 考虑匹配强度（可选）
        match_mode = conditions.get('match_mode', 'any')  # any, all
        if match_mode == 'all' and matched_count < total_keywords:
            return 0.0
        elif match_mode == 'any' and matched_count == 0:
            return 0.0
        
        return min(match_ratio, 1.0)
    
    def _match_pattern(self, conditions: Dict[str, Any], text: str) -> float:
        """正则表达式匹配"""
        pattern = conditions.get('pattern', '')
        if not pattern:
            return 0.0
        
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 可以根据匹配的复杂度调整置信度
                return 1.0
            return 0.0
        except re.error as e:
            logger.error(f"正则表达式错误: {pattern}, {str(e)}")
            return 0.0
    
    def _match_intent(self, conditions: Dict[str, Any], text: str) -> float:
        """意图匹配（简化版，实际应该调用NLP服务）"""
        # 这里是简化实现，实际应该调用意图识别服务
        intent_keywords = conditions.get('intent_keywords', [])
        if not intent_keywords:
            return 0.0
        
        # 简单的关键词匹配作为意图识别的替代
        matched = any(keyword.lower() in text for keyword in intent_keywords)
        return 0.8 if matched else 0.0
    
    def _match_sentiment(self, conditions: Dict[str, Any], text: str) -> float:
        """情感匹配（简化版，实际应该调用情感分析服务）"""
        # 这里是简化实现，实际应该调用情感分析服务
        target_sentiment = conditions.get('sentiment', 'neutral')
        
        # 简单的情感关键词匹配
        positive_words = ['好', '不错', '满意', '喜欢', '推荐', '优秀']
        negative_words = ['差', '不好', '失望', '讨厌', '糟糕', '问题']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if target_sentiment == 'positive' and positive_count > negative_count:
            return 0.7
        elif target_sentiment == 'negative' and negative_count > positive_count:
            return 0.7
        elif target_sentiment == 'neutral' and positive_count == negative_count:
            return 0.5
        
        return 0.0
    
    def recommend_tags(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        推荐标签
        
        Args:
            text: 文本内容
            limit: 推荐数量限制
            
        Returns:
            List[Dict]: 推荐的标签信息
        """
        matched_rules = self.match_text(text)
        
        # 收集所有推荐的标签
        tag_scores = {}
        
        for rule, confidence in matched_rules:
            for tag in rule.target_tags.all():
                if tag.is_active:
                    # 累计分数，考虑规则优先级
                    score = confidence * (rule.priority + 1) / 10
                    tag_scores[tag.id] = tag_scores.get(tag.id, 0) + score
        
        # 排序并返回top N
        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for tag_id, score in sorted_tags[:limit]:
            try:
                tag = Tag.objects.get(id=tag_id)
                result.append({
                    'tag_id': tag.id,
                    'tag_name': tag.name,
                    'category': tag.category.name,
                    'color': tag.color,
                    'confidence': min(score, 1.0)
                })
            except Tag.DoesNotExist:
                continue
        
        return result
    
    def batch_match(self, texts: List[str]) -> Dict[str, List[Tuple[TagRule, float]]]:
        """
        批量匹配文本
        
        Args:
            texts: 文本列表
            
        Returns:
            Dict: 每个文本的匹配结果
        """
        results = {}
        for i, text in enumerate(texts):
            results[f"text_{i}"] = self.match_text(text)
        return results
    
    def clear_cache(self):
        """清除缓存"""
        self.cached_rules = None
        self.cache_timestamp = None


class TagRecommendationService:
    """标签推荐服务"""
    
    def __init__(self):
        self.matching_service = TagMatchingService()
    
    def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门标签"""
        from django.db.models import Count
        
        popular_tags = (
            Tag.objects
            .filter(is_active=True)
            .annotate(usage_count=Count('tagassignment'))
            .order_by('-usage_count')[:limit]
        )
        
        return [
            {
                'tag_id': tag.id,
                'tag_name': tag.name,
                'category': tag.category.name,
                'color': tag.color,
                'usage_count': tag.usage_count
            }
            for tag in popular_tags
        ]
    
    def get_related_tags(self, tag_ids: List[int], limit: int = 5) -> List[Dict[str, Any]]:
        """获取相关标签"""
        # 这里可以基于共现频率、语义相似度等计算相关标签
        # 简化实现：返回同分类下的其他标签
        from django.db.models import Q
        
        if not tag_ids:
            return []
        
        # 获取指定标签的分类
        categories = Tag.objects.filter(id__in=tag_ids).values_list('category_id', flat=True)
        
        # 找到同分类下的其他标签
        related_tags = (
            Tag.objects
            .filter(category_id__in=categories, is_active=True)
            .exclude(id__in=tag_ids)[:limit]
        )
        
        return [
            {
                'tag_id': tag.id,
                'tag_name': tag.name,
                'category': tag.category.name,
                'color': tag.color
            }
            for tag in related_tags
        ] 