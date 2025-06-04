"""
智能客服聊天机器人服务层
处理消息、人工接入、数据分析等业务逻辑
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.cache import cache
from django.contrib.auth.models import User

from .models import ChatbotConfig, ChatSession, HumanHandoff, ChatStatistics, AgentPerformance
from apps.history.models import ChatMessage
from apps.keywords.models import KeywordMatch
from apps.agents_mgmt.models import Agent

logger = logging.getLogger('chatbot.services')


class MessageProcessorService:
    """消息处理服务"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5分钟缓存
    
    def process_message(self, session: ChatSession, message: str, message_type: str = 'user') -> Dict[str, Any]:
        """
        处理消息的核心方法
        """
        try:
            # 1. 创建消息记录
            chat_message = ChatMessage.objects.create(
                session=session,
                message_type=message_type,
                content=message,
                metadata={'processed_at': timezone.now().isoformat()}
            )
            
            # 2. 更新会话信息
            session.message_count += 1
            session.last_message_at = timezone.now()
            session.save()
            
            # 3. 如果是用户消息，需要生成机器人回复
            if message_type == 'user':
                bot_response = self._generate_bot_response(session, message)
                
                # 创建机器人回复消息
                if bot_response.get('content'):
                    bot_message = ChatMessage.objects.create(
                        session=session,
                        message_type='bot',
                        content=bot_response['content'],
                        metadata={
                            'confidence': bot_response.get('confidence', 1.0),
                            'agent_used': bot_response.get('agent_used'),
                            'processing_time': bot_response.get('processing_time', 0)
                        }
                    )
                    
                    session.message_count += 1
                    session.save()
                
                return {
                    'success': True,
                    'user_message_id': chat_message.id,
                    'bot_message_id': bot_message.id if bot_response.get('content') else None,
                    'bot_response': bot_response.get('content', ''),
                    'confidence': bot_response.get('confidence', 1.0),
                    'should_handoff': bot_response.get('should_handoff', False),
                    'handoff_reason': bot_response.get('handoff_reason')
                }
            
            return {
                'success': True,
                'message_id': chat_message.id,
                'message_type': message_type
            }
            
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_bot_response(self, session: ChatSession, message: str) -> Dict[str, Any]:
        """生成机器人回复"""
        try:
            config = session.config
            if not config:
                return {
                    'content': '系统配置错误，请联系管理员',
                    'confidence': 0.0,
                    'should_handoff': True,
                    'handoff_reason': 'config_error'
                }
            
            # 1. 检查是否需要人工接入
            handoff_check = self._check_handoff_needed(message, config)
            if handoff_check['needed']:
                return {
                    'content': '正在为您转接人工客服，请稍等...',
                    'confidence': 1.0,
                    'should_handoff': True,
                    'handoff_reason': handoff_check['reason']
                }
            
            # 2. 使用智能体生成回复
            if config.primary_agent:
                agent_response = self._call_agent(config.primary_agent, message, session)
                if agent_response['success']:
                    return agent_response
            
            # 3. 使用备用智能体
            if config.fallback_agent:
                agent_response = self._call_agent(config.fallback_agent, message, session)
                if agent_response['success']:
                    return agent_response
            
            # 4. 返回默认回复
            return {
                'content': config.default_response,
                'confidence': 0.1,
                'should_handoff': True,
                'handoff_reason': 'no_agent_available'
            }
            
        except Exception as e:
            logger.error(f"生成机器人回复失败: {str(e)}")
            return {
                'content': '抱歉，系统出现问题，正在为您转接人工客服',
                'confidence': 0.0,
                'should_handoff': True,
                'handoff_reason': 'system_error'
            }
    
    def _check_handoff_needed(self, message: str, config: ChatbotConfig) -> Dict[str, Any]:
        """检查是否需要人工接入"""
        if not config.auto_handoff_enabled:
            return {'needed': False}
        
        # 检查关键词匹配
        message_lower = message.lower()
        for keyword in config.handoff_keywords:
            if keyword.lower() in message_lower:
                return {
                    'needed': True,
                    'reason': 'keyword_match',
                    'matched_keyword': keyword
                }
        
        # 检查其他条件（可扩展）
        # 例如：消息长度、复杂度等
        
        return {'needed': False}
    
    def _call_agent(self, agent: Agent, message: str, session: ChatSession) -> Dict[str, Any]:
        """调用智能体处理消息"""
        try:
            start_time = timezone.now()
            
            # 这里应该调用实际的智能体API
            # 目前返回模拟响应
            response_content = f"智能体 {agent.name} 正在处理您的问题: {message}"
            confidence = 0.8
            
            processing_time = (timezone.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'content': response_content,
                'confidence': confidence,
                'agent_used': agent.name,
                'processing_time': processing_time,
                'should_handoff': confidence < 0.5
            }
            
        except Exception as e:
            logger.error(f"调用智能体失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class HumanHandoffService:
    """人工接入服务"""
    
    def create_handoff_request(self, session: ChatSession, reason: str, 
                             priority: str = 'normal', context: Dict = None) -> Dict[str, Any]:
        """创建人工接入请求"""
        try:
            # 检查是否已有待处理的接入请求
            existing = HumanHandoff.objects.filter(
                session=session,
                status__in=['pending', 'assigned', 'in_progress']
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'error': '该会话已有待处理的人工接入请求',
                    'existing_handoff_id': existing.id
                }
            
            # 创建人工接入记录
            handoff = HumanHandoff.objects.create(
                session=session,
                trigger_reason=reason,
                priority=priority,
                trigger_context=context or {},
                status='pending'
            )
            
            # 更新会话状态
            session.status = 'waiting_human'
            session.save()
            
            # 尝试自动分配客服
            assignment_result = self.auto_assign_agent(handoff)
            
            return {
                'success': True,
                'handoff_id': handoff.id,
                'status': handoff.status,
                'assignment_result': assignment_result
            }
            
        except Exception as e:
            logger.error(f"创建人工接入请求失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def auto_assign_agent(self, handoff: HumanHandoff) -> Dict[str, Any]:
        """自动分配客服"""
        try:
            # 查找可用的客服（这里简化处理）
            # 实际应该根据工作负载、技能匹配等因素分配
            available_agents = User.objects.filter(
                is_active=True,
                groups__name='customer_service'  # 假设有客服组
            )
            
            if not available_agents.exists():
                return {
                    'success': False,
                    'reason': 'no_available_agents'
                }
            
            # 简单的轮询分配
            agent = available_agents.first()
            
            handoff.assigned_agent = agent
            handoff.status = 'assigned'
            handoff.assigned_at = timezone.now()
            handoff.save()
            
            return {
                'success': True,
                'assigned_agent_id': agent.id,
                'assigned_agent_name': agent.username
            }
            
        except Exception as e:
            logger.error(f"自动分配客服失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取人工接入队列状态"""
        try:
            pending_count = HumanHandoff.objects.filter(status='pending').count()
            assigned_count = HumanHandoff.objects.filter(status='assigned').count()
            in_progress_count = HumanHandoff.objects.filter(status='in_progress').count()
            
            # 计算平均等待时间
            pending_handoffs = HumanHandoff.objects.filter(
                status='pending',
                created_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            avg_wait_time = 0
            if pending_handoffs.exists():
                total_wait_time = sum([
                    (timezone.now() - h.created_at).total_seconds() 
                    for h in pending_handoffs
                ])
                avg_wait_time = total_wait_time / pending_handoffs.count()
            
            return {
                'pending_count': pending_count,
                'assigned_count': assigned_count,
                'in_progress_count': in_progress_count,
                'total_queue': pending_count + assigned_count,
                'avg_wait_time_seconds': avg_wait_time
            }
            
        except Exception as e:
            logger.error(f"获取队列状态失败: {str(e)}")
            return {
                'error': str(e)
            }


class ChatAnalyticsService:
    """聊天数据分析服务"""
    
    def generate_daily_statistics(self, date: datetime.date, platform: str = None) -> Dict[str, Any]:
        """生成每日统计数据"""
        try:
            # 基础查询条件
            base_filter = {
                'created_at__date': date
            }
            if platform:
                base_filter['platform'] = platform
            
            # 会话统计
            sessions = ChatSession.objects.filter(**base_filter)
            total_sessions = sessions.count()
            active_sessions = sessions.filter(status='active').count()
            completed_sessions = sessions.filter(status='completed').count()
            
            # 消息统计
            messages = ChatMessage.objects.filter(
                session__in=sessions
            )
            total_messages = messages.count()
            bot_messages = messages.filter(message_type='bot').count()
            user_messages = messages.filter(message_type='user').count()
            human_messages = messages.filter(message_type='human').count()
            
            # 人工接入统计
            handoffs = HumanHandoff.objects.filter(
                created_at__date=date
            )
            if platform:
                handoffs = handoffs.filter(session__platform=platform)
            
            handoff_requests = handoffs.count()
            handoff_completed = handoffs.filter(status='completed').count()
            
            # 计算平均等待和处理时间
            completed_handoffs = handoffs.filter(
                status='completed',
                assigned_at__isnull=False,
                completed_at__isnull=False
            )
            
            avg_wait_time = 0
            avg_handle_time = 0
            if completed_handoffs.exists():
                wait_times = [h.waiting_time for h in completed_handoffs]
                handle_times = [h.handling_time for h in completed_handoffs]
                avg_wait_time = sum(wait_times) / len(wait_times)
                avg_handle_time = sum(handle_times) / len(handle_times)
            
            # 满意度统计
            satisfaction_ratings = handoffs.filter(
                customer_satisfaction__isnull=False
            )
            satisfaction_count = satisfaction_ratings.count()
            avg_satisfaction = 0
            if satisfaction_count > 0:
                avg_satisfaction = satisfaction_ratings.aggregate(
                    avg=Avg('customer_satisfaction')
                )['avg']
            
            # 机器人成功率（简化计算）
            bot_success_rate = 0.8  # 这里应该根据实际逻辑计算
            
            # 创建或更新统计记录
            stats, created = ChatStatistics.objects.get_or_create(
                date=date,
                platform=platform or '',
                defaults={
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'completed_sessions': completed_sessions,
                    'total_messages': total_messages,
                    'bot_messages': bot_messages,
                    'user_messages': user_messages,
                    'human_messages': human_messages,
                    'handoff_requests': handoff_requests,
                    'handoff_completed': handoff_completed,
                    'avg_handoff_wait_time': avg_wait_time,
                    'avg_handoff_handle_time': avg_handle_time,
                    'satisfaction_ratings': satisfaction_count,
                    'avg_satisfaction': avg_satisfaction or 0,
                    'bot_success_rate': bot_success_rate,
                    'avg_response_time': 1.5  # 模拟数据
                }
            )
            
            if not created:
                # 更新现有记录
                stats.total_sessions = total_sessions
                stats.active_sessions = active_sessions
                stats.completed_sessions = completed_sessions
                stats.total_messages = total_messages
                stats.bot_messages = bot_messages
                stats.user_messages = user_messages
                stats.human_messages = human_messages
                stats.handoff_requests = handoff_requests
                stats.handoff_completed = handoff_completed
                stats.avg_handoff_wait_time = avg_wait_time
                stats.avg_handoff_handle_time = avg_handle_time
                stats.satisfaction_ratings = satisfaction_count
                stats.avg_satisfaction = avg_satisfaction or 0
                stats.bot_success_rate = bot_success_rate
                stats.save()
            
            return {
                'success': True,
                'statistics_id': stats.id,
                'created': created
            }
            
        except Exception as e:
            logger.error(f"生成每日统计失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """获取仪表板数据"""
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # 获取统计数据
            stats = ChatStatistics.objects.filter(
                date__range=[start_date, end_date]
            ).order_by('date')
            
            # 汇总数据
            total_sessions = sum([s.total_sessions for s in stats])
            total_messages = sum([s.total_messages for s in stats])
            total_handoffs = sum([s.handoff_requests for s in stats])
            
            # 计算平均值
            avg_satisfaction = 0
            satisfaction_count = sum([s.satisfaction_ratings for s in stats])
            if satisfaction_count > 0:
                total_satisfaction = sum([
                    s.avg_satisfaction * s.satisfaction_ratings 
                    for s in stats if s.satisfaction_ratings > 0
                ])
                avg_satisfaction = total_satisfaction / satisfaction_count
            
            # 趋势数据
            daily_data = []
            for stat in stats:
                daily_data.append({
                    'date': stat.date.isoformat(),
                    'sessions': stat.total_sessions,
                    'messages': stat.total_messages,
                    'handoffs': stat.handoff_requests,
                    'satisfaction': stat.avg_satisfaction
                })
            
            return {
                'summary': {
                    'total_sessions': total_sessions,
                    'total_messages': total_messages,
                    'total_handoffs': total_handoffs,
                    'avg_satisfaction': round(avg_satisfaction, 2),
                    'handoff_rate': round((total_handoffs / total_sessions * 100) if total_sessions > 0 else 0, 2)
                },
                'daily_trends': daily_data,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                }
            }
            
        except Exception as e:
            logger.error(f"获取仪表板数据失败: {str(e)}")
            return {
                'error': str(e)
            }
    
    def generate_agent_performance(self, agent_id: str, date: datetime.date) -> Dict[str, Any]:
        """生成智能体性能数据"""
        try:
            from apps.agents_mgmt.models import AgentExecution
            
            # 获取智能体执行记录
            executions = AgentExecution.objects.filter(
                agent_id=agent_id,
                started_at__date=date
            )
            
            total_requests = executions.count()
            successful_requests = executions.filter(status='completed').count()
            failed_requests = executions.filter(status='failed').count()
            
            # 计算响应时间
            completed_executions = executions.filter(
                status='completed',
                completed_at__isnull=False
            )
            
            response_times = []
            for execution in completed_executions:
                if execution.started_at and execution.completed_at:
                    response_time = (execution.completed_at - execution.started_at).total_seconds() * 1000
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            
            # 创建或更新性能记录
            performance, created = AgentPerformance.objects.get_or_create(
                agent_id=agent_id,
                date=date,
                defaults={
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'avg_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'min_response_time': min_response_time,
                    'accuracy_score': 0.85,  # 模拟数据
                    'confidence_avg': 0.75,  # 模拟数据
                    'cpu_usage_avg': 45.0,   # 模拟数据
                    'memory_usage_avg': 512.0,  # 模拟数据
                    'timeout_count': 0,
                    'error_count': failed_requests
                }
            )
            
            return {
                'success': True,
                'performance_id': performance.id,
                'created': created
            }
            
        except Exception as e:
            logger.error(f"生成智能体性能数据失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 