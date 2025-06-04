"""
应用管理模块视图
对接多个应用（如微信公众号、小程序、Web端等）
统一管理接入参数、回调地址、鉴权规则
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import json
import hashlib
import hmac
from typing import Dict, Any

from .models import Application, AppConfig, AppCallback, AppAuth, AppStatistics
from .serializers import ApplicationSerializer, AppConfigSerializer, AppCallbackSerializer, AppAuthSerializer
from .services import (
    WeChatService, XiaohongshuService, TaobaoService, 
    JingdongService, PinduoduoService, WebChatService
)
from apps.chatbot.services import MessageProcessorService
from apps.chatbot.models import ChatSession
from apps.history.models import ChatMessage

logger = logging.getLogger('applications')


class ApplicationViewSet(viewsets.ModelViewSet):
    """应用管理"""
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['platform', 'status', 'is_active']
    search_fields = ['name', 'description', 'app_id']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活应用"""
        app = self.get_object()
        
        # 检查配置是否完整
        if not app.config:
            return Response({'error': '应用配置不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 根据平台初始化服务
            service = self._get_platform_service(app)
            if service:
                validation_result = service.validate_config()
                if not validation_result.get('valid'):
                    return Response({
                        'error': '配置验证失败',
                        'details': validation_result.get('errors', [])
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            app.status = 'active'
            app.activated_at = timezone.now()
            app.save()
            
            logger.info(f"应用已激活: {app.name} ({app.platform})")
            
            return Response({
                'success': True,
                'message': f'应用 {app.name} 已激活',
                'app_id': app.id,
                'status': app.status
            })
            
        except Exception as e:
            logger.error(f"激活应用失败: {app.name} - {str(e)}")
            return Response({
                'error': '激活应用失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """停用应用"""
        app = self.get_object()
        
        app.status = 'inactive'
        app.save()
        
        return Response({
            'success': True,
            'message': f'应用 {app.name} 已停用',
            'app_id': app.id,
            'status': app.status
        })

    @action(detail=True, methods=['get'])
    def status_detail(self, request, pk=None):
        """获取应用详细状态"""
        app = self.get_object()
        
        # 获取今日统计数据
        today = timezone.now().date()
        stats = AppStatistics.objects.filter(app=app, date=today).first()
        
        return Response({
            'app_id': app.id,
            'name': app.name,
            'platform': app.platform,
            'status': app.status,
            'is_active': app.is_active,
            'created_at': app.created_at,
            'activated_at': app.activated_at,
            'last_callback_at': app.last_callback_at,
            'today_stats': {
                'message_count': stats.message_count if stats else 0,
                'session_count': stats.session_count if stats else 0,
                'error_count': stats.error_count if stats else 0
            }
        })

    @method_decorator(csrf_exempt)
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def callback(self, request, pk=None):
        """
        应用回调接口
        POST /api/applications/{app_name}/callback/
        不同平台通过此接口推送消息和事件
        """
        try:
            app = self.get_object()
            
            if app.status != 'active':
                return Response({'error': '应用未激活'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证签名
            if not self._verify_signature(app, request):
                logger.warning(f"签名验证失败: {app.name}")
                return Response({'error': '签名验证失败'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 记录回调
            callback_record = AppCallback.objects.create(
                app=app,
                method=request.method,
                headers=dict(request.headers),
                body=request.body.decode('utf-8') if request.body else '',
                ip_address=self._get_client_ip(request)
            )
            
            # 更新应用最后回调时间
            app.last_callback_at = timezone.now()
            app.save(update_fields=['last_callback_at'])
            
            # 根据平台处理回调
            result = self._process_platform_callback(app, request, callback_record)
            
            # 更新回调记录
            callback_record.response_data = result
            callback_record.status = 'success' if result.get('success') else 'failed'
            callback_record.processed_at = timezone.now()
            callback_record.save()
            
            return Response(result.get('response', {'success': True}))
            
        except Exception as e:
            logger.error(f"处理回调失败: {str(e)}")
            
            # 记录错误
            if 'callback_record' in locals():
                callback_record.status = 'error'
                callback_record.error_message = str(e)
                callback_record.processed_at = timezone.now()
                callback_record.save()
            
            return Response({
                'error': '处理失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_platform_service(self, app: Application):
        """获取平台服务实例"""
        services = {
            'wechat': WeChatService,
            'xiaohongshu': XiaohongshuService,
            'taobao': TaobaoService,
            'jingdong': JingdongService,
            'pinduoduo': PinduoduoService,
            'webchat': WebChatService
        }
        
        service_class = services.get(app.platform)
        if service_class:
            return service_class(app)
        return None

    def _verify_signature(self, app: Application, request) -> bool:
        """验证回调签名"""
        try:
            auth_config = app.auth_config or {}
            signature_method = auth_config.get('signature_method', 'none')
            
            if signature_method == 'none':
                return True
            
            service = self._get_platform_service(app)
            if service:
                return service.verify_signature(request)
            
            return True
            
        except Exception as e:
            logger.error(f"签名验证异常: {str(e)}")
            return False

    def _process_platform_callback(self, app: Application, request, callback_record) -> Dict[str, Any]:
        """处理平台回调"""
        try:
            service = self._get_platform_service(app)
            
            if not service:
                return {'success': False, 'error': f'不支持的平台: {app.platform}'}
            
            # 解析回调数据
            callback_data = service.parse_callback(request)
            
            if not callback_data.get('valid'):
                return {'success': False, 'error': '回调数据格式错误'}
            
            # 处理不同类型的事件
            event_type = callback_data.get('event_type')
            
            if event_type == 'message':
                return self._handle_message_event(app, callback_data, service)
            elif event_type == 'event':
                return self._handle_system_event(app, callback_data, service)
            else:
                return {'success': True, 'message': '事件已接收'}
            
        except Exception as e:
            logger.error(f"处理平台回调异常: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _handle_message_event(self, app: Application, callback_data: dict, service) -> Dict[str, Any]:
        """处理消息事件"""
        try:
            message_data = callback_data.get('message', {})
            user_id = message_data.get('user_id')
            content = message_data.get('content', '')
            message_type = message_data.get('type', 'text')
            
            if not user_id or not content:
                return {'success': False, 'error': '消息数据不完整'}
            
            # 获取或创建聊天会话
            session, created = ChatSession.objects.get_or_create(
                platform_user_id=user_id,
                app_name=app.name,
                platform=app.platform,
                defaults={
                    'status': 'active',
                    'created_at': timezone.now()
                }
            )
            
            # 保存用户消息
            user_message = ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=content,
                metadata={
                    'platform_message_id': message_data.get('message_id'),
                    'message_type': message_type,
                    'raw_data': message_data
                }
            )
            
            # 使用智能体处理消息
            processor = MessageProcessorService()
            response_result = processor.process_message(
                session=session,
                user_message=user_message,
                app=app
            )
            
            # 保存机器人回复
            if response_result.get('response'):
                bot_message = ChatMessage.objects.create(
                    session=session,
                    message_type='bot',
                    content=response_result['response'],
                    metadata={
                        'agent_id': response_result.get('agent_id'),
                        'confidence': response_result.get('confidence', 1.0),
                        'processing_time': response_result.get('processing_time', 0)
                    }
                )
                
                # 发送回复到平台
                send_result = service.send_message(
                    user_id=user_id,
                    content=response_result['response'],
                    message_type='text'
                )
                
                if send_result.get('success'):
                    bot_message.metadata['platform_message_id'] = send_result.get('message_id')
                    bot_message.save()
            
            # 检查是否需要转人工
            if response_result.get('human_handoff_required'):
                session.status = 'transferred_to_human'
                session.save()
                
                # 发送转人工通知
                service.send_message(
                    user_id=user_id,
                    content="您的问题已转接至人工客服，请稍等...",
                    message_type='text'
                )
            
            # 更新应用统计
            self._update_app_statistics(app, 'message')
            
            return {
                'success': True,
                'session_id': session.id,
                'response': response_result.get('response', ''),
                'human_handoff': response_result.get('human_handoff_required', False)
            }
            
        except Exception as e:
            logger.error(f"处理消息事件失败: {str(e)}")
            self._update_app_statistics(app, 'error')
            return {'success': False, 'error': str(e)}

    def _handle_system_event(self, app: Application, callback_data: dict, service) -> Dict[str, Any]:
        """处理系统事件"""
        try:
            event_data = callback_data.get('event', {})
            event_name = event_data.get('name')
            
            logger.info(f"收到系统事件: {app.platform} - {event_name}")
            
            # 根据事件类型处理
            if event_name == 'user_follow':
                # 用户关注事件
                return self._handle_user_follow(app, event_data, service)
            elif event_name == 'user_unfollow':
                # 用户取消关注事件
                return self._handle_user_unfollow(app, event_data, service)
            else:
                return {'success': True, 'message': f'事件 {event_name} 已记录'}
            
        except Exception as e:
            logger.error(f"处理系统事件失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _handle_user_follow(self, app: Application, event_data: dict, service) -> Dict[str, Any]:
        """处理用户关注事件"""
        user_id = event_data.get('user_id')
        
        if user_id:
            # 发送欢迎消息
            welcome_message = app.config.get('welcome_message', '欢迎关注！我是智能客服助手，有什么可以帮助您的吗？')
            
            service.send_message(
                user_id=user_id,
                content=welcome_message,
                message_type='text'
            )
        
        return {'success': True, 'message': '欢迎消息已发送'}

    def _handle_user_unfollow(self, app: Application, event_data: dict, service) -> Dict[str, Any]:
        """处理用户取消关注事件"""
        user_id = event_data.get('user_id')
        
        if user_id:
            # 更新会话状态
            ChatSession.objects.filter(
                platform_user_id=user_id,
                app_name=app.name
            ).update(status='user_unfollowed')
        
        return {'success': True, 'message': '用户取消关注已记录'}

    def _update_app_statistics(self, app: Application, stat_type: str):
        """更新应用统计"""
        try:
            today = timezone.now().date()
            stats, created = AppStatistics.objects.get_or_create(
                app=app,
                date=today,
                defaults={
                    'message_count': 0,
                    'session_count': 0,
                    'error_count': 0
                }
            )
            
            if stat_type == 'message':
                stats.message_count += 1
            elif stat_type == 'session':
                stats.session_count += 1
            elif stat_type == 'error':
                stats.error_count += 1
            
            stats.save()
            
        except Exception as e:
            logger.error(f"更新应用统计失败: {str(e)}")

    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AppConfigViewSet(viewsets.ModelViewSet):
    """应用配置管理"""
    queryset = AppConfig.objects.select_related('app')
    serializer_class = AppConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['app', 'config_type']
    ordering = ['-updated_at']


class AppCallbackViewSet(viewsets.ReadOnlyModelViewSet):
    """应用回调记录"""
    queryset = AppCallback.objects.select_related('app')
    serializer_class = AppCallbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['app', 'status', 'method']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """回调统计"""
        app_id = request.query_params.get('app_id')
        queryset = self.get_queryset()
        
        if app_id:
            queryset = queryset.filter(app_id=app_id)
        
        total = queryset.count()
        success = queryset.filter(status='success').count()
        failed = queryset.filter(status='failed').count()
        error = queryset.filter(status='error').count()
        
        return Response({
            'total_callbacks': total,
            'success': success,
            'failed': failed,
            'error': error,
            'success_rate': round((success / total * 100) if total > 0 else 0, 2)
        })


class AppAuthViewSet(viewsets.ModelViewSet):
    """应用认证配置"""
    queryset = AppAuth.objects.select_related('app')
    serializer_class = AppAuthSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['app', 'auth_type']
    ordering = ['-created_at'] 