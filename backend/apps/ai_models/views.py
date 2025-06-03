"""
AI模型管理模块视图
提供模型配置、调用、监控等API接口
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, Any

from .models import (
    AIModelProvider, AIModel, ModelCallRecord, ModelPerformance,
    ModelLoadBalancer, ModelWeight, ModelQuota
)
from .serializers import (
    AIModelProviderSerializer, AIModelSerializer, ModelCallRecordSerializer,
    ModelPerformanceSerializer, ModelLoadBalancerSerializer, ModelWeightSerializer,
    ModelQuotaSerializer, ModelCallRequestSerializer, ModelCallResponseSerializer,
    ModelComparisonSerializer, ModelBenchmarkSerializer
)
from .services import ModelCallService, LoadBalancerService, PerformanceMonitorService

logger = logging.getLogger('ai_models')


class AIModelProviderViewSet(viewsets.ModelViewSet):
    """AI模型提供商管理"""
    queryset = AIModelProvider.objects.all()
    serializer_class = AIModelProviderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按类型获取提供商"""
        provider_type = request.query_params.get('type')
        if not provider_type:
            return Response({'error': '缺少type参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        providers = self.get_queryset().filter(
            provider_type=provider_type,
            is_active=True
        )
        
        serializer = self.get_serializer(providers, many=True)
        return Response({
            'provider_type': provider_type,
            'providers': serializer.data,
            'count': providers.count()
        })


class AIModelViewSet(viewsets.ModelViewSet):
    """AI模型管理"""
    queryset = AIModel.objects.select_related('provider', 'created_by')
    serializer_class = AIModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'model_type', 'is_active']
    search_fields = ['name', 'model_id', 'description']
    ordering = ['-priority', 'name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def call(self, request):
        """
        调用AI模型
        POST /api/ai-models/call/
        """
        serializer = ModelCallRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            model = AIModel.objects.get(
                id=serializer.validated_data['model_id'],
                is_active=True
            )
        except AIModel.DoesNotExist:
            return Response({'error': '模型不存在或未激活'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # 获取客户端IP和User-Agent
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 调用模型
            service = ModelCallService()
            
            # 使用asyncio运行异步调用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(service.call_model(
                model=model,
                input_text=serializer.validated_data['input_text'],
                parameters={
                    'temperature': serializer.validated_data.get('temperature'),
                    'max_tokens': serializer.validated_data.get('max_tokens'),
                    'top_p': serializer.validated_data.get('top_p'),
                    'additional_params': serializer.validated_data.get('additional_params', {})
                },
                session_id=serializer.validated_data.get('session_id', ''),
                user=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            ))
            
            loop.close()
            
            # 序列化响应
            response_serializer = ModelCallResponseSerializer(data=result)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data)
            else:
                return Response(result)
            
        except Exception as e:
            logger.error(f"模型调用API失败: {str(e)}")
            return Response({
                'success': False,
                'error': '模型调用失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        模型对比测试
        POST /api/ai-models/compare/
        """
        serializer = ModelComparisonSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        model_ids = serializer.validated_data['model_ids']
        input_text = serializer.validated_data['input_text']
        parameters = serializer.validated_data.get('parameters', {})
        
        try:
            models = AIModel.objects.filter(
                id__in=model_ids,
                is_active=True
            )
            
            if models.count() != len(model_ids):
                return Response({'error': '部分模型不存在或未激活'}, status=status.HTTP_400_BAD_REQUEST)
            
            service = ModelCallService()
            comparison_results = []
            
            # 获取客户端信息
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            for model in models:
                try:
                    # 异步调用每个模型
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(service.call_model(
                        model=model,
                        input_text=input_text,
                        parameters=parameters,
                        user=request.user,
                        ip_address=ip_address,
                        user_agent=user_agent
                    ))
                    
                    loop.close()
                    
                    comparison_results.append({
                        'model_id': model.id,
                        'model_name': model.name,
                        'provider': model.provider.name,
                        'result': result
                    })
                    
                except Exception as e:
                    comparison_results.append({
                        'model_id': model.id,
                        'model_name': model.name,
                        'provider': model.provider.name,
                        'result': {
                            'success': False,
                            'error': str(e),
                            'error_type': 'comparison_failed'
                        }
                    })
            
            return Response({
                'input_text': input_text,
                'parameters': parameters,
                'results': comparison_results,
                'total_models': len(comparison_results)
            })
            
        except Exception as e:
            logger.error(f"模型对比失败: {str(e)}")
            return Response({
                'error': '模型对比失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def benchmark(self, request, pk=None):
        """
        模型基准测试
        POST /api/ai-models/{id}/benchmark/
        """
        model = self.get_object()
        serializer = ModelBenchmarkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        test_cases = serializer.validated_data['test_cases']
        parameters = serializer.validated_data.get('parameters', {})
        concurrent_requests = serializer.validated_data.get('concurrent_requests', 1)
        
        try:
            service = ModelCallService()
            benchmark_results = []
            
            # 获取客户端信息
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            for i, test_case in enumerate(test_cases):
                try:
                    start_time = timezone.now()
                    
                    # 运行测试用例
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(service.call_model(
                        model=model,
                        input_text=test_case,
                        parameters=parameters,
                        session_id=f"benchmark_{model.id}_{i}",
                        user=request.user,
                        ip_address=ip_address,
                        user_agent=user_agent
                    ))
                    
                    loop.close()
                    
                    end_time = timezone.now()
                    
                    benchmark_results.append({
                        'test_case_index': i,
                        'input_text': test_case,
                        'result': result,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat()
                    })
                    
                except Exception as e:
                    benchmark_results.append({
                        'test_case_index': i,
                        'input_text': test_case,
                        'result': {
                            'success': False,
                            'error': str(e),
                            'error_type': 'benchmark_failed'
                        }
                    })
            
            # 计算统计信息
            successful_tests = [r for r in benchmark_results if r['result'].get('success')]
            failed_tests = [r for r in benchmark_results if not r['result'].get('success')]
            
            if successful_tests:
                avg_response_time = sum(r['result'].get('response_time', 0) for r in successful_tests) / len(successful_tests)
                total_cost = sum(r['result'].get('cost', 0) for r in successful_tests)
                total_tokens = sum(r['result'].get('total_tokens', 0) for r in successful_tests)
            else:
                avg_response_time = 0
                total_cost = 0
                total_tokens = 0
            
            return Response({
                'model_id': model.id,
                'model_name': model.name,
                'test_cases_count': len(test_cases),
                'successful_tests': len(successful_tests),
                'failed_tests': len(failed_tests),
                'success_rate': (len(successful_tests) / len(test_cases) * 100) if test_cases else 0,
                'average_response_time': avg_response_time,
                'total_cost': total_cost,
                'total_tokens': total_tokens,
                'results': benchmark_results
            })
            
        except Exception as e:
            logger.error(f"基准测试失败: {str(e)}")
            return Response({
                'error': '基准测试失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """获取模型健康状态"""
        model = self.get_object()
        
        try:
            monitor_service = PerformanceMonitorService()
            health_status = monitor_service.get_model_health_status(model)
            
            return Response({
                'model_id': model.id,
                'model_name': model.name,
                'health_status': health_status,
                'is_active': model.is_active,
                'last_check': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"获取模型健康状态失败: {str(e)}")
            return Response({
                'error': '获取健康状态失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_capability(self, request):
        """按能力筛选模型"""
        capability = request.query_params.get('capability')
        if not capability:
            return Response({'error': '缺少capability参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        models = self.get_queryset().filter(
            capabilities__contains=[capability],
            is_active=True
        )
        
        serializer = self.get_serializer(models, many=True)
        return Response({
            'capability': capability,
            'models': serializer.data,
            'count': models.count()
        })

    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ModelCallRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """模型调用记录"""
    queryset = ModelCallRecord.objects.select_related('model', 'user')
    serializer_class = ModelCallRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['model', 'status', 'user']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """调用统计"""
        model_id = request.query_params.get('model_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        if model_id:
            queryset = queryset.filter(model_id=model_id)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # 基础统计
        total_calls = queryset.count()
        successful_calls = queryset.filter(status='success').count()
        failed_calls = queryset.filter(status='failed').count()
        
        # Token和成本统计
        token_stats = queryset.aggregate(
            total_input_tokens=Sum('input_tokens'),
            total_output_tokens=Sum('output_tokens'),
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost'),
            avg_response_time=Avg('response_time')
        )
        
        # 按模型分组统计
        model_stats = queryset.values(
            'model__name', 'model__provider__name'
        ).annotate(
            call_count=Count('id'),
            success_count=Count('id', filter=Q(status='success')),
            avg_cost=Avg('cost'),
            avg_response_time=Avg('response_time', filter=Q(status='success'))
        ).order_by('-call_count')[:10]
        
        return Response({
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
            'token_stats': token_stats,
            'top_models': list(model_stats)
        })


class ModelPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """模型性能统计"""
    queryset = ModelPerformance.objects.select_related('model')
    serializer_class = ModelPerformanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['model', 'date']
    ordering = ['-date', '-total_calls']

    @action(detail=False, methods=['post'])
    def update_daily(self, request):
        """更新每日性能统计"""
        date_str = request.data.get('date')
        
        try:
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date = timezone.now().date()
            
            monitor_service = PerformanceMonitorService()
            monitor_service.update_daily_performance(date)
            
            return Response({
                'success': True,
                'message': f'已更新 {date} 的性能统计',
                'date': date.isoformat()
            })
            
        except Exception as e:
            logger.error(f"更新性能统计失败: {str(e)}")
            return Response({
                'error': '更新失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """性能趋势数据"""
        model_id = request.query_params.get('model_id')
        days = int(request.query_params.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            date__range=[start_date, end_date]
        )
        
        if model_id:
            queryset = queryset.filter(model_id=model_id)
        
        trends_data = []
        for performance in queryset.order_by('date'):
            trends_data.append({
                'date': performance.date.isoformat(),
                'model_id': performance.model.id,
                'model_name': performance.model.name,
                'total_calls': performance.total_calls,
                'success_rate': performance.success_rate,
                'avg_response_time': performance.average_response_time,
                'total_cost': performance.total_cost
            })
        
        return Response({
            'period': f'{start_date} to {end_date}',
            'days': days,
            'trends': trends_data
        })


class ModelLoadBalancerViewSet(viewsets.ModelViewSet):
    """模型负载均衡管理"""
    queryset = ModelLoadBalancer.objects.prefetch_related('modelweight_set__model')
    serializer_class = ModelLoadBalancerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['strategy', 'is_active']
    search_fields = ['name']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def call(self, request, pk=None):
        """通过负载均衡器调用模型"""
        load_balancer = self.get_object()
        
        if not load_balancer.is_active:
            return Response({'error': '负载均衡器未激活'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ModelCallRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取客户端信息
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 通过负载均衡器调用
            service = LoadBalancerService()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(service.call_with_load_balancer(
                load_balancer=load_balancer,
                input_text=serializer.validated_data['input_text'],
                parameters={
                    'temperature': serializer.validated_data.get('temperature'),
                    'max_tokens': serializer.validated_data.get('max_tokens'),
                    'top_p': serializer.validated_data.get('top_p'),
                    'additional_params': serializer.validated_data.get('additional_params', {})
                },
                session_id=serializer.validated_data.get('session_id', ''),
                user=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            ))
            
            loop.close()
            
            result['load_balancer_id'] = load_balancer.id
            result['load_balancer_name'] = load_balancer.name
            result['strategy'] = load_balancer.strategy
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"负载均衡器调用失败: {str(e)}")
            return Response({
                'success': False,
                'error': '负载均衡器调用失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def add_model(self, request, pk=None):
        """添加模型到负载均衡器"""
        load_balancer = self.get_object()
        model_id = request.data.get('model_id')
        weight = request.data.get('weight', 1)
        
        try:
            model = AIModel.objects.get(id=model_id, is_active=True)
            
            model_weight, created = ModelWeight.objects.get_or_create(
                load_balancer=load_balancer,
                model=model,
                defaults={'weight': weight}
            )
            
            if not created:
                model_weight.weight = weight
                model_weight.save()
            
            return Response({
                'success': True,
                'message': f'模型 {model.name} 已{"添加到" if created else "更新在"}负载均衡器中',
                'weight': model_weight.weight
            })
            
        except AIModel.DoesNotExist:
            return Response({'error': '模型不存在或未激活'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': '添加模型失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'])
    def remove_model(self, request, pk=None):
        """从负载均衡器移除模型"""
        load_balancer = self.get_object()
        model_id = request.data.get('model_id')
        
        try:
            ModelWeight.objects.filter(
                load_balancer=load_balancer,
                model_id=model_id
            ).delete()
            
            return Response({
                'success': True,
                'message': '模型已从负载均衡器中移除'
            })
            
        except Exception as e:
            return Response({
                'error': '移除模型失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ModelQuotaViewSet(viewsets.ModelViewSet):
    """模型配额管理"""
    queryset = ModelQuota.objects.select_related('model', 'user')
    serializer_class = ModelQuotaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['model', 'user', 'quota_type', 'is_active']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def my_quotas(self, request):
        """获取当前用户的配额"""
        quotas = self.get_queryset().filter(
            user=request.user,
            is_active=True
        )
        
        serializer = self.get_serializer(quotas, many=True)
        return Response({
            'user_id': request.user.id,
            'username': request.user.username,
            'quotas': serializer.data,
            'total_quotas': quotas.count()
        })

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """重置配额使用量"""
        quota = self.get_object()
        
        quota.used_calls = 0
        quota.used_tokens = 0
        quota.used_cost = 0
        quota.last_reset = timezone.now()
        quota.save()
        
        return Response({
            'success': True,
            'message': '配额使用量已重置',
            'quota_id': quota.id,
            'reset_at': quota.last_reset.isoformat()
        }) 