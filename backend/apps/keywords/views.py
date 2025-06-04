"""
关键词管理模块视图
定义关键触发词，当用户触发这些关键词时可切换到人工客服接入模式
需要配置触发阈值、优先级，并支持定时更新
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, F
import logging
import re
from typing import Dict, Any, List

from .models import KeywordCategory, Keyword, KeywordRule, KeywordMatch, KeywordStatistics
from .serializers import (
    KeywordCategorySerializer, KeywordSerializer, KeywordRuleSerializer,
    KeywordMatchSerializer, KeywordStatisticsSerializer
)
from .services import KeywordMatchingService, SentimentAnalysisService

logger = logging.getLogger(__name__)


class KeywordCategoryViewSet(viewsets.ModelViewSet):
    """关键词分类管理"""
    queryset = KeywordCategory.objects.all()
    serializer_class = KeywordCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'category_type']
    search_fields = ['name', 'description']
    ordering = ['priority', 'name']

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按类型获取分类"""
        category_type = request.query_params.get('type')
        if not category_type:
            return Response({'error': '缺少type参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        categories = self.get_queryset().filter(
            category_type=category_type,
            is_active=True
        ).order_by('priority', 'name')
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class KeywordViewSet(viewsets.ModelViewSet):
    """关键词管理"""
    queryset = Keyword.objects.select_related('category', 'created_by')
    serializer_class = KeywordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'keyword_type', 'is_active', 'priority_level']
    search_fields = ['word', 'description', 'tags']
    ordering = ['-priority_level', '-weight', '-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        智能体调用：检查文本是否触发关键词
        GET /api/keywords/check/?text={latest_message}
        """
        text = request.query_params.get('text', '').strip()
        check_type = request.query_params.get('type', 'human_handoff')  # human_handoff, sentiment, category
        threshold = float(request.query_params.get('threshold', 0.5))
        
        if not text:
            return Response({'error': '缺少text参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = KeywordMatchingService()
            
            if check_type == 'human_handoff':
                result = service.check_human_handoff(text, threshold)
            elif check_type == 'sentiment':
                result = service.check_sentiment_keywords(text, threshold)
            elif check_type == 'category':
                result = service.classify_text(text, threshold)
            else:
                result = service.match_all_types(text, threshold)
            
            # 记录匹配结果
            if result.get('matched_keywords'):
                self._record_keyword_matches(text, result['matched_keywords'], request.user)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"关键词检查失败: {str(e)}")
            return Response({
                'error': '关键词检查失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_check(self, request):
        """批量检查关键词"""
        texts = request.data.get('texts', [])
        check_type = request.data.get('type', 'human_handoff')
        threshold = float(request.data.get('threshold', 0.5))
        
        if not texts or not isinstance(texts, list):
            return Response({'error': '缺少texts参数或格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = KeywordMatchingService()
            results = []
            
            for text in texts:
                if isinstance(text, str) and text.strip():
                    if check_type == 'human_handoff':
                        result = service.check_human_handoff(text.strip(), threshold)
                    elif check_type == 'sentiment':
                        result = service.check_sentiment_keywords(text.strip(), threshold)
                    else:
                        result = service.match_all_types(text.strip(), threshold)
                    
                    result['text'] = text.strip()
                    results.append(result)
            
            return Response({
                'total_texts': len(texts),
                'processed_texts': len(results),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"批量关键词检查失败: {str(e)}")
            return Response({
                'error': '批量检查失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类获取关键词"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response({'error': '缺少category_id参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        keywords = self.get_queryset().filter(
            category_id=category_id,
            is_active=True
        ).order_by('-priority_level', '-weight')
        
        serializer = self.get_serializer(keywords, many=True)
        return Response({
            'category_id': category_id,
            'keywords': serializer.data,
            'count': keywords.count()
        })

    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """获取高优先级关键词"""
        limit = int(request.query_params.get('limit', 50))
        keyword_type = request.query_params.get('type')
        
        queryset = self.get_queryset().filter(
            is_active=True,
            priority_level__gte=8  # 高优先级
        )
        
        if keyword_type:
            queryset = queryset.filter(keyword_type=keyword_type)
        
        keywords = queryset.order_by('-priority_level', '-weight')[:limit]
        serializer = self.get_serializer(keywords, many=True)
        
        return Response({
            'high_priority_keywords': serializer.data,
            'count': keywords.count(),
            'limit': limit
        })

    @action(detail=True, methods=['post'])
    def test_match(self, request, pk=None):
        """测试关键词匹配"""
        keyword = self.get_object()
        test_text = request.data.get('text', '')
        
        if not test_text:
            return Response({'error': '缺少测试文本'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = KeywordMatchingService()
            match_result = service.test_keyword_match(keyword, test_text)
            
            return Response({
                'keyword_id': keyword.id,
                'keyword_word': keyword.word,
                'test_text': test_text,
                'is_match': match_result.get('is_match', False),
                'confidence': match_result.get('confidence', 0.0),
                'match_details': match_result.get('details', {})
            })
            
        except Exception as e:
            logger.error(f"测试关键词匹配失败: {str(e)}")
            return Response({
                'error': '测试失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _record_keyword_matches(self, text: str, matched_keywords: List[Dict], user):
        """记录关键词匹配结果"""
        try:
            for match_info in matched_keywords:
                keyword_id = match_info.get('keyword_id')
                confidence = match_info.get('confidence', 0.0)
                
                if keyword_id:
                    KeywordMatch.objects.create(
                        keyword_id=keyword_id,
                        matched_text=text,
                        confidence=confidence,
                        match_context={'full_text': text},
                        matched_by=user
                    )
                    
                    # 更新关键词统计
                    keyword = Keyword.objects.get(id=keyword_id)
                    keyword.match_count = F('match_count') + 1
                    keyword.save(update_fields=['match_count'])
                    
        except Exception as e:
            logger.error(f"记录关键词匹配失败: {str(e)}")


class KeywordRuleViewSet(viewsets.ModelViewSet):
    """关键词规则管理"""
    queryset = KeywordRule.objects.prefetch_related('keywords')
    serializer_class = KeywordRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rule_type', 'is_active', 'trigger_action']
    search_fields = ['name', 'description']
    ordering = ['-priority', '-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def evaluate(self, request):
        """评估规则匹配"""
        text = request.data.get('text', '')
        rule_ids = request.data.get('rule_ids', [])
        
        if not text:
            return Response({'error': '缺少text参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = KeywordMatchingService()
            
            if rule_ids:
                rules = self.get_queryset().filter(id__in=rule_ids, is_active=True)
            else:
                rules = self.get_queryset().filter(is_active=True)
            
            evaluation_results = []
            
            for rule in rules:
                result = service.evaluate_rule(rule, text)
                evaluation_results.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type,
                    'is_triggered': result.get('is_triggered', False),
                    'confidence': result.get('confidence', 0.0),
                    'matched_keywords': result.get('matched_keywords', []),
                    'trigger_action': rule.trigger_action
                })
            
            # 按优先级和置信度排序
            evaluation_results.sort(
                key=lambda x: (x['is_triggered'], x['confidence']), 
                reverse=True
            )
            
            return Response({
                'text': text,
                'total_rules': len(evaluation_results),
                'triggered_rules': len([r for r in evaluation_results if r['is_triggered']]),
                'evaluation_results': evaluation_results
            })
            
        except Exception as e:
            logger.error(f"规则评估失败: {str(e)}")
            return Response({
                'error': '规则评估失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def test_rule(self, request, pk=None):
        """测试单个规则"""
        rule = self.get_object()
        test_cases = request.data.get('test_cases', [])
        
        if not test_cases:
            return Response({'error': '缺少测试用例'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = KeywordMatchingService()
            test_results = []
            
            for test_case in test_cases:
                if isinstance(test_case, str):
                    text = test_case
                    expected = None
                else:
                    text = test_case.get('text', '')
                    expected = test_case.get('expected', None)
                
                if text:
                    result = service.evaluate_rule(rule, text)
                    test_result = {
                        'text': text,
                        'expected': expected,
                        'actual': result.get('is_triggered', False),
                        'confidence': result.get('confidence', 0.0),
                        'matched_keywords': result.get('matched_keywords', [])
                    }
                    
                    if expected is not None:
                        test_result['is_correct'] = (expected == test_result['actual'])
                    
                    test_results.append(test_result)
            
            # 计算准确率（如果有期望结果）
            correct_count = len([r for r in test_results if r.get('is_correct', True)])
            accuracy = (correct_count / len(test_results)) if test_results else 0.0
            
            return Response({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'total_tests': len(test_results),
                'accuracy': round(accuracy * 100, 2),
                'test_results': test_results
            })
            
        except Exception as e:
            logger.error(f"测试规则失败: {str(e)}")
            return Response({
                'error': '测试失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KeywordMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """关键词匹配记录"""
    queryset = KeywordMatch.objects.select_related('keyword', 'matched_by')
    serializer_class = KeywordMatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['keyword', 'match_type']
    ordering = ['-matched_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """匹配统计"""
        keyword_id = request.query_params.get('keyword_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        if keyword_id:
            queryset = queryset.filter(keyword_id=keyword_id)
        
        if date_from:
            queryset = queryset.filter(matched_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(matched_at__date__lte=date_to)
        
        total_matches = queryset.count()
        
        # 按关键词分组统计
        keyword_stats = queryset.values(
            'keyword__word', 'keyword__keyword_type'
        ).annotate(
            match_count=models.Count('id')
        ).order_by('-match_count')[:10]
        
        # 按日期分组统计
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        daily_stats = queryset.annotate(
            date=TruncDate('matched_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')[:7]
        
        return Response({
            'total_matches': total_matches,
            'top_keywords': list(keyword_stats),
            'daily_stats': list(daily_stats)
        })


class KeywordStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """关键词统计信息"""
    queryset = KeywordStatistics.objects.select_related('keyword')
    serializer_class = KeywordStatisticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['keyword', 'keyword__category']
    ordering = ['-total_matches']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """统计概览"""
        total_keywords = Keyword.objects.filter(is_active=True).count()
        total_matches = KeywordMatch.objects.count()
        active_keywords = self.get_queryset().filter(total_matches__gt=0).count()
        
        # 获取热门关键词
        top_keywords = self.get_queryset().order_by('-total_matches')[:10]
        top_keywords_data = self.get_serializer(top_keywords, many=True).data
        
        # 人工接入触发统计
        human_handoff_matches = KeywordMatch.objects.filter(
            keyword__keyword_type='human_handoff'
        ).count()
        
        return Response({
            'total_keywords': total_keywords,
            'total_matches': total_matches,
            'active_keywords': active_keywords,
            'usage_rate': round((active_keywords / total_keywords * 100) if total_keywords > 0 else 0, 2),
            'human_handoff_triggers': human_handoff_matches,
            'top_keywords': top_keywords_data
        })

    @action(detail=False, methods=['post'])
    def update_statistics(self, request):
        """更新统计数据"""
        try:
            from django.db.models import Count, Avg
            
            # 更新所有关键词的统计数据
            updated_count = 0
            
            for keyword in Keyword.objects.filter(is_active=True):
                matches = KeywordMatch.objects.filter(keyword=keyword)
                
                stats, created = KeywordStatistics.objects.get_or_create(
                    keyword=keyword,
                    defaults={
                        'total_matches': 0,
                        'average_confidence': 0.0,
                        'last_matched_at': None
                    }
                )
                
                stats.total_matches = matches.count()
                if stats.total_matches > 0:
                    stats.average_confidence = matches.aggregate(
                        avg=Avg('confidence')
                    )['avg'] or 0.0
                    stats.last_matched_at = matches.order_by('-matched_at').first().matched_at
                else:
                    stats.average_confidence = 0.0
                    stats.last_matched_at = None
                
                stats.updated_at = timezone.now()
                stats.save()
                updated_count += 1
            
            return Response({
                'success': True,
                'updated_keywords': updated_count,
                'message': '统计数据更新完成'
            })
            
        except Exception as e:
            logger.error(f"更新统计数据失败: {str(e)}")
            return Response({
                'error': '更新失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 