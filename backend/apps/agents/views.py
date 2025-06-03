"""
智能体API视图
提供智能体功能的RESTful API接口
"""

import asyncio
import logging
from typing import Dict, Any
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
import json

from .services import (
    process_chat_message, analyze_user_tags, analyze_sentiment,
    query_knowledge, get_agent_status, activate_agent, deactivate_agent,
    update_agent_config, cleanup_agents, AgentManager
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request):
    """聊天API - 统一的对话接口"""
    try:
        data = request.data
        user_id = str(request.user.id)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        context = data.get('context', {})
        
        if not message:
            return Response({
                'success': False,
                'error': '消息内容不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步处理聊天消息
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                process_chat_message(user_id, message, session_id, context)
            )
        finally:
            loop.close()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': {
                    'response': result['data']['response'],
                    'conversation_state': result['data']['conversation_state'],
                    'next_actions': result['data']['next_actions'],
                    'timestamp': result['data']['timestamp']
                }
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', '处理失败'),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return Response({
            'success': False,
            'error': '服务器内部错误',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_tags_api(request):
    """用户标签分析API"""
    try:
        data = request.data
        user_id = str(request.user.id)
        message = data.get('message', '').strip()
        session_data = data.get('session_data', {})
        
        if not message:
            return Response({
                'success': False,
                'error': '消息内容不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步分析标签
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                analyze_user_tags(user_id, message, session_data)
            )
        finally:
            loop.close()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': {
                    'tags': result['data']['tags'],
                    'tag_scores': result['data']['tag_scores'],
                    'content_tags': result['data']['content_tags'],
                    'behavior_tags': result['data']['behavior_tags'],
                    'analysis_time': result['data']['analysis_time']
                }
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', '标签分析失败'),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Tag analysis API error: {e}")
        return Response({
            'success': False,
            'error': '服务器内部错误',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_sentiment_api(request):
    """情感分析API"""
    try:
        data = request.data
        user_id = str(request.user.id)
        message = data.get('message', '').strip()
        context = data.get('context', {})
        
        if not message:
            return Response({
                'success': False,
                'error': '消息内容不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步分析情感
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                analyze_sentiment(user_id, message, context)
            )
        finally:
            loop.close()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': {
                    'sentiment': result['data']['sentiment'],
                    'detailed_results': result['data']['detailed_results'],
                    'confidence': result['data']['confidence'],
                    'analysis_time': result['data']['analysis_time']
                }
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', '情感分析失败'),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Sentiment analysis API error: {e}")
        return Response({
            'success': False,
            'error': '服务器内部错误',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def knowledge_query_api(request):
    """知识库查询API"""
    try:
        data = request.data
        query = data.get('query', '').strip()
        user_id = str(request.user.id)
        knowledge_base = data.get('knowledge_base', 'general')
        context = data.get('context', {})
        
        if not query:
            return Response({
                'success': False,
                'error': '查询内容不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步查询知识库
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                query_knowledge(query, user_id, knowledge_base, context)
            )
        finally:
            loop.close()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': {
                    'query': result['data']['query'],
                    'answer': result['data']['answer'],
                    'knowledge_sources': result['data']['knowledge_sources'],
                    'confidence': result['data']['confidence'],
                    'search_stats': result['data']['search_stats']
                }
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', '知识库查询失败'),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Knowledge query API error: {e}")
        return Response({
            'success': False,
            'error': '服务器内部错误',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_status_api(request):
    """获取智能体状态API"""
    try:
        status_data = get_agent_status()
        metrics = AgentManager.get_agent_metrics()
        
        return Response({
            'success': True,
            'data': {
                'agent_status': status_data,
                'metrics': metrics,
                'available_agents': AgentManager.get_available_agents()
            }
        })
        
    except Exception as e:
        logger.error(f"Agent status API error: {e}")
        return Response({
            'success': False,
            'error': '获取智能体状态失败',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_control_api(request):
    """智能体控制API"""
    try:
        data = request.data
        agent_name = data.get('agent_name', '').strip()
        action = data.get('action', '').strip()
        config = data.get('config', {})
        
        if not agent_name:
            return Response({
                'success': False,
                'error': '智能体名称不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if action == 'activate':
            activate_agent(agent_name)
            message = f"智能体 {agent_name} 已激活"
        elif action == 'deactivate':
            deactivate_agent(agent_name)
            message = f"智能体 {agent_name} 已停用"
        elif action == 'update_config':
            if not config:
                return Response({
                    'success': False,
                    'error': '配置信息不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            update_agent_config(agent_name, config)
            message = f"智能体 {agent_name} 配置已更新"
        else:
            return Response({
                'success': False,
                'error': '不支持的操作类型',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': {
                'message': message,
                'agent_name': agent_name,
                'action': action
            }
        })
        
    except Exception as e:
        logger.error(f"Agent control API error: {e}")
        return Response({
            'success': False,
            'error': '智能体控制操作失败',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_pipeline_api(request):
    """智能体流水线API"""
    try:
        data = request.data
        agent_names = data.get('agent_names', [])
        input_data = data.get('input_data', {})
        
        if not agent_names:
            return Response({
                'success': False,
                'error': '智能体列表不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not input_data:
            return Response({
                'success': False,
                'error': '输入数据不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步运行流水线
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                AgentManager.run_agent_pipeline(agent_names, input_data)
            )
        finally:
            loop.close()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', '流水线执行失败'),
                'data': result.get('pipeline_results', [])
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Agent pipeline API error: {e}")
        return Response({
            'success': False,
            'error': '智能体流水线执行失败',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_agents_api(request):
    """清理智能体资源API"""
    try:
        cleanup_agents()
        
        return Response({
            'success': True,
            'data': {
                'message': '智能体资源清理完成'
            }
        })
        
    except Exception as e:
        logger.error(f"Agent cleanup API error: {e}")
        return Response({
            'success': False,
            'error': '智能体资源清理失败',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """Webhook接口 - 用于接收RAGFlow和Langflow的回调"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            webhook_type = data.get('type', '')
            
            if webhook_type == 'ragflow_update':
                # 处理RAGFlow知识库更新
                self._handle_ragflow_update(data)
            elif webhook_type == 'langflow_flow_complete':
                # 处理Langflow流程完成
                self._handle_langflow_complete(data)
            else:
                logger.warning(f"Unknown webhook type: {webhook_type}")
            
            return JsonResponse({
                'success': True,
                'message': 'Webhook processed successfully'
            })
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _handle_ragflow_update(self, data):
        """处理RAGFlow知识库更新"""
        try:
            # 这里可以实现知识库更新的逻辑
            # 例如：清理缓存、重新加载知识等
            logger.info(f"RAGFlow update received: {data}")
        except Exception as e:
            logger.error(f"Error handling RAGFlow update: {e}")
    
    def _handle_langflow_complete(self, data):
        """处理Langflow流程完成"""
        try:
            # 这里可以实现流程完成后的逻辑
            # 例如：记录日志、触发后续动作等
            logger.info(f"Langflow completion received: {data}")
        except Exception as e:
            logger.error(f"Error handling Langflow completion: {e}")


# 智能体能力展示API
@api_view(['GET'])
def agent_capabilities_api(request):
    """智能体能力展示API（公开接口）"""
    try:
        capabilities = {
            'tag_agent': {
                'name': '用户标签智能体',
                'description': '基于用户行为和对话内容自动识别用户特征和偏好',
                'capabilities': [
                    '购买意向分析',
                    '价格敏感度判断',
                    '产品偏好识别',
                    '沟通风格分析',
                    '决策模式预测'
                ],
                'example_tags': [
                    'high_intent', 'price_sensitive', 'electronics_lover',
                    'polite', 'decisive', 'frequent_buyer'
                ]
            },
            'sentiment_agent': {
                'name': '情感分析智能体',
                'description': '多维度分析用户情感状态，支持中英文情感识别',
                'capabilities': [
                    '实时情感识别',
                    '情感趋势分析',
                    '多语言情感支持',
                    '上下文情感调整',
                    '情感变化预警'
                ],
                'supported_emotions': [
                    'positive', 'negative', 'neutral',
                    'angry', 'happy', 'sad', 'surprised'
                ]
            },
            'memory_agent': {
                'name': '记忆管理智能体',
                'description': '管理对话历史和用户画像，提供上下文感知能力',
                'capabilities': [
                    '短期记忆管理',
                    '长期记忆存储',
                    '用户画像构建',
                    '对话状态跟踪',
                    '个性化上下文'
                ],
                'memory_types': [
                    'personal_info', 'preferences', 'purchase_intent',
                    'complaints', 'compliments', 'product_interests'
                ]
            },
            'knowledge_agent': {
                'name': '知识库智能体',
                'description': '基于RAGFlow的智能知识检索和问答系统',
                'capabilities': [
                    'RAGFlow知识检索',
                    '多源知识融合',
                    '智能答案生成',
                    '相关性排序',
                    '个性化推荐'
                ],
                'knowledge_types': [
                    'product', 'faq', 'policy', 'script'
                ]
            },
            'chat_agent': {
                'name': '聊天统合智能体',
                'description': '基于Langflow整合所有智能体，提供统一对话接口',
                'capabilities': [
                    'Langflow流程编排',
                    '智能体协调',
                    '对话状态管理',
                    '个性化回复',
                    '多轮对话支持'
                ],
                'conversation_states': [
                    'greeting', 'information_gathering', 'product_inquiry',
                    'product_recommendation', 'price_negotiation',
                    'order_processing', 'after_sales', 'closing'
                ]
            }
        }
        
        return Response({
            'success': True,
            'data': {
                'capabilities': capabilities,
                'architecture': {
                    'base_framework': 'Python + Django',
                    'rag_engine': 'RAGFlow',
                    'flow_engine': 'Langflow',
                    'nlp_libraries': ['jieba', 'snownlp', 'vaderSentiment'],
                    'supported_llms': ['OpenAI GPT', 'Anthropic Claude', '通义千问', '智谱清言']
                },
                'integration': {
                    'ragflow_features': [
                        '文档解析和向量化',
                        '语义检索',
                        '知识图谱构建',
                        '多模态支持'
                    ],
                    'langflow_features': [
                        '可视化流程编排',
                        '组件化开发',
                        '实时调试',
                        '模板复用'
                    ]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Agent capabilities API error: {e}")
        return Response({
            'success': False,
            'error': '获取智能体能力信息失败',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 