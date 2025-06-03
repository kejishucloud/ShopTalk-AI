"""
标签管理模块视图
提供标签的增删改查和规则匹配API
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
import logging

from .models import TagCategory, Tag, TagRule, TagAssignment, TagStatistics
from .serializers import (
    TagCategorySerializer, TagSerializer, TagRuleSerializer, 
    TagAssignmentSerializer, TagStatisticsSerializer
)
from .services import TagMatchingService

logger = logging.getLogger(__name__)


class TagCategoryViewSet(viewsets.ModelViewSet):
    """标签分类管理"""
    queryset = TagCategory.objects.all()
    serializer_class = TagCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


class TagViewSet(viewsets.ModelViewSet):
    """标签管理"""
    queryset = Tag.objects.select_related('category', 'created_by')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_system', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类获取标签"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response({'error': '缺少category_id参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        tags = self.get_queryset().filter(category_id=category_id, is_active=True)
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class TagRuleViewSet(viewsets.ModelViewSet):
    """标签规则管理"""
    queryset = TagRule.objects.prefetch_related('target_tags')
    serializer_class = TagRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rule_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-priority', '-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_intent(self, request):
        """智能体调用：根据意图获取匹配规则"""
        intent = request.query_params.get('intent')
        if not intent:
            return Response({'error': '缺少intent参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        rules = self.get_queryset().filter(
            rule_type='intent',
            conditions__intent=intent,
            is_active=True
        )
        
        serializer = self.get_serializer(rules, many=True)
        return Response({
            'intent': intent,
            'rules': serializer.data,
            'count': rules.count()
        })

    @action(detail=False, methods=['post'])
    def match_text(self, request):
        """文本匹配API - 智能体调用"""
        text = request.data.get('text', '')
        if not text:
            return Response({'error': '缺少text参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = TagMatchingService()
        matched_rules = service.match_text(text)
        
        return Response({
            'text': text,
            'matched_rules': [
                {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type,
                    'tags': [tag.name for tag in rule.target_tags.all()],
                    'confidence': confidence
                }
                for rule, confidence in matched_rules
            ],
            'total_matches': len(matched_rules)
        })


class TagAssignmentViewSet(viewsets.ModelViewSet):
    """标签分配管理"""
    queryset = TagAssignment.objects.select_related('tag', 'content_type', 'assigned_by', 'rule')
    serializer_class = TagAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tag', 'content_type', 'assignment_type']
    ordering = ['-assigned_at']

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @action(detail=False, methods=['post'])
    def assign(self, request):
        """智能体调用：批量分配标签"""
        data = request.data
        tag_ids = data.get('tag_ids', [])
        content_type_id = data.get('content_type_id')
        object_id = data.get('object_id')
        assignment_type = data.get('assignment_type', 'agent')
        confidence = data.get('confidence', 1.0)
        
        if not all([tag_ids, content_type_id, object_id]):
            return Response(
                {'error': '缺少必要参数: tag_ids, content_type_id, object_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            assignments = []
            
            for tag_id in tag_ids:
                assignment, created = TagAssignment.objects.get_or_create(
                    tag_id=tag_id,
                    content_type=content_type,
                    object_id=object_id,
                    defaults={
                        'assignment_type': assignment_type,
                        'confidence': confidence,
                        'assigned_by': request.user
                    }
                )
                assignments.append(assignment)
            
            serializer = self.get_serializer(assignments, many=True)
            return Response({
                'success': True,
                'assignments': serializer.data,
                'created_count': sum(1 for a in assignments if a.assigned_at == a.assigned_at)
            })
            
        except ContentType.DoesNotExist:
            return Response(
                {'error': f'无效的content_type_id: {content_type_id}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"标签分配失败: {str(e)}")
            return Response(
                {'error': '标签分配失败'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def by_object(self, request):
        """获取对象的所有标签"""
        content_type_id = request.query_params.get('content_type_id')
        object_id = request.query_params.get('object_id')
        
        if not all([content_type_id, object_id]):
            return Response(
                {'error': '缺少参数: content_type_id, object_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignments = self.get_queryset().filter(
            content_type_id=content_type_id,
            object_id=object_id
        )
        
        serializer = self.get_serializer(assignments, many=True)
        return Response({
            'object_type': content_type_id,
            'object_id': object_id,
            'assignments': serializer.data,
            'tag_count': assignments.count()
        })

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        """移除标签分配"""
        tag_id = request.data.get('tag_id')
        content_type_id = request.data.get('content_type_id')
        object_id = request.data.get('object_id')
        
        if not all([tag_id, content_type_id, object_id]):
            return Response(
                {'error': '缺少必要参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = TagAssignment.objects.filter(
            tag_id=tag_id,
            content_type_id=content_type_id,
            object_id=object_id
        ).delete()
        
        return Response({
            'success': True,
            'deleted_count': deleted_count
        })


class TagStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """标签统计信息"""
    queryset = TagStatistics.objects.select_related('tag')
    serializer_class = TagStatisticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tag']
    ordering = ['-total_assignments']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """标签使用概览"""
        total_tags = Tag.objects.filter(is_active=True).count()
        total_assignments = TagAssignment.objects.count()
        active_tags = TagStatistics.objects.filter(active_assignments__gt=0).count()
        
        top_tags = self.get_queryset().order_by('-total_assignments')[:10]
        top_tags_data = self.get_serializer(top_tags, many=True).data
        
        return Response({
            'total_tags': total_tags,
            'total_assignments': total_assignments,
            'active_tags': active_tags,
            'usage_rate': round((active_tags / total_tags * 100) if total_tags > 0 else 0, 2),
            'top_tags': top_tags_data
        }) 