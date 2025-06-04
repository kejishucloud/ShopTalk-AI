"""
智能体管理服务模块
提供智能体的生命周期管理、监控和统计功能
"""

import os
import signal
import psutil
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from .models import Agent, AgentExecution, AgentLog, AgentMetrics

logger = logging.getLogger(__name__)


class AgentManagerService:
    """智能体管理服务"""
    
    def start_agent(self, agent: Agent) -> Dict[str, Any]:
        """启动智能体"""
        try:
            if agent.status == 'running':
                return {'success': False, 'error': '智能体已在运行中'}
            
            # 这里应该实际启动智能体进程
            # 示例：创建一个模拟的进程ID
            import random
            mock_pid = random.randint(10000, 99999)
            
            # 更新智能体状态
            agent.status = 'running'
            agent.pid = mock_pid
            agent.started_at = timezone.now()
            agent.save()
            
            # 记录日志
            AgentLog.objects.create(
                agent=agent,
                level='INFO',
                message=f'智能体 {agent.name} 启动成功，PID: {mock_pid}'
            )
            
            return {
                'success': True,
                'pid': mock_pid,
                'started_at': agent.started_at
            }
            
        except Exception as e:
            logger.error(f"启动智能体失败: {str(e)}")
            agent.status = 'error'
            agent.save()
            
            AgentLog.objects.create(
                agent=agent,
                level='ERROR',
                message=f'启动智能体失败: {str(e)}'
            )
            
            return {'success': False, 'error': str(e)}
    
    def stop_agent(self, agent: Agent) -> Dict[str, Any]:
        """停止智能体"""
        try:
            if agent.status != 'running':
                return {'success': False, 'error': '智能体未在运行'}
            
            # 实际场景中应该发送终止信号给进程
            if agent.pid:
                try:
                    # 这里只是模拟，实际应该使用进程管理
                    # os.kill(agent.pid, signal.SIGTERM)
                    pass
                except ProcessLookupError:
                    logger.warning(f"进程 {agent.pid} 不存在")
            
            # 更新智能体状态
            agent.status = 'stopped'
            agent.pid = None
            agent.save()
            
            # 记录日志
            AgentLog.objects.create(
                agent=agent,
                level='INFO',
                message=f'智能体 {agent.name} 已停止'
            )
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"停止智能体失败: {str(e)}")
            
            AgentLog.objects.create(
                agent=agent,
                level='ERROR',
                message=f'停止智能体失败: {str(e)}'
            )
            
            return {'success': False, 'error': str(e)}
    
    def get_uptime(self, agent: Agent) -> Optional[str]:
        """获取智能体运行时间"""
        if agent.status == 'running' and agent.started_at:
            uptime = timezone.now() - agent.started_at
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        return None
    
    def get_memory_usage(self, agent: Agent) -> Optional[float]:
        """获取智能体内存使用情况"""
        if agent.pid and agent.status == 'running':
            try:
                # 在实际场景中使用 psutil 获取真实的内存使用
                import random
                return round(random.uniform(50, 500), 2)  # MB
            except Exception:
                return None
        return None
    
    def get_cpu_usage(self, agent: Agent) -> Optional[float]:
        """获取智能体CPU使用情况"""
        if agent.pid and agent.status == 'running':
            try:
                # 在实际场景中使用 psutil 获取真实的CPU使用率
                import random
                return round(random.uniform(1, 20), 2)  # %
            except Exception:
                return None
        return None
    
    def calculate_success_rate(self, agent: Agent) -> float:
        """计算智能体成功率"""
        if agent.total_executions > 0:
            return round(agent.successful_executions / agent.total_executions * 100, 2)
        return 0.0
    
    def restart_agent(self, agent: Agent) -> Dict[str, Any]:
        """重启智能体"""
        try:
            # 先停止
            stop_result = self.stop_agent(agent)
            if not stop_result['success']:
                return stop_result
            
            # 等待一秒
            import time
            time.sleep(1)
            
            # 再启动
            start_result = self.start_agent(agent)
            
            if start_result['success']:
                AgentLog.objects.create(
                    agent=agent,
                    level='INFO',
                    message=f'智能体 {agent.name} 重启成功'
                )
            
            return start_result
            
        except Exception as e:
            logger.error(f"重启智能体失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_metrics(self, agent: Agent) -> Dict[str, Any]:
        """收集智能体指标"""
        try:
            cpu_usage = self.get_cpu_usage(agent) or 0.0
            memory_usage = self.get_memory_usage(agent) or 0.0
            
            # 计算最近一分钟的请求数
            one_minute_ago = timezone.now() - timedelta(minutes=1)
            recent_executions = AgentExecution.objects.filter(
                agent=agent,
                started_at__gte=one_minute_ago
            ).count()
            
            # 计算平均响应时间
            avg_duration = AgentExecution.objects.filter(
                agent=agent,
                status='completed',
                duration__isnull=False
            ).aggregate(avg_duration=Avg('duration'))['avg_duration'] or 0.0
            
            # 计算错误率
            total_recent = AgentExecution.objects.filter(
                agent=agent,
                started_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            failed_recent = AgentExecution.objects.filter(
                agent=agent,
                started_at__gte=timezone.now() - timedelta(hours=1),
                status='failed'
            ).count()
            
            error_rate = (failed_recent / total_recent * 100) if total_recent > 0 else 0.0
            
            # 保存指标
            metrics = AgentMetrics.objects.create(
                agent=agent,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                requests_per_minute=recent_executions,
                average_response_time=avg_duration,
                error_rate=error_rate,
                metrics_data={
                    'uptime': self.get_uptime(agent),
                    'success_rate': self.calculate_success_rate(agent)
                }
            )
            
            return {
                'success': True,
                'metrics': {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'requests_per_minute': recent_executions,
                    'average_response_time': avg_duration,
                    'error_rate': error_rate
                }
            }
            
        except Exception as e:
            logger.error(f"收集指标失败: {str(e)}")
            return {'success': False, 'error': str(e)}


class AgentStatisticsService:
    """智能体统计服务"""
    
    def get_overview_statistics(self) -> Dict[str, Any]:
        """获取总览统计信息"""
        try:
            total_agents = Agent.objects.count()
            running_agents = Agent.objects.filter(status='running').count()
            idle_agents = Agent.objects.filter(status='idle').count()
            error_agents = Agent.objects.filter(status='error').count()
            
            # 今日执行统计
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_executions = AgentExecution.objects.filter(
                started_at__gte=today_start
            )
            
            total_executions_today = today_executions.count()
            successful_executions_today = today_executions.filter(status='completed').count()
            failed_executions_today = today_executions.filter(status='failed').count()
            
            # 平均响应时间
            avg_response_time = today_executions.filter(
                status='completed',
                duration__isnull=False
            ).aggregate(avg_duration=Avg('duration'))['avg_duration'] or 0.0
            
            # 成功率
            success_rate = (successful_executions_today / total_executions_today * 100) if total_executions_today > 0 else 0.0
            
            return {
                'total_agents': total_agents,
                'running_agents': running_agents,
                'idle_agents': idle_agents,
                'error_agents': error_agents,
                'total_executions_today': total_executions_today,
                'successful_executions_today': successful_executions_today,
                'failed_executions_today': failed_executions_today,
                'average_response_time': round(avg_response_time, 3),
                'success_rate': round(success_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
    
    def get_agent_performance_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取智能体性能排行"""
        try:
            agents = Agent.objects.filter(
                is_active=True,
                total_executions__gt=0
            ).order_by('-successful_executions')[:limit]
            
            performance_data = []
            for agent in agents:
                executions = AgentExecution.objects.filter(agent=agent)
                success_count = executions.filter(status='completed').count()
                failure_count = executions.filter(status='failed').count()
                
                avg_duration = executions.filter(
                    status='completed',
                    duration__isnull=False
                ).aggregate(avg_duration=Avg('duration'))['avg_duration'] or 0.0
                
                performance_data.append({
                    'agent_id': agent.id,
                    'agent_name': agent.name,
                    'executions_count': agent.total_executions,
                    'success_count': success_count,
                    'failure_count': failure_count,
                    'success_rate': agent.success_rate,
                    'average_duration': round(avg_duration, 3),
                    'last_execution': agent.last_execution_at
                })
            
            return performance_data
            
        except Exception as e:
            logger.error(f"获取性能排行失败: {str(e)}")
            return []
    
    def get_execution_trends(self, days: int = 7) -> Dict[str, Any]:
        """获取执行趋势数据"""
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            trends = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = timezone.datetime.combine(current_date, timezone.datetime.min.time())
                day_end = day_start + timedelta(days=1)
                
                day_executions = AgentExecution.objects.filter(
                    started_at__gte=day_start,
                    started_at__lt=day_end
                )
                
                total = day_executions.count()
                success = day_executions.filter(status='completed').count()
                failed = day_executions.filter(status='failed').count()
                
                trends.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'total_executions': total,
                    'successful_executions': success,
                    'failed_executions': failed,
                    'success_rate': (success / total * 100) if total > 0 else 0
                })
                
                current_date += timedelta(days=1)
            
            return {
                'period': f"{start_date} to {end_date}",
                'trends': trends
            }
            
        except Exception as e:
            logger.error(f"获取执行趋势失败: {str(e)}")
            return {}


class AgentHealthCheckService:
    """智能体健康检查服务"""
    
    def check_agent_health(self, agent: Agent) -> Dict[str, Any]:
        """检查单个智能体健康状态"""
        try:
            health_data = {
                'agent_id': agent.id,
                'agent_name': agent.name,
                'status': agent.status,
                'is_healthy': True,
                'issues': []
            }
            
            # 检查是否长时间未执行
            if agent.last_execution_at:
                time_since_last = timezone.now() - agent.last_execution_at
                if time_since_last > timedelta(hours=1) and agent.status == 'running':
                    health_data['is_healthy'] = False
                    health_data['issues'].append('长时间未执行任务')
            
            # 检查错误率
            if agent.total_executions > 10:
                error_rate = agent.failed_executions / agent.total_executions
                if error_rate > 0.1:  # 错误率超过10%
                    health_data['is_healthy'] = False
                    health_data['issues'].append(f'错误率过高: {error_rate*100:.1f}%')
            
            # 检查内存使用
            memory_usage = self._get_memory_usage(agent)
            if memory_usage and memory_usage > 1000:  # 超过1GB
                health_data['is_healthy'] = False
                health_data['issues'].append(f'内存使用过高: {memory_usage}MB')
            
            return health_data
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                'agent_id': agent.id,
                'agent_name': agent.name,
                'is_healthy': False,
                'issues': [f'健康检查失败: {str(e)}']
            }
    
    def check_all_agents_health(self) -> List[Dict[str, Any]]:
        """检查所有智能体健康状态"""
        agents = Agent.objects.filter(is_active=True)
        return [self.check_agent_health(agent) for agent in agents]
    
    def _get_memory_usage(self, agent: Agent) -> Optional[float]:
        """获取内存使用情况（私有方法）"""
        # 这里应该实际获取内存使用情况
        # 为了演示，返回随机值
        if agent.status == 'running':
            import random
            return round(random.uniform(100, 800), 2)
        return None 