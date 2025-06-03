"""
情感判断智能体
基于用户消息内容和行为分析用户情感状态
"""

import re
import jieba
from typing import Dict, Any, List, Tuple
from datetime import datetime
import json

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

try:
    from snownlp import SnowNLP
    SNOWNLP_AVAILABLE = True
except ImportError:
    SNOWNLP_AVAILABLE = False

from .base_agent import BaseAgent


class SentimentAgent(BaseAgent):
    """情感判断智能体"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("sentiment_agent", config)
        
        # 初始化情感分析器
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # 中文情感词典
        self.positive_words = {
            '好', '棒', '不错', '满意', '喜欢', '开心', '高兴', '赞', '优秀', '完美',
            '太好了', '太棒了', '很好', '非常好', '特别好', '真好', '真棒', '真不错',
            '谢谢', '感谢', '惊喜', '超赞', '给力', '牛', '厉害', '优质', '精彩'
        }
        
        self.negative_words = {
            '差', '烂', '不好', '失望', '生气', '愤怒', '讨厌', '糟糕', '垃圾', '恶心',
            '太差了', '太烂了', '很差', '非常差', '特别差', '真差', '真烂', '真不好',
            '投诉', '退货', '退款', '问题', '麻烦', '坑爹', '黑心', '欺骗', '骗人'
        }
        
        self.neutral_words = {
            '一般', '还行', '凑合', '普通', '平常', '常规', '标准', '正常', '可以'
        }
        
        # 情感强度词
        self.intensity_modifiers = {
            '非常': 1.5, '特别': 1.5, '超级': 1.5, '极其': 1.8, '超': 1.3,
            '很': 1.2, '太': 1.4, '真': 1.2, '好': 1.1, '挺': 1.1,
            '有点': 0.8, '稍微': 0.7, '略': 0.7, '还': 0.9
        }
        
        # 否定词
        self.negation_words = {'不', '没', '无', '非', '未', '否', '别', '莫'}
        
        # 情感模式
        self.emotion_patterns = {
            'angry': [r'生气', r'愤怒', r'火大', r'气死了', r'烦死了'],
            'happy': [r'开心', r'高兴', r'快乐', r'爽', r'舒服'],
            'sad': [r'难过', r'伤心', r'郁闷', r'沮丧', r'失落'],
            'surprised': [r'惊讶', r'震惊', r'意外', r'没想到', r'想不到'],
            'worried': [r'担心', r'焦虑', r'紧张', r'不安', r'忧虑'],
            'satisfied': [r'满意', r'舒心', r'放心', r'安心', r'称心'],
            'disappointed': [r'失望', r'遗憾', r'可惜', r'无语', r'郁闷']
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['user_id', 'message']
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户消息并分析情感"""
        user_id = input_data['user_id']
        message = input_data['message']
        context = input_data.get('context', {})
        
        # 多种情感分析方法
        sentiment_results = {}
        
        # 1. 基于词典的中文情感分析
        chinese_sentiment = self._analyze_chinese_sentiment(message)
        sentiment_results['chinese'] = chinese_sentiment
        
        # 2. SnowNLP情感分析（如果可用）
        if SNOWNLP_AVAILABLE:
            snow_sentiment = self._analyze_with_snownlp(message)
            sentiment_results['snownlp'] = snow_sentiment
        
        # 3. VADER情感分析（如果可用）
        if VADER_AVAILABLE:
            vader_sentiment = self._analyze_with_vader(message)
            sentiment_results['vader'] = vader_sentiment
        
        # 4. 情感模式匹配
        emotion_patterns = self._match_emotion_patterns(message)
        sentiment_results['emotions'] = emotion_patterns
        
        # 5. 综合情感分析
        final_sentiment = self._combine_sentiment_results(sentiment_results)
        
        # 6. 上下文调整
        adjusted_sentiment = self._adjust_with_context(final_sentiment, context)
        
        result = {
            'user_id': user_id,
            'message': message,
            'sentiment': adjusted_sentiment,
            'detailed_results': sentiment_results,
            'confidence': self._calculate_confidence(sentiment_results),
            'analysis_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"Sentiment analysis for user {user_id}: {adjusted_sentiment['label']} ({adjusted_sentiment['score']:.2f})")
        
        return result
    
    def _analyze_chinese_sentiment(self, text: str) -> Dict[str, Any]:
        """基于中文词典的情感分析"""
        words = list(jieba.cut(text))
        
        positive_score = 0
        negative_score = 0
        intensity_multiplier = 1.0
        negation_flag = False
        
        for i, word in enumerate(words):
            # 检查强度修饰词
            if word in self.intensity_modifiers:
                intensity_multiplier = self.intensity_modifiers[word]
                continue
            
            # 检查否定词
            if word in self.negation_words:
                negation_flag = True
                continue
            
            # 计算情感分数
            if word in self.positive_words:
                score = 1.0 * intensity_multiplier
                if negation_flag:
                    negative_score += score
                else:
                    positive_score += score
            elif word in self.negative_words:
                score = 1.0 * intensity_multiplier
                if negation_flag:
                    positive_score += score
                else:
                    negative_score += score
            
            # 重置修饰符
            if word not in self.intensity_modifiers and word not in self.negation_words:
                intensity_multiplier = 1.0
                negation_flag = False
        
        # 计算最终分数
        total_score = positive_score + negative_score
        if total_score == 0:
            polarity = 0
            label = 'neutral'
        else:
            polarity = (positive_score - negative_score) / total_score
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
        
        return {
            'label': label,
            'score': polarity,
            'positive_score': positive_score,
            'negative_score': negative_score,
            'confidence': min(abs(polarity) + 0.3, 1.0)
        }
    
    def _analyze_with_snownlp(self, text: str) -> Dict[str, Any]:
        """使用SnowNLP进行情感分析"""
        try:
            s = SnowNLP(text)
            sentiment_score = s.sentiments
            
            if sentiment_score > 0.6:
                label = 'positive'
            elif sentiment_score < 0.4:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'label': label,
                'score': sentiment_score,
                'confidence': abs(sentiment_score - 0.5) * 2
            }
        except Exception as e:
            self.logger.error(f"SnowNLP analysis error: {e}")
            return {'label': 'neutral', 'score': 0.5, 'confidence': 0.0}
    
    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """使用VADER进行情感分析"""
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            compound = scores['compound']
            
            if compound >= 0.05:
                label = 'positive'
            elif compound <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'label': label,
                'score': compound,
                'detailed_scores': scores,
                'confidence': abs(compound)
            }
        except Exception as e:
            self.logger.error(f"VADER analysis error: {e}")
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}
    
    def _match_emotion_patterns(self, text: str) -> Dict[str, float]:
        """情感模式匹配"""
        emotions = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text))
                score += matches
            
            if score > 0:
                emotions[emotion] = min(score / len(patterns), 1.0)
        
        return emotions
    
    def _combine_sentiment_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """综合多种情感分析结果"""
        labels = []
        scores = []
        confidences = []
        
        # 收集所有结果
        for method, result in results.items():
            if method == 'emotions':
                continue
            
            if isinstance(result, dict) and 'label' in result:
                labels.append(result['label'])
                scores.append(result.get('score', 0))
                confidences.append(result.get('confidence', 0))
        
        if not labels:
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}
        
        # 投票决定最终标签
        from collections import Counter
        label_counts = Counter(labels)
        final_label = label_counts.most_common(1)[0][0]
        
        # 计算平均分数和置信度
        final_score = sum(scores) / len(scores) if scores else 0.0
        final_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'label': final_label,
            'score': final_score,
            'confidence': final_confidence,
            'emotions': results.get('emotions', {})
        }
    
    def _adjust_with_context(self, sentiment: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """基于上下文调整情感分析结果"""
        adjusted_sentiment = sentiment.copy()
        
        # 历史情感趋势
        if 'recent_sentiments' in context:
            recent_sentiments = context['recent_sentiments']
            if len(recent_sentiments) >= 3:
                # 检查情感急剧变化
                if all(s['label'] == 'negative' for s in recent_sentiments[-3:]):
                    if sentiment['label'] == 'neutral':
                        adjusted_sentiment['label'] = 'negative'
                        adjusted_sentiment['confidence'] *= 0.8
                
                elif all(s['label'] == 'positive' for s in recent_sentiments[-3:]):
                    if sentiment['label'] == 'neutral':
                        adjusted_sentiment['label'] = 'positive'
                        adjusted_sentiment['confidence'] *= 0.8
        
        # 会话阶段调整
        conversation_stage = context.get('conversation_stage', 'unknown')
        if conversation_stage == 'complaint_handling':
            # 投诉处理阶段，负面情感权重增加
            if sentiment['label'] == 'negative':
                adjusted_sentiment['confidence'] *= 1.2
        elif conversation_stage == 'order_confirmation':
            # 订单确认阶段，正面情感权重增加
            if sentiment['label'] == 'positive':
                adjusted_sentiment['confidence'] *= 1.2
        
        return adjusted_sentiment
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """计算整体置信度"""
        confidences = []
        
        for method, result in results.items():
            if method == 'emotions':
                continue
            
            if isinstance(result, dict) and 'confidence' in result:
                confidences.append(result['confidence'])
        
        if not confidences:
            return 0.0
        
        # 使用加权平均，更多方法同意的结果置信度更高
        return sum(confidences) / len(confidences)
    
    def analyze_sentiment_trend(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析情感趋势"""
        if not messages:
            return {'trend': 'stable', 'overall_sentiment': 'neutral'}
        
        sentiments = []
        for msg in messages:
            sentiment_data = msg.get('sentiment', {})
            if sentiment_data:
                sentiments.append(sentiment_data)
        
        if len(sentiments) < 2:
            return {'trend': 'insufficient_data', 'overall_sentiment': 'neutral'}
        
        # 计算趋势
        recent_scores = [s.get('score', 0) for s in sentiments[-5:]]
        early_scores = [s.get('score', 0) for s in sentiments[:5]]
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        early_avg = sum(early_scores) / len(early_scores)
        
        if recent_avg - early_avg > 0.2:
            trend = 'improving'
        elif early_avg - recent_avg > 0.2:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # 整体情感
        all_scores = [s.get('score', 0) for s in sentiments]
        overall_avg = sum(all_scores) / len(all_scores)
        
        if overall_avg > 0.1:
            overall_sentiment = 'positive'
        elif overall_avg < -0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'trend': trend,
            'overall_sentiment': overall_sentiment,
            'overall_score': overall_avg,
            'trend_score': recent_avg - early_avg,
            'sentiment_count': len(sentiments)
        }
    
    def get_emotion_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取情感总结"""
        emotion_counts = {}
        total_messages = len(messages)
        
        for msg in messages:
            sentiment_data = msg.get('sentiment', {})
            emotions = sentiment_data.get('emotions', {})
            
            for emotion, score in emotions.items():
                if score > 0.5:  # 只统计高置信度的情感
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 计算情感分布
        emotion_distribution = {
            emotion: count / total_messages if total_messages > 0 else 0
            for emotion, count in emotion_counts.items()
        }
        
        # 找出主导情感
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
        
        return {
            'total_messages': total_messages,
            'emotion_counts': emotion_counts,
            'emotion_distribution': emotion_distribution,
            'dominant_emotion': dominant_emotion
        } 