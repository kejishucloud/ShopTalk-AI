"""
知识库API视图
支持话术和产品知识库的完整CRUD操作
"""

import logging
import csv
import io
from typing import Dict, Any, List
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import UploadedFile

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import KnowledgeBase, Script, Product, DocumentCategory, DocumentTag
from .serializers import (
    KnowledgeBaseSerializer, ScriptSerializer, ProductSerializer,
    DocumentCategorySerializer, DocumentTagSerializer
)
from .import_services import ScriptImportService, ProductImportService, get_import_template
from .kb_sync import kb_sync_service, sync_knowledge_base_task, sync_script_task, sync_product_task

logger = logging.getLogger(__name__)


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """知识库视图集"""
    
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户的知识库"""
        queryset = super().get_queryset()
        
        # 按知识库类型筛选
        kb_type = self.request.query_params.get('type')
        if kb_type:
            queryset = queryset.filter(knowledge_type=kb_type)
        
        # 按访问级别筛选
        access_level = self.request.query_params.get('access_level')
        if access_level:
            queryset = queryset.filter(access_level=access_level)
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """创建知识库"""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        summary="同步知识库到RAGFlow",
        description="将知识库同步到RAGFlow系统"
    )
    @action(detail=True, methods=['post'])
    def sync_to_ragflow(self, request, pk=None):
        """同步知识库到RAGFlow"""
        knowledge_base = self.get_object()
        
        try:
            # 异步执行同步任务
            task = sync_knowledge_base_task.delay(knowledge_base.id)
            
            return Response({
                'message': '同步任务已启动',
                'task_id': task.id,
                'knowledge_base_id': knowledge_base.id
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"启动同步任务失败: {e}")
            return Response({
                'error': f'启动同步任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="获取同步状态",
        description="获取知识库RAGFlow同步状态"
    )
    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """获取同步状态"""
        knowledge_base = self.get_object()
        
        try:
            status_info = kb_sync_service.get_sync_status(knowledge_base.id)
            return Response(status_info)
            
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return Response({
                'error': f'获取同步状态失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="搜索知识库",
        description="在RAGFlow中搜索知识库内容",
        parameters=[
            OpenApiParameter('query', str, description='搜索查询'),
            OpenApiParameter('top_k', int, description='返回结果数量', default=10),
        ]
    )
    @action(detail=True, methods=['post'])
    def search(self, request, pk=None):
        """搜索知识库"""
        knowledge_base = self.get_object()
        query = request.data.get('query', '')
        top_k = request.data.get('top_k', 10)
        
        if not query:
            return Response({
                'error': '查询不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            results = kb_sync_service.search_ragflow(knowledge_base.id, query, top_k)
            
            return Response({
                'query': query,
                'results': results,
                'total': len(results)
            })
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return Response({
                'error': f'搜索失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="获取知识库统计",
        description="获取知识库内容统计信息"
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取知识库统计"""
        knowledge_base = self.get_object()
        
        try:
            # 本地统计
            script_stats = Script.objects.filter(knowledge_base=knowledge_base).aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='active')),
                synced=Count('id', filter=Q(vector_synced=True))
            )
            
            product_stats = Product.objects.filter(knowledge_base=knowledge_base).aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='active')),
                synced=Count('id', filter=Q(vector_synced=True))
            )
            
            category_count = DocumentCategory.objects.filter(knowledge_base=knowledge_base).count()
            tag_count = DocumentTag.objects.filter(knowledge_base=knowledge_base).count()
            
            return Response({
                'scripts': script_stats,
                'products': product_stats,
                'categories': category_count,
                'tags': tag_count,
                'ragflow_synced': bool(knowledge_base.ragflow_kb_id)
            })
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return Response({
                'error': f'获取统计失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScriptViewSet(viewsets.ModelViewSet):
    """话术视图集"""
    
    queryset = Script.objects.all()
    serializer_class = ScriptSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]
    
    def get_queryset(self):
        """获取话术列表"""
        queryset = super().get_queryset()
        
        # 按知识库筛选
        kb_id = self.request.query_params.get('knowledge_base')
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id)
        
        # 按类型筛选
        script_type = self.request.query_params.get('script_type')
        if script_type:
            queryset = queryset.filter(script_type=script_type)
        
        # 按状态筛选
        script_status = self.request.query_params.get('status')
        if script_status:
            queryset = queryset.filter(status=script_status)
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(content__icontains=search)
            )
        
        return queryset.filter(knowledge_base__created_by=self.request.user)
    
    def perform_create(self, serializer):
        """创建话术"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """更新话术"""
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="同步话术到RAGFlow",
        description="将单个话术同步到RAGFlow"
    )
    @action(detail=True, methods=['post'])
    def sync_to_ragflow(self, request, pk=None):
        """同步话术到RAGFlow"""
        script = self.get_object()
        
        try:
            # 异步执行同步任务
            task = sync_script_task.delay(script.id)
            
            return Response({
                'message': '同步任务已启动',
                'task_id': task.id,
                'script_id': script.id
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"启动话术同步任务失败: {e}")
            return Response({
                'error': f'启动同步任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="批量导入话术",
        description="从CSV/Excel/JSON文件批量导入话术",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'knowledge_base_id': {'type': 'integer'}
                }
            }
        }
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_data(self, request):
        """批量导入话术"""
        file = request.FILES.get('file')
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        if not file:
            return Response({
                'error': '请选择要导入的文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not knowledge_base_id:
            return Response({
                'error': '请指定知识库ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取知识库
            knowledge_base = get_object_or_404(
                KnowledgeBase, 
                id=knowledge_base_id, 
                created_by=request.user
            )
            
            # 执行导入
            import_service = ScriptImportService(knowledge_base, request.user)
            result = import_service.import_data(file)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"导入话术失败: {e}")
            return Response({
                'error': f'导入失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="获取导入模板",
        description="下载话术导入模板文件"
    )
    @action(detail=False, methods=['get'])
    def import_template(self, request):
        """获取导入模板"""
        try:
            template = get_import_template('script')
            
            # 创建CSV文件
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{template["filename"]}"'
            response.write('\ufeff')  # BOM for Excel
            
            writer = csv.DictWriter(response, fieldnames=template['headers'])
            writer.writeheader()
            
            # 写入示例数据
            for sample in template['sample_data']:
                writer.writerow(sample)
            
            return response
            
        except Exception as e:
            logger.error(f"生成导入模板失败: {e}")
            return Response({
                'error': f'生成模板失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductViewSet(viewsets.ModelViewSet):
    """产品视图集"""
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]
    
    def get_queryset(self):
        """获取产品列表"""
        queryset = super().get_queryset()
        
        # 按知识库筛选
        kb_id = self.request.query_params.get('knowledge_base')
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id)
        
        # 按品牌筛选
        brand = self.request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand=brand)
        
        # 按分类筛选
        category = self.request.query_params.get('product_category')
        if category:
            queryset = queryset.filter(product_category=category)
        
        # 按状态筛选
        product_status = self.request.query_params.get('status')
        if product_status:
            queryset = queryset.filter(status=product_status)
        
        # 价格范围筛选
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.filter(knowledge_base__created_by=self.request.user)
    
    def perform_create(self, serializer):
        """创建产品"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """更新产品"""
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="同步产品到RAGFlow",
        description="将单个产品同步到RAGFlow"
    )
    @action(detail=True, methods=['post'])
    def sync_to_ragflow(self, request, pk=None):
        """同步产品到RAGFlow"""
        product = self.get_object()
        
        try:
            # 异步执行同步任务
            task = sync_product_task.delay(product.id)
            
            return Response({
                'message': '同步任务已启动',
                'task_id': task.id,
                'product_id': product.id
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"启动产品同步任务失败: {e}")
            return Response({
                'error': f'启动同步任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="批量导入产品",
        description="从CSV/Excel/JSON文件批量导入产品",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'knowledge_base_id': {'type': 'integer'}
                }
            }
        }
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_data(self, request):
        """批量导入产品"""
        file = request.FILES.get('file')
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        if not file:
            return Response({
                'error': '请选择要导入的文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not knowledge_base_id:
            return Response({
                'error': '请指定知识库ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取知识库
            knowledge_base = get_object_or_404(
                KnowledgeBase, 
                id=knowledge_base_id, 
                created_by=request.user
            )
            
            # 执行导入
            import_service = ProductImportService(knowledge_base, request.user)
            result = import_service.import_data(file)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"导入产品失败: {e}")
            return Response({
                'error': f'导入失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="获取导入模板",
        description="下载产品导入模板文件"
    )
    @action(detail=False, methods=['get'])
    def import_template(self, request):
        """获取导入模板"""
        try:
            template = get_import_template('product')
            
            # 创建CSV文件
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{template["filename"]}"'
            response.write('\ufeff')  # BOM for Excel
            
            writer = csv.DictWriter(response, fieldnames=template['headers'])
            writer.writeheader()
            
            # 写入示例数据
            for sample in template['sample_data']:
                writer.writerow(sample)
            
            return response
            
        except Exception as e:
            logger.error(f"生成导入模板失败: {e}")
            return Response({
                'error': f'生成模板失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """文档分类视图集"""
    
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取分类列表"""
        queryset = super().get_queryset()
        
        # 按知识库筛选
        kb_id = self.request.query_params.get('knowledge_base')
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id)
        
        return queryset.filter(knowledge_base__created_by=self.request.user)


class DocumentTagViewSet(viewsets.ModelViewSet):
    """文档标签视图集"""
    
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取标签列表"""
        queryset = super().get_queryset()
        
        # 按知识库筛选
        kb_id = self.request.query_params.get('knowledge_base')
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id)
        
        # 按使用次数排序
        order_by = self.request.query_params.get('order_by', '-usage_count')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset.filter(knowledge_base__created_by=self.request.user) 