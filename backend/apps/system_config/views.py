from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ConfigCategory, SystemConfig, ConfigGroup
from .serializers import (
    ConfigCategorySerializer, SystemConfigSerializer, ConfigGroupSerializer,
    ConfigCategoryDetailSerializer, ConfigUpdateSerializer
)


class ConfigCategoryViewSet(viewsets.ModelViewSet):
    """配置分类视图集"""
    queryset = ConfigCategory.objects.filter(is_active=True)
    serializer_class = ConfigCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    @action(detail=True, methods=['get'])
    def detail_with_configs(self, request, pk=None):
        """获取配置分类及其下的所有配置项"""
        category = get_object_or_404(ConfigCategory, pk=pk, is_active=True)
        serializer = ConfigCategoryDetailSerializer(category)
        return Response(serializer.data)


class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置视图集"""
    queryset = SystemConfig.objects.filter(is_active=True)
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'config_type', 'is_required', 'is_encrypted']
    search_fields = ['key', 'display_name', 'description']
    ordering_fields = ['order', 'key', 'created_at']
    ordering = ['category__order', 'order', 'key']

    def get_permissions(self):
        """根据操作类型设置权限"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类获取配置项"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response({'error': '需要提供category_id参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        configs = self.get_queryset().filter(category_id=category_id)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """批量更新配置"""
        serializer = ConfigUpdateSerializer(data=request.data)
        if serializer.is_valid():
            configs_data = serializer.validated_data['configs']
            
            with transaction.atomic():
                updated_configs = []
                errors = []
                
                for config_data in configs_data:
                    key = config_data['key']
                    value = config_data['value']
                    
                    try:
                        config = SystemConfig.objects.get(key=key, is_active=True)
                        config.set_value(value)
                        updated_configs.append({
                            'key': key,
                            'old_value': config.value,
                            'new_value': value
                        })
                    except SystemConfig.DoesNotExist:
                        errors.append(f'配置项 {key} 不存在')
                    except Exception as e:
                        errors.append(f'更新配置项 {key} 时出错: {str(e)}')
                
                if errors:
                    return Response({
                        'success': False,
                        'errors': errors,
                        'updated': updated_configs
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'success': True,
                    'message': f'成功更新了 {len(updated_configs)} 个配置项',
                    'updated': updated_configs
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_by_key(self, request):
        """根据key获取配置值"""
        key = request.query_params.get('key')
        if not key:
            return Response({'error': '需要提供key参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = SystemConfig.objects.get(key=key, is_active=True)
            return Response({
                'key': config.key,
                'value': config.get_value(),
                'display_name': config.display_name,
                'description': config.description
            })
        except SystemConfig.DoesNotExist:
            return Response({'error': f'配置项 {key} 不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def set_by_key(self, request):
        """根据key设置配置值"""
        key = request.data.get('key')
        value = request.data.get('value')
        
        if not key:
            return Response({'error': '需要提供key参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = SystemConfig.objects.get(key=key, is_active=True)
            config.set_value(value)
            return Response({
                'success': True,
                'message': f'配置项 {key} 更新成功',
                'key': config.key,
                'value': config.get_value()
            })
        except SystemConfig.DoesNotExist:
            return Response({'error': f'配置项 {key} 不存在'}, status=status.HTTP_404_NOT_FOUND)


class ConfigGroupViewSet(viewsets.ModelViewSet):
    """配置组视图集"""
    queryset = ConfigGroup.objects.all()
    serializer_class = ConfigGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['order', 'name']
    ordering = ['category__order', 'order', 'name']

    def get_permissions(self):
        """根据操作类型设置权限"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes] 