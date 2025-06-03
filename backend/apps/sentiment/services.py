"""
情感分析服务
支持多种AI模型进行情感分析
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from .models import SentimentAnalysis, EmotionKeyword

logger = logging.getLogger('sentiment')


class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self, model_type: str = 'transformer'):
        self.model_type = model_type
        self.config = settings.SENTIMENT_ANALYSIS
        self.confidence_threshold = self.config.get('CONFIDENCE_THRESHOLD', 0.7)
        
    def analyze(self, text: str, user_id: Optional[int] = None, 
                platform: str = '', conversation_id: str = '') -> Dict:
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            user_id: 用户ID
            platform: 平台名称
            conversation_id: 对话ID
            
        Returns:
            情感分析结果
        """
        try:
            # 检查缓存
            if self.config.get('CACHE_RESULTS', True):
                cache_key = f"sentiment:{hash(text)}:{self.model_type}"
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.debug(f"使用缓存的情感分析结果: {text[:50]}")
                    return cached_result
            
            # 预处理文本
            cleaned_text = self._preprocess_text(text)
            
            # 执行情感分析
            if self.model_type == 'transformer':
                result = self._analyze_with_transformer(cleaned_text)
            elif self.model_type == 'baidu':
                result = self._analyze_with_baidu(cleaned_text)
            elif self.model_type == 'tencent':
                result = self._analyze_with_tencent(cleaned_text)
            elif self.model_type == 'openai':
                result = self._analyze_with_openai(cleaned_text)
            else:
                result = self._analyze_with_keywords(cleaned_text)
            
            # 保存结果到数据库
            if result['confidence'] >= self.confidence_threshold:
                self._save_analysis_result(
                    text, result, user_id, platform, conversation_id
                )
            
            # 缓存结果
            if self.config.get('CACHE_RESULTS', True):
                cache_timeout = self.config.get('CACHE_TIMEOUT', 3600)
                cache.set(cache_key, result, cache_timeout)
            
            logger.info(f"情感分析完成: {result['sentiment']} (置信度: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'positive_score': 0.0,
                'negative_score': 0.0,
                'neutral_score': 1.0,
                'error': str(e)
            }
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符（保留中文、英文、数字、基本标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:()（）。，！？；：]', '', text)
        
        return text
    
    def _analyze_with_transformer(self, text: str) -> Dict:
        """使用Transformer模型分析"""
        try:
            # 这里应该集成实际的transformer模型
            # 暂时使用关键词分析作为fallback
            return self._analyze_with_keywords(text)
            
        except Exception as e:
            logger.error(f"Transformer分析失败: {str(e)}")
            return self._analyze_with_keywords(text)
    
    def _analyze_with_baidu(self, text: str) -> Dict:
        """使用百度情感分析API"""
        try:
            # 这里应该调用百度情感分析API
            # 暂时使用关键词分析作为fallback
            return self._analyze_with_keywords(text)
            
        except Exception as e:
            logger.error(f"百度情感分析失败: {str(e)}")
            return self._analyze_with_keywords(text)
    
    def _analyze_with_tencent(self, text: str) -> Dict:
        """使用腾讯情感分析API"""
        try:
            # 这里应该调用腾讯情感分析API
            # 暂时使用关键词分析作为fallback
            return self._analyze_with_keywords(text)
            
        except Exception as e:
            logger.error(f"腾讯情感分析失败: {str(e)}")
            return self._analyze_with_keywords(text)
    
    def _analyze_with_openai(self, text: str) -> Dict:
        """使用OpenAI进行情感分析"""
        try:
            # 这里应该调用OpenAI API
            # 暂时使用关键词分析作为fallback
            return self._analyze_with_keywords(text)
            
        except Exception as e:
            logger.error(f"OpenAI情感分析失败: {str(e)}")
            return self._analyze_with_keywords(text)
    
    def _analyze_with_keywords(self, text: str) -> Dict:
        """基于关键词的情感分析"""
        try:
            # 获取情感关键词
            keywords = EmotionKeyword.objects.filter(is_active=True)
            
            positive_score = 0.0
            negative_score = 0.0
            neutral_score = 0.0
            
            # 计算情感分数
            for keyword in keywords:
                if keyword.keyword in text:
                    if keyword.sentiment == 'positive':
                        positive_score += keyword.weight
                    elif keyword.sentiment == 'negative':
                        negative_score += keyword.weight
                    else:
                        neutral_score += keyword.weight
            
            # 如果没有匹配的关键词，默认为中性
            if positive_score == 0 and negative_score == 0 and neutral_score == 0:
                neutral_score = 1.0
            
            # 归一化分数
            total_score = positive_score + negative_score + neutral_score
            if total_score > 0:
                positive_score /= total_score
                negative_score /= total_score
                neutral_score /= total_score
            
            # 确定主要情感
            if positive_score > negative_score and positive_score > neutral_score:
                sentiment = 'positive'
                confidence = positive_score
            elif negative_score > positive_score and negative_score > neutral_score:
                sentiment = 'negative'
                confidence = negative_score
            else:
                sentiment = 'neutral'
                confidence = neutral_score
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'positive_score': positive_score,
                'negative_score': negative_score,
                'neutral_score': neutral_score,
            }
            
        except Exception as e:
            logger.error(f"关键词情感分析失败: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'positive_score': 0.0,
                'negative_score': 0.0,
                'neutral_score': 1.0,
            }
    
    def _save_analysis_result(self, text: str, result: Dict, 
                            user_id: Optional[int], platform: str, 
                            conversation_id: str):
        """保存分析结果到数据库"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
            
            SentimentAnalysis.objects.create(
                text=text,
                sentiment=result['sentiment'],
                confidence=result['confidence'],
                model_type=self.model_type,
                positive_score=result['positive_score'],
                negative_score=result['negative_score'],
                neutral_score=result['neutral_score'],
                user=user,
                platform=platform,
                conversation_id=conversation_id,
            )
            
        except Exception as e:
            logger.error(f"保存情感分析结果失败: {str(e)}")


class SentimentReportGenerator:
    """情感分析报告生成器"""
    
    def generate_daily_report(self, date) -> Dict:
        """生成日报"""
        from datetime import datetime, timedelta
        
        start_date = date
        end_date = date + timedelta(days=1)
        
        return self._generate_report('daily', start_date, end_date)
    
    def generate_weekly_report(self, start_date) -> Dict:
        """生成周报"""
        from datetime import timedelta
        
        end_date = start_date + timedelta(days=7)
        
        return self._generate_report('weekly', start_date, end_date)
    
    def generate_monthly_report(self, year: int, month: int) -> Dict:
        """生成月报"""
        from datetime import date
        import calendar
        
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        
        return self._generate_report('monthly', start_date, end_date)
    
    def _generate_report(self, period_type: str, start_date, end_date) -> Dict:
        """生成报告"""
        try:
            # 查询指定时间范围内的情感分析数据
            analyses = SentimentAnalysis.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            )
            
            total_count = analyses.count()
            if total_count == 0:
                return {
                    'period_type': period_type,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_analyses': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'positive_ratio': 0.0,
                    'negative_ratio': 0.0,
                    'neutral_ratio': 0.0,
                    'platform_stats': {},
                }
            
            # 统计各种情感的数量
            positive_count = analyses.filter(sentiment='positive').count()
            negative_count = analyses.filter(sentiment='negative').count()
            neutral_count = analyses.filter(sentiment='neutral').count()
            
            # 计算比例
            positive_ratio = positive_count / total_count
            negative_ratio = negative_count / total_count
            neutral_ratio = neutral_count / total_count
            
            # 统计各平台数据
            platform_stats = {}
            platforms = analyses.values_list('platform', flat=True).distinct()
            
            for platform in platforms:
                if platform:
                    platform_analyses = analyses.filter(platform=platform)
                    platform_total = platform_analyses.count()
                    platform_positive = platform_analyses.filter(sentiment='positive').count()
                    platform_negative = platform_analyses.filter(sentiment='negative').count()
                    platform_neutral = platform_analyses.filter(sentiment='neutral').count()
                    
                    platform_stats[platform] = {
                        'total': platform_total,
                        'positive': platform_positive,
                        'negative': platform_negative,
                        'neutral': platform_neutral,
                        'positive_ratio': platform_positive / platform_total if platform_total > 0 else 0,
                        'negative_ratio': platform_negative / platform_total if platform_total > 0 else 0,
                        'neutral_ratio': platform_neutral / platform_total if platform_total > 0 else 0,
                    }
            
            report_data = {
                'period_type': period_type,
                'start_date': start_date,
                'end_date': end_date,
                'total_analyses': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'platform_stats': platform_stats,
            }
            
            # 保存报告到数据库
            from .models import SentimentReport
            SentimentReport.objects.update_or_create(
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                defaults=report_data
            )
            
            return report_data
            
        except Exception as e:
            logger.error(f"生成情感分析报告失败: {str(e)}")
            return {}


def analyze_sentiment(text: str, model_type: str = 'transformer', 
                     user_id: Optional[int] = None, platform: str = '', 
                     conversation_id: str = '') -> Dict:
    """
    便捷的情感分析函数
    
    Args:
        text: 要分析的文本
        model_type: 使用的模型类型
        user_id: 用户ID
        platform: 平台名称
        conversation_id: 对话ID
        
    Returns:
        情感分析结果
    """
    analyzer = SentimentAnalyzer(model_type)
    return analyzer.analyze(text, user_id, platform, conversation_id) 