"""
知识库API视图
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from .models import (
    KnowledgeBase, Script, Product, Document, FAQ, 
    DocumentCategory, DocumentTag
)
from .api_serializers import (
    KnowledgeBaseSerializer, ScriptSerializer, ProductSerializer,
    DocumentSerializer, FAQSerializer, DocumentCategorySerializer,
    DocumentTagSerializer, KnowledgeSearchSerializer, 
    BatchImportSerializer, KnowledgeStatsSerializer
)
from .vector_services import KnowledgeVectorService
from .ragflow_client import KnowledgeRAGFlowSync
from .import_services import ScriptImportService, ProductImportService
from .kb_sync import (
    sync_knowledge_base_task, sync_single_content_task,
    sync_updated_content_task
)

logger = logging.getLogger(__name__)

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """知识库视图集"""
    
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_type', 'access_level', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 根据权限过滤
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=user) | 
                Q(access_level='public') |
                Q(permissions__contains={'users': [user.id]})
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """同步知识库到向量库和RAGFlow"""
        knowledge_base = self.get_object()
        
        try:
            # 启动异步同步任务
            task = sync_knowledge_base_task.delay(knowledge_base.id)
            
            return Response({
                'message': '知识库同步任务已启动',
                'task_id': task.id,
                'knowledge_base_id': knowledge_base.id
            })
            
        except Exception as e:
            logger.error(f"启动知识库同步任务失败: {e}")
            return Response({
                'error': f'启动同步任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取知识库统计信息"""
        knowledge_base = self.get_object()
        
        try:
            stats = {
                'knowledge_base_id': knowledge_base.id,
                'knowledge_base_name': knowledge_base.name,
                'total_scripts': knowledge_base.scripts.filter(is_active=True).count(),
                'total_products': knowledge_base.products.filter(status='active').count(),
                'total_documents': knowledge_base.documents.filter(is_active=True).count(),
                'total_faqs': knowledge_base.faqs.filter(is_active=True).count(),
                'total_vectors': knowledge_base.vectors.count(),
                'last_sync_time': knowledge_base.updated_at,
                'sync_status': 'completed'  # 可以根据实际同步状态调整
            }
            
            serializer = KnowledgeStatsSerializer(stats)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取知识库统计失败: {e}")
            return Response({
                'error': f'获取统计信息失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScriptViewSet(viewsets.ModelViewSet):
    """话术视图集"""
    
    queryset = Script.objects.all()
    serializer_class = ScriptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'script_type', 'status', 'is_active']
    search_fields = ['name', 'content']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'usage_count']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 根据知识库权限过滤
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=user) |
                Q(knowledge_base__created_by=user) |
                Q(knowledge_base__access_level='public') |
                Q(knowledge_base__permissions__contains={'users': [user.id]})
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """创建话术后同步"""
        script = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            script.knowledge_base.id, 'script', script.id
        )
    
    def perform_update(self, serializer):
        """更新话术后同步"""
        script = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            script.knowledge_base.id, 'script', script.id
        )
    
    @action(detail=True, methods=['post'])
    def increment_usage(self, request, pk=None):
        """增加使用次数"""
        script = self.get_object()
        script.increment_usage()
        
        return Response({
            'message': '使用次数已更新',
            'usage_count': script.usage_count
        })

class ProductViewSet(viewsets.ModelViewSet):
    """产品视图集"""
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'brand', 'product_category', 'status']
    search_fields = ['name', 'sku', 'description', 'brand']
    ordering_fields = ['created_at', 'updated_at', 'price', 'sales_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 根据知识库权限过滤
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=user) |
                Q(knowledge_base__created_by=user) |
                Q(knowledge_base__access_level='public') |
                Q(knowledge_base__permissions__contains={'users': [user.id]})
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """创建产品后同步"""
        product = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            product.knowledge_base.id, 'product', product.id
        )
    
    def perform_update(self, serializer):
        """更新产品后同步"""
        product = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            product.knowledge_base.id, 'product', product.id
        )

class DocumentViewSet(viewsets.ModelViewSet):
    """文档视图集"""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'document_type', 'process_status', 'is_active']
    search_fields = ['title', 'content', 'summary']
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 根据知识库权限过滤
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=user) |
                Q(knowledge_base__created_by=user) |
                Q(knowledge_base__access_level='public') |
                Q(knowledge_base__permissions__contains={'users': [user.id]})
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """创建文档后同步"""
        document = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            document.knowledge_base.id, 'document', document.id
        )
    
    def perform_update(self, serializer):
        """更新文档后同步"""
        document = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            document.knowledge_base.id, 'document', document.id
        )
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """增加查看次数"""
        document = self.get_object()
        document.increment_view_count()
        
        return Response({
            'message': '查看次数已更新',
            'view_count': document.view_count
        })

class FAQViewSet(viewsets.ModelViewSet):
    """FAQ视图集"""
    
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base', 'faq_category', 'status', 'is_active']
    search_fields = ['question', 'answer']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'view_count']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 根据知识库权限过滤
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=user) |
                Q(knowledge_base__created_by=user) |
                Q(knowledge_base__access_level='public') |
                Q(knowledge_base__permissions__contains={'users': [user.id]})
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """创建FAQ后同步"""
        faq = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            faq.knowledge_base.id, 'faq', faq.id
        )
    
    def perform_update(self, serializer):
        """更新FAQ后同步"""
        faq = serializer.save()
        
        # 异步同步到向量库和RAGFlow
        sync_single_content_task.delay(
            faq.knowledge_base.id, 'faq', faq.id
        )
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """标记为有用"""
        faq = self.get_object()
        faq.mark_helpful()
        
        return Response({
            'message': 'FAQ已标记为有用',
            'helpful_count': faq.helpful_count,
            'helpfulness_ratio': faq.helpfulness_ratio
        })
    
    @action(detail=True, methods=['post'])
    def mark_unhelpful(self, request, pk=None):
        """标记为无用"""
        faq = self.get_object()
        faq.mark_unhelpful()
        
        return Response({
            'message': 'FAQ已标记为无用',
            'unhelpful_count': faq.unhelpful_count,
            'helpfulness_ratio': faq.helpfulness_ratio
        })

class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """文档分类视图集"""
    
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['knowledge_base', 'parent', 'is_active']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']

class DocumentTagViewSet(viewsets.ModelViewSet):
    """文档标签视图集"""
    
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['knowledge_base']
    search_fields = ['name', 'description']
    ordering_fields = ['usage_count', 'name', 'created_at']
    ordering = ['-usage_count', 'name']

class KnowledgeSearchView(viewsets.GenericViewSet):
    """知识搜索视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """搜索知识库"""
        serializer = KnowledgeSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # 获取搜索参数
            query = serializer.validated_data['query']
            kb_id = serializer.validated_data['knowledge_base_id']
            content_types = serializer.validated_data.get('content_types')
            top_k = serializer.validated_data.get('top_k', 10)
            similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.7)
            
            # 检查知识库权限
            kb = get_object_or_404(KnowledgeBase, id=kb_id)
            user = request.user
            
            if not (user.is_superuser or 
                   kb.created_by == user or 
                   kb.access_level == 'public' or
                   user.id in kb.permissions.get('users', [])):
                return Response({
                    'error': '没有访问该知识库的权限'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 向量搜索
            vector_service = KnowledgeVectorService()
            vector_results = vector_service.search_knowledge(
                kb_id, query, top_k, content_types
            )
            
            # RAGFlow搜索
            ragflow_sync = KnowledgeRAGFlowSync()
            ragflow_results = ragflow_sync.search_ragflow(kb_id, query, top_k)
            
            # 合并结果
            results = {
                'query': query,
                'knowledge_base_id': kb_id,
                'vector_results': vector_results,
                'ragflow_results': ragflow_results,
                'total_results': len(vector_results) + len(ragflow_results)
            }
            
            return Response(results)
            
        except Exception as e:
            logger.error(f"知识搜索失败: {e}")
            return Response({
                'error': f'搜索失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchImportView(viewsets.GenericViewSet):
    """批量导入视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """批量导入数据"""
        serializer = BatchImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            kb_id = serializer.validated_data['knowledge_base_id']
            content_type = serializer.validated_data['content_type']
            file = serializer.validated_data['file']
            
            # 检查知识库权限
            kb = get_object_or_404(KnowledgeBase, id=kb_id)
            user = request.user
            
            if not (user.is_superuser or 
                   kb.created_by == user or
                   user.id in kb.permissions.get('editors', [])):
                return Response({
                    'error': '没有编辑该知识库的权限'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 根据内容类型选择导入服务
            if content_type == 'scripts':
                service = ScriptImportService(kb_id, user.id)
            elif content_type == 'products':
                service = ProductImportService(kb_id, user.id)
            else:
                return Response({
                    'error': f'不支持的内容类型: {content_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 执行导入
            result = service.import_from_file(file)
            
            return Response({
                'message': '数据导入完成',
                'content_type': content_type,
                'knowledge_base_id': kb_id,
                'result': result.to_dict()
            })
            
        except Exception as e:
            logger.error(f"批量导入失败: {e}")
            return Response({
                'error': f'导入失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def template(self, request):
        """获取导入模板"""
        content_type = request.query_params.get('content_type')
        
        if content_type == 'scripts':
            template = {
                'required_fields': ['name', 'script_type', 'content'],
                'optional_fields': ['priority', 'status', 'tags', 'variables', 'conditions'],
                'script_types': [choice[0] for choice in Script.ScriptType.choices],
                'example': {
                    'name': '产品介绍话术',
                    'script_type': 'product_intro',
                    'content': '您好，我们的产品具有以下特点...',
                    'priority': 1,
                    'status': 'active',
                    'tags': '产品,介绍',
                    'variables': '{"product_name": "产品名称"}',
                    'conditions': '{"scene": "product_inquiry"}'
                }
            }
        elif content_type == 'products':
            template = {
                'required_fields': ['sku', 'name', 'price'],
                'optional_fields': ['brand', 'product_category', 'description', 
                                  'short_description', 'stock_quantity', 'status', 
                                  'tags', 'specifications', 'attributes'],
                'statuses': [choice[0] for choice in Product.ProductStatus.choices],
                'example': {
                    'sku': 'P001',
                    'name': '示例产品',
                    'price': 99.99,
                    'brand': '品牌名称',
                    'product_category': '产品分类',
                    'description': '产品详细描述',
                    'short_description': '产品简短描述',
                    'stock_quantity': 100,
                    'status': 'active',
                    'tags': '标签1,标签2',
                    'specifications': '{"颜色": "红色", "尺寸": "L"}',
                    'attributes': '{"材质": "棉质", "产地": "中国"}'
                }
            }
        else:
            return Response({
                'error': '请指定content_type参数: scripts 或 products'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(template)

class KnowledgeSyncView(viewsets.GenericViewSet):
    """知识库同步视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def sync_updated(self, request):
        """同步最近更新的内容"""
        hours = request.data.get('hours', 24)
        
        try:
            # 启动增量同步任务
            task = sync_updated_content_task.delay(hours)
            
            return Response({
                'message': f'最近{hours}小时的内容同步任务已启动',
                'task_id': task.id,
                'hours': hours
            })
            
        except Exception as e:
            logger.error(f"启动增量同步任务失败: {e}")
            return Response({
                'error': f'启动同步任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 