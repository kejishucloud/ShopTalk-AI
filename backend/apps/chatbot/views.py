"""
智能客服管理模块视图
将不同应用、平台（小红书、电商、PDD、淘宝、京东等）的对接配置集中管理
提供实时状态监控API和转人工客服接口
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
import logging
from typing import Dict, Any

from .models import ChatbotConfig, ChatSession, HumanHandoff, ChatStatistics, AgentPerformance
from .serializers import (
    ChatbotConfigSerializer, ChatSessionSerializer, HumanHandoffSerializer,
    ChatStatisticsSerializer, AgentPerformanceSerializer
)
from .services import MessageProcessorService, HumanHandoffService, ChatAnalyticsService
from apps.history.models import ChatMessage
from apps.keywords.models import KeywordMatch
from apps.agents_mgmt.models import Agent

logger = logging.getLogger('chatbot')


class ChatbotConfigViewSet(viewsets.ModelViewSet):
    """智能客服配置管理"""
    queryset = ChatbotConfig.objects.all()
    serializer_class = ChatbotConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['platform', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-updated_at']

    @action(detail=False, methods=['get'])
    def platform_configs(self, request):
        """获取各平台配置"""
        platform = request.query_params.get('platform')
        
        queryset = self.get_queryset()
        if platform:
            queryset = queryset.filter(platform=platform)
        
        configs = queryset.filter(is_active=True)
        serializer = self.get_serializer(configs, many=True)
        
        return Response({
            'platform': platform,
            'configs': serializer.data,
            'total': configs.count()
        })


class ChatSessionViewSet(viewsets.ModelViewSet):
    """聊天会话管理"""
    queryset = ChatSession.objects.select_related('user', 'assigned_agent')
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['platform', 'status', 'app_name']
    search_fields = ['platform_user_id', 'user__username']
    ordering = ['-updated_at']

    @action(detail=False, methods=['get'])
    def active_sessions(self, request):
        """获取活跃会话"""
        platform = request.query_params.get('platform')
        limit = int(request.query_params.get('limit', 20))
        
        queryset = self.get_queryset().filter(
            status__in=['active', 'waiting_human'],
            updated_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        if platform:
            queryset = queryset.filter(platform=platform)
        
        sessions = queryset.order_by('-updated_at')[:limit]
        serializer = self.get_serializer(sessions, many=True)
        
        return Response({
            'active_sessions': serializer.data,
            'total': sessions.count(),
            'platform': platform
        })

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """获取会话消息"""
        session = self.get_object()
        
        messages = ChatMessage.objects.filter(
            session=session
        ).order_by('created_at')
        
        message_data = []
        for message in messages:
            message_data.append({
                'id': message.id,
                'type': message.message_type,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'metadata': message.metadata
            })
        
        return Response({
            'session_id': session.id,
            'messages': message_data,
            'total_messages': len(message_data),
            'session_status': session.status
        })

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """发送消息到会话"""
        session = self.get_object()
        content = request.data.get('content', '')
        message_type = request.data.get('type', 'bot')
        
        if not content:
            return Response({'error': '消息内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 创建消息记录
            message = ChatMessage.objects.create(
                session=session,
                message_type=message_type,
                content=content,
                user=request.user if message_type == 'human' else None,
                metadata={
                    'sent_by_api': True,
                    'sender_user_id': request.user.id
                }
            )
            
            # 更新会话时间
            session.updated_at = timezone.now()
            session.save()
            
            # 如果是人工客服发送，需要通过对应平台发送消息
            if message_type == 'human':
                from apps.applications.models import Application
                app = Application.objects.filter(
                    name=session.app_name,
                    platform=session.platform,
                    status='active'
                ).first()
                
                if app:
                    from apps.applications.services import get_platform_service
                    service = get_platform_service(app)
                    if service:
                        send_result = service.send_message(
                            user_id=session.platform_user_id,
                            content=content,
                            message_type='text'
                        )
                        
                        if send_result.get('success'):
                            message.metadata['platform_message_id'] = send_result.get('message_id')
                            message.metadata['send_status'] = 'sent'
                        else:
                            message.metadata['send_status'] = 'failed'
                            message.metadata['send_error'] = send_result.get('error')
                        
                        message.save()
            
            return Response({
                'success': True,
                'message_id': message.id,
                'session_id': session.id,
                'content': content,
                'type': message_type,
                'created_at': message.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return Response({
                'error': '发送消息失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HumanHandoffViewSet(viewsets.ModelViewSet):
    """人工接入管理"""
    queryset = HumanHandoff.objects.select_related('session', 'triggered_by', 'assigned_agent')
    serializer_class = HumanHandoffSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'trigger_reason']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'])
    def transfer_to_human(self, request):
        """
        转人工客服接口
        前端调用：POST /api/chatbot/human-handoff/transfer_to_human/
        """
        session_id = request.data.get('session_id')
        reason = request.data.get('reason', 'user_request')
        priority = request.data.get('priority', 'normal')
        context = request.data.get('context', {})
        
        if not session_id:
            return Response({'error': '缺少session_id参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.history.models import ChatSession
            session = ChatSession.objects.get(id=session_id)
            
            # 检查是否已经在人工接入队列中
            existing_handoff = HumanHandoff.objects.filter(
                session=session,
                status__in=['pending', 'assigned']
            ).first()
            
            if existing_handoff:
                return Response({
                    'error': '该会话已在人工接入队列中',
                    'handoff_id': existing_handoff.id,
                    'status': existing_handoff.status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建人工接入记录
            handoff = HumanHandoff.objects.create(
                session=session,
                trigger_reason=reason,
                priority=priority,
                context_data=context,
                triggered_by=request.user,
                status='pending'
            )
            
            # 更新会话状态
            session.status = 'waiting_human'
            session.save()
            
            # 使用人工接入服务处理分配
            handoff_service = HumanHandoffService()
            assignment_result = handoff_service.assign_agent(handoff)
            
            # 记录转接消息
            ChatMessage.objects.create(
                session=session,
                message_type='system',
                content=f"您的问题已转接至人工客服，原因：{reason}。请稍等，客服将尽快为您服务。",
                metadata={
                    'handoff_id': handoff.id,
                    'transfer_reason': reason,
                    'priority': priority
                }
            )
            
            # 如果成功分配了客服
            if assignment_result.get('assigned'):
                handoff.assigned_agent = assignment_result['agent']
                handoff.assigned_at = timezone.now()
                handoff.status = 'assigned'
                handoff.save()
                
                session.status = 'human_assigned'
                session.save()
                
                return Response({
                    'success': True,
                    'handoff_id': handoff.id,
                    'status': 'assigned',
                    'assigned_agent': assignment_result['agent'].username,
                    'message': '已成功分配人工客服',
                    'estimated_wait_time': assignment_result.get('estimated_wait_time', 0)
                })
            else:
                return Response({
                    'success': True,
                    'handoff_id': handoff.id,
                    'status': 'pending',
                    'message': '已加入人工客服队列，请耐心等待',
                    'queue_position': assignment_result.get('queue_position', 0),
                    'estimated_wait_time': assignment_result.get('estimated_wait_time', 300)
                })
                
        except ChatSession.DoesNotExist:
            return Response({
                'error': '会话不存在',
                'session_id': session_id
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"转人工客服失败: {str(e)}")
            return Response({
                'error': '转人工客服失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def assign_agent(self, request, pk=None):
        """分配客服代理"""
        handoff = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if handoff.status != 'pending':
            return Response({'error': '该转接请求状态不允许分配'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.contrib.auth.models import User
            agent = User.objects.get(id=agent_id)
            
            handoff.assigned_agent = agent
            handoff.assigned_at = timezone.now()
            handoff.status = 'assigned'
            handoff.save()
            
            # 更新会话状态
            handoff.session.status = 'human_assigned'
            handoff.session.save()
            
            # 发送分配通知消息
            ChatMessage.objects.create(
                session=handoff.session,
                message_type='system',
                content=f"客服 {agent.get_full_name() or agent.username} 已为您服务。",
                metadata={
                    'handoff_id': handoff.id,
                    'assigned_agent_id': agent.id
                }
            )
            
            return Response({
                'success': True,
                'handoff_id': handoff.id,
                'assigned_agent': agent.username,
                'assigned_at': handoff.assigned_at.isoformat()
            })
            
        except User.DoesNotExist:
            return Response({'error': '客服代理不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"分配客服失败: {str(e)}")
            return Response({
                'error': '分配客服失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成人工服务"""
        handoff = self.get_object()
        resolution = request.data.get('resolution', '')
        rating = request.data.get('rating')  # 用户评分
        
        if handoff.status != 'assigned':
            return Response({'error': '该转接请求状态不允许完成'}, status=status.HTTP_400_BAD_REQUEST)
        
        handoff.status = 'completed'
        handoff.completed_at = timezone.now()
        handoff.resolution = resolution
        handoff.user_rating = rating
        handoff.save()
        
        # 更新会话状态
        handoff.session.status = 'completed'
        handoff.session.save()
        
        # 记录完成消息
        ChatMessage.objects.create(
            session=handoff.session,
            message_type='system',
            content="人工客服已结束服务。感谢您的使用！",
            metadata={
                'handoff_id': handoff.id,
                'resolution': resolution,
                'rating': rating
            }
        )
        
        return Response({
            'success': True,
            'handoff_id': handoff.id,
            'completed_at': handoff.completed_at.isoformat(),
            'resolution': resolution
        })

    @action(detail=False, methods=['get'])
    def queue_status(self, request):
        """获取人工接入队列状态"""
        pending_count = self.get_queryset().filter(status='pending').count()
        assigned_count = self.get_queryset().filter(status='assigned').count()
        
        # 计算平均等待时间
        completed_handoffs = self.get_queryset().filter(
            status='completed',
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        
        avg_wait_time = 0
        if completed_handoffs.exists():
            wait_times = []
            for handoff in completed_handoffs:
                if handoff.assigned_at:
                    wait_time = (handoff.assigned_at - handoff.created_at).total_seconds()
                    wait_times.append(wait_time)
            
            if wait_times:
                avg_wait_time = sum(wait_times) / len(wait_times)
        
        # 获取可用客服数量
        from django.contrib.auth.models import User
        available_agents = User.objects.filter(
            groups__name='customer_service',
            is_active=True
        ).count()
        
        return Response({
            'pending_count': pending_count,
            'assigned_count': assigned_count,
            'available_agents': available_agents,
            'average_wait_time': int(avg_wait_time),
            'estimated_wait_time': max(int(avg_wait_time * (pending_count / max(available_agents, 1))), 60)
        })


class ChatStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """聊天统计数据"""
    queryset = ChatStatistics.objects.all()
    serializer_class = ChatStatisticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date']
    ordering = ['-date']

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """仪表板统计数据"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # 今日数据
        today_stats = self.get_queryset().filter(date=today).first()
        yesterday_stats = self.get_queryset().filter(date=yesterday).first()
        
        # 一周数据
        week_stats = self.get_queryset().filter(
            date__gte=week_ago
        ).aggregate(
            total_sessions=Count('total_sessions'),
            total_messages=Count('total_messages'),
            total_handoffs=Count('handoff_count')
        )
        
        # 实时数据
        active_sessions = ChatSession.objects.filter(
            status__in=['active', 'waiting_human', 'human_assigned'],
            updated_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        pending_handoffs = HumanHandoff.objects.filter(
            status='pending'
        ).count()
        
        return Response({
            'today': {
                'sessions': today_stats.total_sessions if today_stats else 0,
                'messages': today_stats.total_messages if today_stats else 0,
                'handoffs': today_stats.handoff_count if today_stats else 0,
                'handoff_rate': today_stats.handoff_rate if today_stats else 0.0
            },
            'yesterday': {
                'sessions': yesterday_stats.total_sessions if yesterday_stats else 0,
                'messages': yesterday_stats.total_messages if yesterday_stats else 0,
                'handoffs': yesterday_stats.handoff_count if yesterday_stats else 0,
                'handoff_rate': yesterday_stats.handoff_rate if yesterday_stats else 0.0
            },
            'week_total': week_stats,
            'realtime': {
                'active_sessions': active_sessions,
                'pending_handoffs': pending_handoffs
            }
        })

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """趋势数据"""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        stats = self.get_queryset().filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        trends_data = []
        for stat in stats:
            trends_data.append({
                'date': stat.date.isoformat(),
                'sessions': stat.total_sessions,
                'messages': stat.total_messages,
                'user_messages': stat.user_messages,
                'bot_messages': stat.bot_messages,
                'handoffs': stat.handoff_count,
                'handoff_rate': stat.handoff_rate
            })
        
        return Response({
            'period': f'{start_date} to {end_date}',
            'days': days,
            'trends': trends_data
        })


class AgentPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """智能体性能监控"""
    queryset = AgentPerformance.objects.select_related('agent')
    serializer_class = AgentPerformanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent', 'date']
    ordering = ['-date', '-total_requests']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """性能概览"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # 聚合数据
        summary = queryset.aggregate(
            total_requests=Count('total_requests'),
            avg_response_time=Avg('average_response_time'),
            avg_success_rate=Avg('success_rate')
        )
        
        # 获取最活跃的智能体
        top_agents = queryset.values(
            'agent__name'
        ).annotate(
            total_reqs=Count('total_requests')
        ).order_by('-total_reqs')[:5]
        
        return Response({
            'summary': summary,
            'top_agents': list(top_agents),
            'period': {
                'from': date_from,
                'to': date_to
            }
        }) 