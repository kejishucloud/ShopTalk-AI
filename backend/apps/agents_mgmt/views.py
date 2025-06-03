"""
智能体管理模块视图
管理多个智能体实例，支持启动/停止、参数配置、日志记录
展示如何调用标签和关键词模块API
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
import logging
import asyncio
import requests
from typing import Dict, Any

from .models import Agent, AgentConfig, AgentExecution, AgentLog
from .serializers import AgentSerializer, AgentConfigSerializer, AgentExecutionSerializer, AgentLogSerializer
from .services import AgentManagerService
from agents import AgentManager, TagAgent, SentimentAgent
from apps.tags.models import TagRule
from apps.keywords.models import Keyword

logger = logging.getLogger('agents')


class AgentViewSet(viewsets.ModelViewSet):
    """智能体管理"""
    queryset = Agent.objects.select_related('config')
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'agent_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动智能体"""
        agent = self.get_object()
        if agent.status == 'running':
            return Response({'error': '智能体已在运行中'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = AgentManagerService()
            result = service.start_agent(agent)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': f'智能体 {agent.name} 启动成功',
                    'agent_id': agent.id,
                    'pid': result.get('pid')
                })
            else:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"启动智能体失败: {str(e)}")
            return Response({
                'error': '启动智能体失败'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止智能体"""
        agent = self.get_object()
        if agent.status != 'running':
            return Response({'error': '智能体未在运行'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = AgentManagerService()
            result = service.stop_agent(agent)
            
            return Response({
                'success': True,
                'message': f'智能体 {agent.name} 已停止',
                'agent_id': agent.id
            })
            
        except Exception as e:
            logger.error(f"停止智能体失败: {str(e)}")
            return Response({
                'error': '停止智能体失败'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def status_detail(self, request, pk=None):
        """获取智能体详细状态"""
        agent = self.get_object()
        service = AgentManagerService()
        
        return Response({
            'agent_id': agent.id,
            'name': agent.name,
            'status': agent.status,
            'uptime': service.get_uptime(agent),
            'memory_usage': service.get_memory_usage(agent),
            'cpu_usage': service.get_cpu_usage(agent),
            'last_execution': agent.last_execution_at,
            'total_executions': agent.total_executions,
            'success_rate': service.calculate_success_rate(agent)
        })

    @action(detail=True, methods=['post'])
    def process_message(self, request, pk=None):
        """
        处理消息 - 展示智能体如何调用tags和keywords模块
        这是智能体处理用户消息的核心API
        """
        agent = self.get_object()
        message = request.data.get('message', '')
        user_id = request.data.get('user_id')
        session_id = request.data.get('session_id')
        
        if not message:
            return Response({'error': '缺少message参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 记录执行开始
            execution = AgentExecution.objects.create(
                agent=agent,
                input_data={'message': message, 'user_id': user_id, 'session_id': session_id},
                status='running',
                started_at=timezone.now()
            )
            
            # 1. 调用标签模块获取意图规则
            intent_result = self._get_intent_rules(message)
            
            # 2. 调用关键词模块检查是否需要人工接入
            human_handoff_result = self._check_human_handoff(message)
            
            # 3. 使用智能体处理消息
            if agent.agent_type == 'tag_agent':
                agent_result = self._process_with_tag_agent(message, intent_result)
            elif agent.agent_type == 'sentiment_agent':
                agent_result = self._process_with_sentiment_agent(message)
            else:
                agent_result = self._process_with_default_agent(message)
            
            # 4. 如果识别到标签，自动分配给消息记录
            if agent_result.get('tags'):
                self._assign_tags_to_message(session_id, agent_result['tags'])
            
            # 更新执行记录
            execution.output_data = {
                'intent_rules': intent_result,
                'human_handoff': human_handoff_result,
                'agent_response': agent_result,
                'processing_time': (timezone.now() - execution.started_at).total_seconds()
            }
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.save()
            
            # 更新智能体统计
            agent.total_executions += 1
            agent.last_execution_at = timezone.now()
            agent.save()
            
            return Response({
                'success': True,
                'execution_id': execution.id,
                'response': agent_result.get('response', ''),
                'tags': agent_result.get('tags', []),
                'intent': intent_result.get('intent'),
                'human_handoff_required': human_handoff_result.get('required', False),
                'confidence': agent_result.get('confidence', 1.0),
                'processing_time': execution.output_data['processing_time']
            })
            
        except Exception as e:
            logger.error(f"智能体处理消息失败: {str(e)}")
            
            # 更新执行记录为失败状态
            if 'execution' in locals():
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.completed_at = timezone.now()
                execution.save()
            
            return Response({
                'error': '消息处理失败',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_intent_rules(self, message: str) -> Dict[str, Any]:
        """调用标签模块获取意图匹配规则"""
        try:
            # 示例：智能体调用 GET /api/tags/rules/?intent={intent}
            from apps.tags.services import TagMatchingService
            
            service = TagMatchingService()
            intent = service.extract_intent(message)  # 智能体提取意图
            
            # 调用标签模块API获取规则
            url = f"/api/v1/tags/rules/by_intent/?intent={intent}"
            # 这里应该使用内部API调用，示例中简化处理
            rules = TagRule.objects.filter(
                rule_type='intent',
                conditions__intent=intent,
                is_active=True
            )
            
            return {
                'intent': intent,
                'matched_rules': [
                    {
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'target_tags': [tag.name for tag in rule.target_tags.all()]
                    }
                    for rule in rules
                ],
                'count': rules.count()
            }
            
        except Exception as e:
            logger.error(f"获取意图规则失败: {str(e)}")
            return {'intent': None, 'matched_rules': [], 'count': 0}

    def _check_human_handoff(self, message: str) -> Dict[str, Any]:
        """调用关键词模块检查是否需要人工接入"""
        try:
            # 示例：智能体调用 GET /api/keywords/check/?text={latest_message}
            from apps.keywords.services import KeywordMatchingService
            
            service = KeywordMatchingService()
            result = service.check_human_handoff(message)
            
            return {
                'required': result.get('human_handoff_required', False),
                'matched_keywords': result.get('matched_keywords', []),
                'confidence': result.get('confidence', 0.0),
                'reason': result.get('reason', '')
            }
            
        except Exception as e:
            logger.error(f"检查人工接入失败: {str(e)}")
            return {'required': False, 'matched_keywords': [], 'confidence': 0.0}

    def _process_with_tag_agent(self, message: str, intent_result: Dict) -> Dict[str, Any]:
        """使用标签智能体处理消息"""
        try:
            tag_agent = TagAgent("tag_processor")
            
            input_data = {
                'text': message,
                'intent': intent_result.get('intent'),
                'rules': intent_result.get('matched_rules', [])
            }
            
            # 异步调用智能体
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(tag_agent.safe_process(input_data))
            loop.close()
            
            return {
                'response': '已识别并处理标签',
                'tags': result.get('data', {}).get('identified_tags', []),
                'confidence': result.get('data', {}).get('confidence', 1.0)
            }
            
        except Exception as e:
            logger.error(f"标签智能体处理失败: {str(e)}")
            return {'response': '标签处理失败', 'tags': [], 'confidence': 0.0}

    def _process_with_sentiment_agent(self, message: str) -> Dict[str, Any]:
        """使用情感分析智能体处理消息"""
        try:
            sentiment_agent = SentimentAgent("sentiment_analyzer")
            
            input_data = {'text': message}
            
            # 异步调用智能体
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(sentiment_agent.safe_process(input_data))
            loop.close()
            
            sentiment = result.get('data', {}).get('sentiment', 'neutral')
            tags = []
            
            # 根据情感分析结果生成标签
            if sentiment == 'negative':
                tags.append('负面情感')
            elif sentiment == 'positive':
                tags.append('正面情感')
            
            return {
                'response': f'情感分析完成：{sentiment}',
                'tags': tags,
                'confidence': result.get('data', {}).get('confidence', 1.0),
                'sentiment': sentiment
            }
            
        except Exception as e:
            logger.error(f"情感智能体处理失败: {str(e)}")
            return {'response': '情感分析失败', 'tags': [], 'confidence': 0.0}

    def _process_with_default_agent(self, message: str) -> Dict[str, Any]:
        """默认智能体处理"""
        return {
            'response': '消息已接收并处理',
            'tags': ['已处理'],
            'confidence': 1.0
        }

    def _assign_tags_to_message(self, session_id: str, tags: list):
        """将识别的标签分配给消息记录"""
        try:
            # 示例：调用 POST /api/tags/assignments/assign/
            from apps.tags.models import Tag, TagAssignment
            from apps.history.models import ChatMessage
            from django.contrib.contenttypes.models import ContentType
            
            # 获取最新的聊天消息
            message = ChatMessage.objects.filter(session_id=session_id).last()
            if not message:
                return
            
            content_type = ContentType.objects.get_for_model(ChatMessage)
            
            for tag_name in tags:
                try:
                    tag = Tag.objects.filter(name=tag_name, is_active=True).first()
                    if tag:
                        TagAssignment.objects.get_or_create(
                            tag=tag,
                            content_type=content_type,
                            object_id=message.id,
                            defaults={
                                'assignment_type': 'agent',
                                'confidence': 0.8
                            }
                        )
                except Exception as e:
                    logger.error(f"分配标签失败 {tag_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"标签分配失败: {str(e)}")


class AgentConfigViewSet(viewsets.ModelViewSet):
    """智能体配置管理"""
    queryset = AgentConfig.objects.all()
    serializer_class = AgentConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    ordering = ['-created_at']


class AgentExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """智能体执行记录"""
    queryset = AgentExecution.objects.select_related('agent')
    serializer_class = AgentExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent', 'status']
    ordering = ['-started_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """执行统计"""
        agent_id = request.query_params.get('agent_id')
        queryset = self.get_queryset()
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        total = queryset.count()
        completed = queryset.filter(status='completed').count()
        failed = queryset.filter(status='failed').count()
        running = queryset.filter(status='running').count()
        
        return Response({
            'total_executions': total,
            'completed': completed,
            'failed': failed,
            'running': running,
            'success_rate': round((completed / total * 100) if total > 0 else 0, 2)
        })


class AgentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """智能体日志"""
    queryset = AgentLog.objects.select_related('agent')
    serializer_class = AgentLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent', 'level']
    ordering = ['-created_at'] 