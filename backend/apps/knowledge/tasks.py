"""
知识库管理定时任务
提供自动化的数据处理、统计分析、清理等功能
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Avg, Sum, F
from django.conf import settings

from .models import (
    KnowledgeBase, Document, FAQ, Product, Script, KnowledgeVector,
    KnowledgeAccessRecord, KnowledgeRecommendation, DocumentTag
)
from .services import (
    DocumentProcessorService, VectorizeService, KnowledgeSearchService,
    RecommendationService, KnowledgeAnalyticsService
)

logger = logging.getLogger('knowledge')


@shared_task(bind=True)
def update_knowledge_base_statistics(self, knowledge_base_id: int = None):
    """
    更新知识库统计数据
    """
    try:
        knowledge_bases = KnowledgeBase.objects.filter(is_active=True)
        if knowledge_base_id:
            knowledge_bases = knowledge_bases.filter(id=knowledge_base_id)
        
        updated_count = 0
        
        for kb in knowledge_bases:
            # 更新文档总数
            document_count = kb.documents.filter(is_active=True).count()
            
            # 更新FAQ总数
            faq_count = kb.faqs.filter(is_active=True, status='published').count()
            
            # 更新总访问次数
            total_views = KnowledgeAccessRecord.objects.filter(
                knowledge_base=kb,
                access_type='view'
            ).count()
            
            # 批量更新
            KnowledgeBase.objects.filter(id=kb.id).update(
                total_documents=document_count,
                total_qa_pairs=faq_count,
                total_views=total_views
            )
            
            updated_count += 1
            
        logger.info(f"知识库统计更新完成，更新了 {updated_count} 个知识库")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'message': '知识库统计更新成功'
        }
        
    except Exception as e:
        logger.error(f"更新知识库统计失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def update_tag_usage_count(self):
    """
    更新标签使用次数
    """
    try:
        updated_count = 0
        
        for tag in DocumentTag.objects.all():
            # 计算标签使用次数
            document_count = tag.document_set.filter(is_active=True).count()
            faq_count = tag.faq_set.filter(is_active=True).count()
            product_count = tag.product_set.count()
            script_count = tag.script_set.filter(is_active=True).count()
            
            total_usage = document_count + faq_count + product_count + script_count
            
            if tag.usage_count != total_usage:
                tag.usage_count = total_usage
                tag.save(update_fields=['usage_count'])
                updated_count += 1
        
        logger.info(f"标签使用次数更新完成，更新了 {updated_count} 个标签")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'message': '标签使用次数更新成功'
        }
        
    except Exception as e:
        logger.error(f"更新标签使用次数失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def process_pending_documents(self):
    """
    处理待处理的文档
    """
    try:
        pending_documents = Document.objects.filter(
            process_status='pending',
            is_active=True
        )[:10]  # 每次处理10个文档
        
        processed_count = 0
        failed_count = 0
        
        processor_service = DocumentProcessorService()
        
        for document in pending_documents:
            try:
                result = processor_service.process_document(document)
                if result['success']:
                    processed_count += 1
                    logger.info(f"文档处理成功: {document.title}")
                else:
                    failed_count += 1
                    logger.warning(f"文档处理失败: {document.title} - {result.get('error')}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"文档处理异常: {document.title} - {str(e)}")
        
        return {
            'success': True,
            'processed_count': processed_count,
            'failed_count': failed_count,
            'message': f'文档处理完成，成功 {processed_count} 个，失败 {failed_count} 个'
        }
        
    except Exception as e:
        logger.error(f"批量处理文档失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def auto_vectorize_content(self):
    """
    自动向量化内容
    """
    try:
        vectorize_service = VectorizeService()
        
        # 处理新增的文档
        new_documents = Document.objects.filter(
            process_status='completed',
            is_active=True,
            knowledge_base__enable_ai_enhancement=True
        ).exclude(
            id__in=KnowledgeVector.objects.filter(content_type='document').values_list('content_id', flat=True)
        )[:5]  # 每次处理5个文档
        
        vectorized_count = 0
        failed_count = 0
        
        for document in new_documents:
            try:
                result = vectorize_service.vectorize_document(document)
                if result['success']:
                    vectorized_count += 1
                    logger.info(f"文档向量化成功: {document.title}")
                else:
                    failed_count += 1
                    logger.warning(f"文档向量化失败: {document.title}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"文档向量化异常: {document.title} - {str(e)}")
        
        # 处理新增的FAQ
        new_faqs = FAQ.objects.filter(
            status='published',
            is_active=True,
            knowledge_base__enable_ai_enhancement=True
        ).exclude(
            id__in=KnowledgeVector.objects.filter(content_type='faq').values_list('content_id', flat=True)
        )[:5]  # 每次处理5个FAQ
        
        for faq in new_faqs:
            try:
                result = vectorize_service.vectorize_faq(faq)
                if result['success']:
                    vectorized_count += 1
                    logger.info(f"FAQ向量化成功: {faq.question[:50]}")
                else:
                    failed_count += 1
                    logger.warning(f"FAQ向量化失败: {faq.question[:50]}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"FAQ向量化异常: {faq.question[:50]} - {str(e)}")
        
        return {
            'success': True,
            'vectorized_count': vectorized_count,
            'failed_count': failed_count,
            'message': f'内容向量化完成，成功 {vectorized_count} 个，失败 {failed_count} 个'
        }
        
    except Exception as e:
        logger.error(f"自动向量化失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def generate_knowledge_recommendations(self):
    """
    生成知识推荐
    """
    try:
        recommendation_service = RecommendationService()
        
        # 为热门文档生成推荐
        popular_documents = Document.objects.filter(
            is_active=True,
            view_count__gte=10
        ).order_by('-view_count')[:20]
        
        generated_count = 0
        
        for document in popular_documents:
            try:
                recommendations = recommendation_service.generate_recommendations(
                    'document', document.id, document.knowledge_base_id, 5
                )
                
                # 保存推荐记录
                for rec in recommendations:
                    KnowledgeRecommendation.objects.update_or_create(
                        knowledge_base_id=document.knowledge_base_id,
                        source_content_type='document',
                        source_content_id=document.id,
                        target_content_type=rec['content_type'],
                        target_content_id=rec['content_id'],
                        recommendation_type='similar',
                        defaults={
                            'similarity_score': rec['score'],
                            'confidence_score': rec['score'],
                            'algorithm': 'auto_generation',
                            'is_active': True
                        }
                    )
                
                generated_count += len(recommendations)
                
            except Exception as e:
                logger.warning(f"为文档 {document.title} 生成推荐失败: {str(e)}")
        
        logger.info(f"知识推荐生成完成，生成了 {generated_count} 个推荐")
        
        return {
            'success': True,
            'generated_count': generated_count,
            'message': '知识推荐生成成功'
        }
        
    except Exception as e:
        logger.error(f"生成知识推荐失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_old_access_records(self, days_to_keep: int = 90):
    """
    清理旧的访问记录
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        deleted_count, _ = KnowledgeAccessRecord.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"清理旧访问记录完成，删除了 {deleted_count} 条记录")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'清理了 {deleted_count} 条旧访问记录'
        }
        
    except Exception as e:
        logger.error(f"清理旧访问记录失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_orphaned_vectors(self):
    """
    清理孤立的向量数据
    """
    try:
        deleted_count = 0
        
        # 清理文档向量
        document_vectors = KnowledgeVector.objects.filter(content_type='document')
        for vector in document_vectors:
            if not Document.objects.filter(id=vector.content_id, is_active=True).exists():
                vector.delete()
                deleted_count += 1
        
        # 清理FAQ向量
        faq_vectors = KnowledgeVector.objects.filter(content_type='faq')
        for vector in faq_vectors:
            if not FAQ.objects.filter(id=vector.content_id, is_active=True).exists():
                vector.delete()
                deleted_count += 1
        
        logger.info(f"清理孤立向量完成，删除了 {deleted_count} 个向量")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'清理了 {deleted_count} 个孤立向量'
        }
        
    except Exception as e:
        logger.error(f"清理孤立向量失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def generate_knowledge_analytics_report(self, knowledge_base_id: int = None):
    """
    生成知识库分析报告
    """
    try:
        analytics_service = KnowledgeAnalyticsService()
        
        knowledge_bases = KnowledgeBase.objects.filter(is_active=True)
        if knowledge_base_id:
            knowledge_bases = knowledge_bases.filter(id=knowledge_base_id)
        
        reports = []
        
        for kb in knowledge_bases:
            try:
                # 生成最近30天的分析报告
                date_from = timezone.now() - timedelta(days=30)
                date_to = timezone.now()
                
                analytics_data = analytics_service.get_knowledge_base_analytics(
                    kb.id, date_from, date_to
                )
                
                if 'error' not in analytics_data:
                    reports.append({
                        'knowledge_base_id': kb.id,
                        'knowledge_base_name': kb.name,
                        'analytics': analytics_data
                    })
                    
            except Exception as e:
                logger.warning(f"为知识库 {kb.name} 生成分析报告失败: {str(e)}")
        
        logger.info(f"知识库分析报告生成完成，生成了 {len(reports)} 个报告")
        
        return {
            'success': True,
            'report_count': len(reports),
            'reports': reports,
            'message': '知识库分析报告生成成功'
        }
        
    except Exception as e:
        logger.error(f"生成知识库分析报告失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def optimize_knowledge_vectors(self):
    """
    优化知识向量质量
    """
    try:
        # 找出质量评分较低的向量
        low_quality_vectors = KnowledgeVector.objects.filter(
            quality_score__lt=0.5
        )[:100]  # 每次处理100个
        
        optimized_count = 0
        
        for vector in low_quality_vectors:
            try:
                # 重新计算质量评分
                text_length = len(vector.text_chunk)
                keyword_count = len(vector.keywords)
                
                # 简单的质量评分算法
                quality_score = min(1.0, (text_length / 500) * 0.6 + (keyword_count / 10) * 0.4)
                
                if quality_score != vector.quality_score:
                    vector.quality_score = quality_score
                    vector.save(update_fields=['quality_score'])
                    optimized_count += 1
                    
            except Exception as e:
                logger.warning(f"优化向量 {vector.id} 失败: {str(e)}")
        
        logger.info(f"向量质量优化完成，优化了 {optimized_count} 个向量")
        
        return {
            'success': True,
            'optimized_count': optimized_count,
            'message': f'优化了 {optimized_count} 个向量的质量评分'
        }
        
    except Exception as e:
        logger.error(f"优化知识向量失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def health_check_knowledge_system(self):
    """
    知识系统健康检查
    """
    try:
        health_status = {}
        
        # 检查知识库状态
        total_kb = KnowledgeBase.objects.count()
        active_kb = KnowledgeBase.objects.filter(is_active=True).count()
        health_status['knowledge_bases'] = {
            'total': total_kb,
            'active': active_kb,
            'status': 'healthy' if active_kb > 0 else 'warning'
        }
        
        # 检查文档处理状态
        pending_docs = Document.objects.filter(process_status='pending').count()
        failed_docs = Document.objects.filter(process_status='failed').count()
        health_status['document_processing'] = {
            'pending': pending_docs,
            'failed': failed_docs,
            'status': 'healthy' if failed_docs < pending_docs * 0.1 else 'warning'
        }
        
        # 检查向量数据
        total_vectors = KnowledgeVector.objects.count()
        low_quality_vectors = KnowledgeVector.objects.filter(quality_score__lt=0.3).count()
        health_status['vectors'] = {
            'total': total_vectors,
            'low_quality': low_quality_vectors,
            'status': 'healthy' if low_quality_vectors < total_vectors * 0.2 else 'warning'
        }
        
        # 检查搜索性能
        recent_searches = KnowledgeAccessRecord.objects.filter(
            access_type='search',
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        avg_response_time = recent_searches.aggregate(
            avg_time=Avg('response_time')
        )['avg_time'] or 0
        
        health_status['search_performance'] = {
            'avg_response_time': avg_response_time,
            'search_count_24h': recent_searches.count(),
            'status': 'healthy' if avg_response_time < 2.0 else 'warning'
        }
        
        # 总体健康状态
        warning_count = sum(1 for status in health_status.values() if status.get('status') == 'warning')
        overall_status = 'healthy' if warning_count == 0 else 'warning' if warning_count <= 2 else 'critical'
        
        health_status['overall'] = {
            'status': overall_status,
            'warning_count': warning_count,
            'check_time': timezone.now().isoformat()
        }
        
        logger.info(f"知识系统健康检查完成，状态: {overall_status}")
        
        return {
            'success': True,
            'health_status': health_status,
            'message': '健康检查完成'
        }
        
    except Exception as e:
        logger.error(f"知识系统健康检查失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        } 