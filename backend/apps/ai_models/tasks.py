"""
AI模型管理定时任务
定时更新性能统计、重置配额、健康检查等
"""

from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
import logging

from .models import ModelQuota, AIModel, ModelLoadBalancer, ModelWeight
from .services import PerformanceMonitorService

logger = logging.getLogger('ai_models.tasks')


@shared_task(bind=True)
def update_daily_model_performance(self, date_str=None):
    """
    定时任务：每天凌晨2点执行
    更新所有模型的每日性能统计
    """
    try:
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = (timezone.now() - timedelta(days=1)).date()
        
        logger.info(f"开始更新{date}的AI模型性能统计")
        
        monitor_service = PerformanceMonitorService()
        monitor_service.update_daily_performance(date)
        
        logger.info(f"AI模型性能统计更新完成 - 日期: {date}")
        
        return {
            'success': True,
            'date': date.isoformat(),
            'message': '性能统计更新完成'
        }
        
    except Exception as e:
        logger.error(f"更新AI模型性能统计失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def reset_model_quotas(self):
    """
    定时任务：重置模型配额
    每日、每周、每月根据配额类型自动重置
    """
    try:
        now = timezone.now()
        reset_count = 0
        
        # 获取需要重置的配额
        quotas_to_reset = ModelQuota.objects.filter(
            is_active=True,
            reset_at__lte=now
        )
        
        for quota in quotas_to_reset:
            # 重置使用量
            quota.used_calls = 0
            quota.used_tokens = 0
            quota.used_cost = 0
            quota.last_reset = now
            
            # 计算下次重置时间
            if quota.quota_type == 'daily':
                quota.reset_at = now + timedelta(days=1)
            elif quota.quota_type == 'weekly':
                quota.reset_at = now + timedelta(weeks=1)
            elif quota.quota_type == 'monthly':
                quota.reset_at = now + timedelta(days=30)
            
            quota.save()
            reset_count += 1
        
        logger.info(f"配额重置完成 - 重置数量: {reset_count}")
        
        return {
            'success': True,
            'reset_count': reset_count,
            'message': '配额重置完成'
        }
        
    except Exception as e:
        logger.error(f"重置模型配额失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def health_check_models(self):
    """
    定时任务：每5分钟执行
    检查所有模型的健康状态
    """
    try:
        monitor_service = PerformanceMonitorService()
        checked_models = 0
        unhealthy_models = []
        
        # 获取所有活跃的模型
        models = AIModel.objects.filter(is_active=True)
        
        for model in models:
            try:
                health_status = monitor_service.get_model_health_status(model)
                checked_models += 1
                
                # 如果模型不健康，更新负载均衡器中的状态
                if health_status['status'] == 'unhealthy':
                    unhealthy_models.append({
                        'model_id': model.id,
                        'model_name': model.name,
                        'status': health_status
                    })
                    
                    # 在所有负载均衡器中标记此模型为不健康
                    ModelWeight.objects.filter(
                        model=model
                    ).update(
                        is_healthy=False,
                        last_health_check=timezone.now()
                    )
                else:
                    # 标记为健康
                    ModelWeight.objects.filter(
                        model=model
                    ).update(
                        is_healthy=True,
                        last_health_check=timezone.now()
                    )
                    
            except Exception as e:
                logger.error(f"检查模型 {model.name} 健康状态失败: {str(e)}")
                unhealthy_models.append({
                    'model_id': model.id,
                    'model_name': model.name,
                    'error': str(e)
                })
        
        logger.info(f"模型健康检查完成 - 检查数量: {checked_models}, 不健康数量: {len(unhealthy_models)}")
        
        return {
            'success': True,
            'checked_models': checked_models,
            'unhealthy_models': unhealthy_models,
            'message': '健康检查完成'
        }
        
    except Exception as e:
        logger.error(f"模型健康检查失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_old_call_records(self, days_to_keep=30):
    """
    定时任务：清理旧的调用记录
    每天凌晨3点执行，清理30天前的记录
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # 删除旧的调用记录
        from .models import ModelCallRecord
        deleted_count, _ = ModelCallRecord.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"清理调用记录完成 - 删除数量: {deleted_count}")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'message': '调用记录清理完成'
        }
        
    except Exception as e:
        logger.error(f"清理调用记录失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def generate_cost_report(self, date_str=None):
    """
    定时任务：生成成本报告
    每周执行，生成模型使用成本统计
    """
    try:
        if date_str:
            end_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        start_date = end_date - timedelta(days=7)
        
        from .models import ModelCallRecord
        from django.db.models import Sum, Count, Avg
        
        # 按模型统计成本
        model_costs = ModelCallRecord.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='success'
        ).values(
            'model__name', 'model__provider__name'
        ).annotate(
            total_cost=Sum('cost'),
            total_calls=Count('id'),
            total_tokens=Sum('total_tokens'),
            avg_cost_per_call=Avg('cost')
        ).order_by('-total_cost')
        
        # 按用户统计成本
        user_costs = ModelCallRecord.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='success',
            user__isnull=False
        ).values(
            'user__username'
        ).annotate(
            total_cost=Sum('cost'),
            total_calls=Count('id'),
            total_tokens=Sum('total_tokens')
        ).order_by('-total_cost')[:10]
        
        # 总体统计
        total_stats = ModelCallRecord.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='success'
        ).aggregate(
            total_cost=Sum('cost'),
            total_calls=Count('id'),
            total_tokens=Sum('total_tokens'),
            avg_response_time=Avg('response_time')
        )
        
        report_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_stats': total_stats,
            'model_costs': list(model_costs),
            'user_costs': list(user_costs)
        }
        
        logger.info(f"成本报告生成完成 - 期间: {start_date} 到 {end_date}")
        
        return {
            'success': True,
            'report_data': report_data,
            'message': '成本报告生成完成'
        }
        
    except Exception as e:
        logger.error(f"生成成本报告失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        } 