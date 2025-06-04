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
import sys
import os
from typing import Dict, Any
from datetime import timedelta
from django.shortcuts import render
from django.core.cache import cache

from .models import Agent, AgentConfig, AgentExecution, AgentLog
from .serializers import AgentSerializer, AgentConfigSerializer, AgentExecutionSerializer, AgentLogSerializer
from .services import AgentManagerService

# Add the parent directory to Python path to import agents module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from agents import TagAgent, SentimentAgent

from apps.tags.models import TagRule

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
            agent.successful_executions += 1
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
                
                # 更新失败统计
                agent.total_executions += 1
                agent.failed_executions += 1
                agent.save()
            
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
            matched_rules = service.match_text(message)
            
            if matched_rules:
                # 取置信度最高的规则作为主要意图
                top_rule, confidence = matched_rules[0]
                return {
                    'intent': top_rule.name,
                    'confidence': confidence,
                    'rule_id': top_rule.id,
                    'matched_rules_count': len(matched_rules)
                }
            else:
                return {
                    'intent': 'unknown',
                    'confidence': 0.0,
                    'rule_id': None,
                    'matched_rules_count': 0
                }
                
        except Exception as e:
            logger.error(f"获取意图规则失败: {str(e)}")
            return {
                'intent': 'error',
                'confidence': 0.0,
                'error': str(e)
            }

    def _check_human_handoff(self, message: str) -> Dict[str, Any]:
        """调用关键词模块检查是否需要人工接入"""
        try:
            # 简化实现：检查特定关键词
            handoff_keywords = ['人工', '客服', '投诉', '退款', '问题']
            
            message_lower = message.lower()
            matched_keywords = [kw for kw in handoff_keywords if kw in message_lower]
            
            return {
                'required': len(matched_keywords) > 0,
                'matched_keywords': matched_keywords,
                'confidence': 0.8 if matched_keywords else 0.0
            }
            
        except Exception as e:
            logger.error(f"检查人工接入失败: {str(e)}")
            return {
                'required': False,
                'error': str(e)
            }

    def _process_with_tag_agent(self, message: str, intent_result: Dict) -> Dict[str, Any]:
        """使用标签智能体处理消息"""
        try:
            # 创建标签智能体实例
            tag_agent = TagAgent()
            
            # 处理消息
            result = tag_agent.process_message(message)
            
            return {
                'response': result.get('response', '我理解了您的需求'),
                'tags': result.get('tags', []),
                'confidence': result.get('confidence', 0.8),
                'agent_type': 'tag_agent'
            }
            
        except Exception as e:
            logger.error(f"标签智能体处理失败: {str(e)}")
            return {
                'response': '抱歉，处理您的消息时出现了问题',
                'tags': [],
                'confidence': 0.0,
                'error': str(e)
            }

    def _process_with_sentiment_agent(self, message: str) -> Dict[str, Any]:
        """使用情感分析智能体处理消息"""
        try:
            # 创建情感分析智能体实例
            sentiment_agent = SentimentAgent()
            
            # 分析情感
            result = sentiment_agent.analyze_sentiment(message)
            
            # 根据情感生成回复
            sentiment = result.get('sentiment', 'neutral')
            if sentiment == 'positive':
                response = '感谢您的积极反馈！'
            elif sentiment == 'negative':
                response = '我理解您的困扰，让我来帮助您解决问题。'
            else:
                response = '我明白了您的意思。'
            
            return {
                'response': response,
                'sentiment': sentiment,
                'confidence': result.get('confidence', 0.7),
                'agent_type': 'sentiment_agent'
            }
            
        except Exception as e:
            logger.error(f"情感分析智能体处理失败: {str(e)}")
            return {
                'response': '抱歉，处理您的消息时出现了问题',
                'sentiment': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }

    def _process_with_default_agent(self, message: str) -> Dict[str, Any]:
        """使用默认智能体处理消息"""
        return {
            'response': '您好，我已经收到您的消息，正在为您处理。',
            'confidence': 0.5,
            'agent_type': 'default'
        }

    def _assign_tags_to_message(self, session_id: str, tags: list):
        """为消息分配标签"""
        try:
            # 这里应该调用标签分配API
            # 示例：POST /api/tags/assignments/assign/
            
            # 简化实现：记录日志
            logger.info(f"为会话 {session_id} 分配标签: {tags}")
            
        except Exception as e:
            logger.error(f"分配标签失败: {str(e)}")


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