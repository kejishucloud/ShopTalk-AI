"""
智能体异步任务模块
使用Celery实现定时任务和批量处理任务
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .services import ChatIngestor, ContextManager, TagManager
from .controllers import ChatIngestionController

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def daily_conversation_ingestion(self):
    """每日对话数据入库任务
    
    每天凌晨1点执行，将昨天新增的对话数据批量写入知识库
    """
    try:
        logger.info("开始执行每日对话数据入库任务")
        
        # 计算昨天的时间范围
        yesterday = timezone.now().date() - timedelta(days=1)
        start_time = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
        end_time = timezone.make_aware(datetime.combine(yesterday, datetime.max.time()))
        
        # TODO: 从数据库获取昨天的对话数据
        # 这里需要根据实际的对话模型来实现
        conversations = _get_conversations_by_date_range(start_time, end_time)
        
        if not conversations:
            logger.info("昨天没有新的对话数据")
            return {
                'success': True,
                'message': '昨天没有新的对话数据',
                'processed': 0
            }
        
        # 使用控制器处理对话数据
        controller = ChatIngestionController()
        result = controller.batch_ingest_conversations(conversations)
        
        if result['success']:
            logger.info(f"每日对话数据入库完成: {result['data']}")
            return {
                'success': True,
                'message': '每日对话数据入库完成',
                'result': result['data']
            }
        else:
            logger.error(f"每日对话数据入库失败: {result['error']}")
            raise Exception(result['error'])
            
    except Exception as e:
        logger.error(f"每日对话数据入库任务失败: {str(e)}")
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"任务重试 {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        else:
            return {
                'success': False,
                'error': str(e),
                'retries_exhausted': True
            }


@shared_task(bind=True, max_retries=2)
def cleanup_expired_data(self):
    """清理过期数据任务
    
    定时清理过期的上下文、低权重标签、重复知识等
    """
    try:
        logger.info("开始执行数据清理任务")
        
        cleanup_results = {
            'contexts_cleaned': 0,
            'tags_cleaned': 0,
            'knowledge_cleaned': 0,
            'errors': []
        }
        
        # 1. 清理过期上下文
        try:
            context_manager = ContextManager()
            contexts_cleaned = context_manager.cleanup_expired_contexts()
            cleanup_results['contexts_cleaned'] = contexts_cleaned
            logger.info(f"清理了 {contexts_cleaned} 个过期上下文")
        except Exception as e:
            error_msg = f"清理过期上下文失败: {str(e)}"
            logger.error(error_msg)
            cleanup_results['errors'].append(error_msg)
        
        # 2. 清理低权重标签
        try:
            tag_manager = TagManager()
            tags_cleaned = _cleanup_low_weight_tags(tag_manager)
            cleanup_results['tags_cleaned'] = tags_cleaned
            logger.info(f"清理了 {tags_cleaned} 个低权重标签")
        except Exception as e:
            error_msg = f"清理低权重标签失败: {str(e)}"
            logger.error(error_msg)
            cleanup_results['errors'].append(error_msg)
        
        # 3. 清理重复知识
        try:
            chat_ingestor = ChatIngestor()
            knowledge_cleaned = chat_ingestor.cleanup_duplicate_knowledge()
            cleanup_results['knowledge_cleaned'] = knowledge_cleaned
            logger.info(f"清理了 {knowledge_cleaned} 个重复知识项")
        except Exception as e:
            error_msg = f"清理重复知识失败: {str(e)}"
            logger.error(error_msg)
            cleanup_results['errors'].append(error_msg)
        
        logger.info(f"数据清理任务完成: {cleanup_results}")
        
        return {
            'success': True,
            'message': '数据清理任务完成',
            'results': cleanup_results
        }
        
    except Exception as e:
        logger.error(f"数据清理任务失败: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"任务重试 {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=300)  # 5分钟后重试
        else:
            return {
                'success': False,
                'error': str(e),
                'retries_exhausted': True
            }


@shared_task
def process_conversation_batch(conversation_ids: List[str]):
    """批量处理对话数据
    
    Args:
        conversation_ids: 对话ID列表
        
    Returns:
        Dict: 处理结果
    """
    try:
        logger.info(f"开始批量处理 {len(conversation_ids)} 个对话")
        
        # 获取对话数据
        conversations = _get_conversations_by_ids(conversation_ids)
        
        if not conversations:
            return {
                'success': False,
                'error': '未找到指定的对话数据'
            }
        
        # 批量处理
        controller = ChatIngestionController()
        result = controller.batch_ingest_conversations(conversations)
        
        logger.info(f"批量处理完成: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"批量处理对话失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def analyze_user_sentiment_batch(user_messages: List[Dict]):
    """批量分析用户情感
    
    Args:
        user_messages: 用户消息列表
        [{'user_id': str, 'message': str, 'timestamp': datetime}, ...]
        
    Returns:
        Dict: 分析结果
    """
    try:
        logger.info(f"开始批量分析 {len(user_messages)} 条消息的情感")
        
        from .controllers import SentimentController
        
        controller = SentimentController()
        results = []
        
        for msg_data in user_messages:
            try:
                result = controller.analyze_text_sentiment(
                    text=msg_data['message'],
                    user_id=msg_data.get('user_id')
                )
                
                results.append({
                    'user_id': msg_data.get('user_id'),
                    'message': msg_data['message'],
                    'sentiment_result': result,
                    'timestamp': msg_data.get('timestamp')
                })
                
            except Exception as e:
                logger.error(f"分析消息情感失败: {str(e)}")
                results.append({
                    'user_id': msg_data.get('user_id'),
                    'message': msg_data['message'],
                    'error': str(e),
                    'timestamp': msg_data.get('timestamp')
                })
        
        logger.info(f"批量情感分析完成，成功 {len([r for r in results if 'error' not in r])} 条")
        
        return {
            'success': True,
            'total': len(user_messages),
            'results': results,
            'processed_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量情感分析失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def update_user_tags_batch(user_tag_updates: List[Dict]):
    """批量更新用户标签
    
    Args:
        user_tag_updates: 用户标签更新列表
        [{'user_id': str, 'message': str}, ...]
        
    Returns:
        Dict: 更新结果
    """
    try:
        logger.info(f"开始批量更新 {len(user_tag_updates)} 个用户的标签")
        
        from .controllers import UserTagController
        
        controller = UserTagController()
        results = []
        
        for update_data in user_tag_updates:
            try:
                result = controller.analyze_and_update_tags(
                    user_id=update_data['user_id'],
                    message=update_data['message']
                )
                
                results.append({
                    'user_id': update_data['user_id'],
                    'update_result': result
                })
                
            except Exception as e:
                logger.error(f"更新用户标签失败: {str(e)}")
                results.append({
                    'user_id': update_data['user_id'],
                    'error': str(e)
                })
        
        successful_updates = len([r for r in results if 'error' not in r])
        logger.info(f"批量标签更新完成，成功 {successful_updates} 个用户")
        
        return {
            'success': True,
            'total': len(user_tag_updates),
            'successful': successful_updates,
            'results': results,
            'processed_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量标签更新失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def knowledge_base_sync(knowledge_items: List[Dict]):
    """知识库同步任务
    
    将处理好的知识项同步到向量数据库
    
    Args:
        knowledge_items: 知识项列表
        
    Returns:
        Dict: 同步结果
    """
    try:
        logger.info(f"开始同步 {len(knowledge_items)} 个知识项到向量数据库")
        
        # TODO: 实现向量数据库同步逻辑
        # 这里可以集成Milvus、Pinecone等向量数据库
        
        sync_results = {
            'total': len(knowledge_items),
            'synced': 0,
            'failed': 0,
            'errors': []
        }
        
        for item in knowledge_items:
            try:
                # 模拟向量化和存储过程
                vector = _vectorize_knowledge_item(item)
                success = _store_to_vector_db(item, vector)
                
                if success:
                    sync_results['synced'] += 1
                else:
                    sync_results['failed'] += 1
                    sync_results['errors'].append(f"存储失败: {item.get('question', 'Unknown')}")
                    
            except Exception as e:
                sync_results['failed'] += 1
                sync_results['errors'].append(f"处理失败: {str(e)}")
        
        logger.info(f"知识库同步完成: {sync_results}")
        
        return {
            'success': True,
            'message': '知识库同步完成',
            'results': sync_results
        }
        
    except Exception as e:
        logger.error(f"知识库同步失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# 辅助函数

def _get_conversations_by_date_range(start_time: datetime, end_time: datetime) -> List[Dict]:
    """根据时间范围获取对话数据
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        List[Dict]: 对话数据列表
    """
    # TODO: 实现实际的数据库查询逻辑
    # 这里需要根据实际的对话模型来实现
    
    # 示例数据结构
    return [
        {
            'conversation_id': 'conv_001',
            'user_id': 'user_001',
            'messages': [
                {'role': 'user', 'content': '你好', 'timestamp': start_time},
                {'role': 'assistant', 'content': '您好！有什么可以帮助您的吗？', 'timestamp': start_time}
            ],
            'tags': ['greeting'],
            'created_at': start_time
        }
    ]


def _get_conversations_by_ids(conversation_ids: List[str]) -> List[Dict]:
    """根据ID列表获取对话数据
    
    Args:
        conversation_ids: 对话ID列表
        
    Returns:
        List[Dict]: 对话数据列表
    """
    # TODO: 实现实际的数据库查询逻辑
    return []


def _cleanup_low_weight_tags(tag_manager: TagManager) -> int:
    """清理低权重标签
    
    Args:
        tag_manager: 标签管理器实例
        
    Returns:
        int: 清理的标签数量
    """
    # TODO: 实现低权重标签清理逻辑
    # 可以遍历所有用户，清理权重过低的标签
    
    cleaned_count = 0
    
    # 示例实现
    try:
        # 获取所有用户ID（需要根据实际情况实现）
        user_ids = _get_all_user_ids()
        
        for user_id in user_ids:
            try:
                existing_tags = tag_manager._get_existing_tags(user_id)
                
                # 过滤低权重标签
                filtered_tags = {
                    name: tag for name, tag in existing_tags.items()
                    if tag.weight >= tag_manager.config.min_weight_threshold
                }
                
                # 如果有标签被过滤，更新用户标签
                if len(filtered_tags) < len(existing_tags):
                    tag_manager._save_tags(user_id, filtered_tags)
                    cleaned_count += len(existing_tags) - len(filtered_tags)
                    
            except Exception as e:
                logger.error(f"清理用户 {user_id} 标签失败: {str(e)}")
                
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
    
    return cleaned_count


def _get_all_user_ids() -> List[str]:
    """获取所有用户ID
    
    Returns:
        List[str]: 用户ID列表
    """
    # TODO: 实现实际的用户ID获取逻辑
    return []


def _vectorize_knowledge_item(knowledge_item: Dict) -> List[float]:
    """将知识项向量化
    
    Args:
        knowledge_item: 知识项数据
        
    Returns:
        List[float]: 向量表示
    """
    # TODO: 实现实际的向量化逻辑
    # 可以使用sentence-transformers等模型
    
    # 示例：返回随机向量
    import random
    return [random.random() for _ in range(768)]


def _store_to_vector_db(knowledge_item: Dict, vector: List[float]) -> bool:
    """存储到向量数据库
    
    Args:
        knowledge_item: 知识项数据
        vector: 向量表示
        
    Returns:
        bool: 是否成功
    """
    # TODO: 实现实际的向量数据库存储逻辑
    # 可以集成Milvus、Pinecone等
    
    try:
        # 模拟存储过程
        logger.info(f"存储知识项到向量数据库: {knowledge_item.get('question', 'Unknown')}")
        return True
    except Exception as e:
        logger.error(f"向量数据库存储失败: {str(e)}")
        return False 