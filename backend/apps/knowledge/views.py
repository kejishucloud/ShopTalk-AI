"""
知识库管理视图
提供知识库、文档、FAQ、商品、话术等的API接口
"""

import logging
import os
from typing import Any, Dict
from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    KnowledgeBase, DocumentCategory, DocumentTag, Document, FAQ, Product,
    Script, KnowledgeVector, KnowledgeAccessRecord, KnowledgeRecommendation
)
from .serializers import (
    KnowledgeBaseSerializer, DocumentCategorySerializer, DocumentTagSerializer,
    DocumentSerializer, FAQSerializer, ProductSerializer, ScriptSerializer,
    KnowledgeVectorSerializer, KnowledgeAccessRecordSerializer,
    KnowledgeRecommendationSerializer, KnowledgeSearchRequestSerializer,
    KnowledgeSearchResultSerializer, DocumentUploadSerializer,
    BatchOperationSerializer, KnowledgeAnalyticsSerializer
)
from .services import (
    DocumentProcessorService, VectorizeService, KnowledgeSearchService,
    RecommendationService, KnowledgeAnalyticsService
)

logger = logging.getLogger('knowledge')


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """知识库管理"""
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_type', 'access_level', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """获取知识库分析数据"""
        knowledge_base = self.get_object()
        
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        
        date_from = None
        date_to = None
        
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            except ValueError:
                return Response({'error': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            except ValueError:
                return Response({'error': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        analytics_service = KnowledgeAnalyticsService()
        analytics_data = analytics_service.get_knowledge_base_analytics(
            knowledge_base.id, date_from, date_to
        )
        
        return Response(analytics_data)

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """导出知识库"""
        knowledge_base = self.get_object()
        export_format = request.data.get('format', 'json')
        include_types = request.data.get('include_types', ['document', 'faq', 'product', 'script'])
        
        # 这里可以实现具体的导出逻辑
        return Response({
            'message': '导出功能开发中',
            'knowledge_base_id': knowledge_base.id,
            'format': export_format,
            'include_types': include_types
        })

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按类型获取知识库"""
        knowledge_type = request.query_params.get('type')
        if not knowledge_type:
            return Response({'error': '缺少type参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        knowledge_bases = self.get_queryset().filter(
            knowledge_type=knowledge_type,
            is_active=True
        )
        
        serializer = self.get_serializer(knowledge_bases, many=True)
        return Response({
            'knowledge_type': knowledge_type,
            'knowledge_bases': serializer.data,
            'count': knowledge_bases.count()
        })


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """文档分类管理"""
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'parent', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取分类树结构"""
        knowledge_base_id = request.query_params.get('knowledge_base_id')
        if not knowledge_base_id:
            return Response({'error': '缺少knowledge_base_id参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取顶级分类
        root_categories = self.get_queryset().filter(
            knowledge_base_id=knowledge_base_id,
            parent=None,
            is_active=True
        )
        
        def build_tree(categories):
            tree = []
            for category in categories:
                children = category.children.filter(is_active=True)
                category_data = self.get_serializer(category).data
                if children.exists():
                    category_data['children'] = build_tree(children)
                tree.append(category_data)
            return tree
        
        tree_data = build_tree(root_categories)
        return Response({
            'knowledge_base_id': knowledge_base_id,
            'tree': tree_data
        })


class DocumentTagViewSet(viewsets.ModelViewSet):
    """文档标签管理"""
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base']
    search_fields = ['name', 'description']
    ordering = ['-usage_count', 'name']

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """获取热门标签"""
        knowledge_base_id = request.query_params.get('knowledge_base_id')
        limit = int(request.query_params.get('limit', 20))
        
        queryset = self.get_queryset()
        if knowledge_base_id:
            queryset = queryset.filter(knowledge_base_id=knowledge_base_id)
        
        popular_tags = queryset.order_by('-usage_count')[:limit]
        serializer = self.get_serializer(popular_tags, many=True)
        
        return Response({
            'tags': serializer.data,
            'count': len(serializer.data)
        })


class DocumentViewSet(viewsets.ModelViewSet):
    """文档管理"""
    queryset = Document.objects.select_related('knowledge_base', 'category', 'created_by')
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'category', 'document_type', 'process_status', 'is_active']
    search_fields = ['title', 'content', 'summary']
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """上传文档"""
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validated_data = serializer.validated_data
            
            # 创建文档记录
            document = Document.objects.create(
                knowledge_base_id=validated_data['knowledge_base_id'],
                category_id=validated_data.get('category_id'),
                title=validated_data['title'],
                file_path=validated_data['file'],
                document_type=self._get_document_type(validated_data['file'].name),
                created_by=request.user
            )
            
            # 设置标签
            if validated_data.get('tag_ids'):
                document.tags.set(validated_data['tag_ids'])
            
            # 自动处理文档
            if validated_data.get('auto_extract', True):
                processor_service = DocumentProcessorService()
                process_result = processor_service.process_document(document)
                
                if not process_result['success']:
                    logger.warning(f"文档处理失败: {process_result.get('error')}")
            
            # 自动向量化
            if validated_data.get('auto_vectorize', True) and document.knowledge_base.enable_ai_enhancement:
                vectorize_service = VectorizeService()
                vectorize_result = vectorize_service.vectorize_document(document)
                
                if not vectorize_result['success']:
                    logger.warning(f"文档向量化失败: {vectorize_result.get('error')}")
            
            document_serializer = DocumentSerializer(document)
            return Response(document_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"文档上传失败: {str(e)}")
            return Response({
                'error': '文档上传失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """处理文档"""
        document = self.get_object()
        
        try:
            processor_service = DocumentProcessorService()
            result = processor_service.process_document(document)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def vectorize(self, request, pk=None):
        """向量化文档"""
        document = self.get_object()
        
        try:
            vectorize_service = VectorizeService()
            result = vectorize_service.vectorize_document(document)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"文档向量化失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载文档"""
        document = self.get_object()
        
        if not document.file_path:
            return Response({'error': '文档文件不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # 增加下载计数
            document.download_count += 1
            document.save(update_fields=['download_count'])
            
            # 记录访问
            self._record_access(document, 'download', request)
            
            # 返回文件
            file_path = document.file_path.path
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read())
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                response['Content-Type'] = 'application/octet-stream'
                return response
                
        except Exception as e:
            logger.error(f"文档下载失败: {str(e)}")
            return Response({
                'error': '文档下载失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """评分文档"""
        document = self.get_object()
        rating = request.data.get('rating')
        
        if not rating or not (1 <= rating <= 5):
            return Response({'error': '评分必须在1-5之间'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            document.add_rating(rating)
            
            return Response({
                'success': True,
                'message': '评分成功',
                'new_rating': document.rating,
                'rating_count': document.rating_count
            })
            
        except Exception as e:
            logger.error(f"文档评分失败: {str(e)}")
            return Response({
                'error': '评分失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """获取推荐内容"""
        document = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        
        try:
            recommendation_service = RecommendationService()
            recommendations = recommendation_service.generate_recommendations(
                'document', document.id, document.knowledge_base_id, limit
            )
            
            return Response({
                'document_id': document.id,
                'recommendations': recommendations,
                'count': len(recommendations)
            })
            
        except Exception as e:
            logger.error(f"获取推荐失败: {str(e)}")
            return Response({
                'error': '获取推荐失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """获取文档详情（增加访问记录）"""
        instance = self.get_object()
        
        # 增加查看计数
        instance.increment_view_count()
        
        # 记录访问
        self._record_access(instance, 'view', request)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _get_document_type(self, filename: str) -> str:
        """根据文件名获取文档类型"""
        ext = os.path.splitext(filename)[1].lower()
        type_mapping = {
            '.pdf': 'pdf',
            '.doc': 'word',
            '.docx': 'word',
            '.xls': 'excel',
            '.xlsx': 'excel',
            '.txt': 'text',
            '.md': 'markdown',
            '.html': 'html',
            '.htm': 'html',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.mp4': 'video',
            '.avi': 'video',
            '.mp3': 'audio',
            '.wav': 'audio',
        }
        return type_mapping.get(ext, 'text')

    def _record_access(self, document: Document, access_type: str, request):
        """记录访问"""
        try:
            KnowledgeAccessRecord.objects.create(
                knowledge_base=document.knowledge_base,
                content_type='document',
                content_id=document.id,
                user=request.user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                access_type=access_type,
                success=True
            )
        except Exception as e:
            logger.warning(f"记录访问失败: {str(e)}")

    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FAQViewSet(viewsets.ModelViewSet):
    """FAQ管理"""
    queryset = FAQ.objects.select_related('knowledge_base', 'category', 'created_by')
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'category', 'status', 'is_active', 'is_featured']
    search_fields = ['question', 'answer']
    ordering = ['-priority', '-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def helpful(self, request, pk=None):
        """标记为有用"""
        faq = self.get_object()
        faq.mark_helpful()
        
        return Response({
            'success': True,
            'message': '标记成功',
            'helpful_count': faq.helpful_count
        })

    @action(detail=True, methods=['post'])
    def unhelpful(self, request, pk=None):
        """标记为无用"""
        faq = self.get_object()
        faq.mark_unhelpful()
        
        return Response({
            'success': True,
            'message': '标记成功',
            'unhelpful_count': faq.unhelpful_count
        })

    @action(detail=True, methods=['post'])
    def vectorize(self, request, pk=None):
        """向量化FAQ"""
        faq = self.get_object()
        
        try:
            vectorize_service = VectorizeService()
            result = vectorize_service.vectorize_faq(faq)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"FAQ向量化失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """获取FAQ详情（增加访问记录）"""
        instance = self.get_object()
        
        # 增加查看计数
        instance.increment_view_count()
        
        # 记录访问
        self._record_access(instance, 'view', request)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _record_access(self, faq: FAQ, access_type: str, request):
        """记录访问"""
        try:
            KnowledgeAccessRecord.objects.create(
                knowledge_base=faq.knowledge_base,
                content_type='faq',
                content_id=faq.id,
                user=request.user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                access_type=access_type,
                success=True
            )
        except Exception as e:
            logger.warning(f"记录访问失败: {str(e)}")

    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ProductViewSet(viewsets.ModelViewSet):
    """商品管理"""
    queryset = Product.objects.select_related('knowledge_base', 'category', 'created_by')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'category', 'status', 'brand', 'product_category']
    search_fields = ['name', 'sku', 'description']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_brand(self, request):
        """按品牌获取商品"""
        brand = request.query_params.get('brand')
        if not brand:
            return Response({'error': '缺少brand参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        products = self.get_queryset().filter(brand=brand, status='active')
        serializer = self.get_serializer(products, many=True)
        
        return Response({
            'brand': brand,
            'products': serializer.data,
            'count': products.count()
        })

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """获取低库存商品"""
        products = self.get_queryset().filter(
            stock_quantity__lte=F('min_stock_level'),
            status='active'
        )
        
        serializer = self.get_serializer(products, many=True)
        return Response({
            'products': serializer.data,
            'count': products.count()
        })


class ScriptViewSet(viewsets.ModelViewSet):
    """话术模板管理"""
    queryset = Script.objects.select_related('knowledge_base', 'category', 'created_by')
    serializer_class = ScriptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'category', 'script_type', 'status', 'is_active']
    search_fields = ['name', 'content']
    ordering = ['-priority', '-usage_count']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """使用话术（增加使用计数）"""
        script = self.get_object()
        script.increment_usage()
        
        return Response({
            'success': True,
            'message': '使用记录成功',
            'usage_count': script.usage_count
        })

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按类型获取话术"""
        script_type = request.query_params.get('type')
        if not script_type:
            return Response({'error': '缺少type参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        scripts = self.get_queryset().filter(
            script_type=script_type,
            status='active',
            is_active=True
        )
        
        serializer = self.get_serializer(scripts, many=True)
        return Response({
            'script_type': script_type,
            'scripts': serializer.data,
            'count': scripts.count()
        })


class KnowledgeSearchView(viewsets.GenericViewSet):
    """知识搜索"""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def search(self, request):
        """执行知识搜索"""
        serializer = KnowledgeSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            search_service = KnowledgeSearchService()
            result = search_service.search(**serializer.validated_data)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"知识搜索失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'results': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchOperationView(viewsets.GenericViewSet):
    """批量操作"""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def batch_operation(self, request):
        """执行批量操作"""
        serializer = BatchOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validated_data = serializer.validated_data
            action = validated_data['action']
            content_type = validated_data['content_type']
            content_ids = validated_data['content_ids']
            
            # 获取模型类
            model_map = {
                'document': Document,
                'faq': FAQ,
                'product': Product,
                'script': Script
            }
            
            if content_type not in model_map:
                return Response({'error': '不支持的内容类型'}, status=status.HTTP_400_BAD_REQUEST)
            
            model_class = model_map[content_type]
            objects = model_class.objects.filter(id__in=content_ids)
            
            if not objects.exists():
                return Response({'error': '未找到指定的内容'}, status=status.HTTP_404_NOT_FOUND)
            
            # 执行批量操作
            updated_count = 0
            
            if action == 'activate':
                updated_count = objects.update(is_active=True)
            elif action == 'deactivate':
                updated_count = objects.update(is_active=False)
            elif action == 'delete':
                updated_count = objects.count()
                objects.delete()
            elif action == 'move_category':
                target_category_id = validated_data.get('target_category_id')
                if not target_category_id:
                    return Response({'error': '缺少目标分类ID'}, status=status.HTTP_400_BAD_REQUEST)
                updated_count = objects.update(category_id=target_category_id)
            elif action in ['add_tags', 'remove_tags']:
                tag_ids = validated_data.get('tag_ids', [])
                if not tag_ids:
                    return Response({'error': '缺少标签ID'}, status=status.HTTP_400_BAD_REQUEST)
                
                for obj in objects:
                    if action == 'add_tags':
                        obj.tags.add(*tag_ids)
                    else:
                        obj.tags.remove(*tag_ids)
                
                updated_count = objects.count()
            
            return Response({
                'success': True,
                'message': f'批量{action}操作完成',
                'updated_count': updated_count
            })
            
        except Exception as e:
            logger.error(f"批量操作失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowledgeAccessRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """知识访问记录"""
    queryset = KnowledgeAccessRecord.objects.select_related('knowledge_base', 'user')
    serializer_class = KnowledgeAccessRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['knowledge_base', 'content_type', 'access_type', 'user']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """访问统计"""
        knowledge_base_id = request.query_params.get('knowledge_base_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        if knowledge_base_id:
            queryset = queryset.filter(knowledge_base_id=knowledge_base_id)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # 基础统计
        total_records = queryset.count()
        unique_users = queryset.values('user').distinct().count()
        
        # 按访问类型统计
        access_type_stats = queryset.values('access_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按内容类型统计
        content_type_stats = queryset.values('content_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 平均响应时间
        avg_response_time = queryset.aggregate(
            avg_time=Avg('response_time')
        )['avg_time'] or 0
        
        return Response({
            'total_records': total_records,
            'unique_users': unique_users,
            'average_response_time': avg_response_time,
            'access_type_stats': list(access_type_stats),
            'content_type_stats': list(content_type_stats)
        })


class KnowledgeRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """知识推荐记录"""
    queryset = KnowledgeRecommendation.objects.select_related('knowledge_base')
    serializer_class = KnowledgeRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['knowledge_base', 'recommendation_type', 'is_active']
    ordering = ['-similarity_score', '-confidence_score'] 