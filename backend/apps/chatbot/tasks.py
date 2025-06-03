"""
智能客服管理模块定时任务
定时同步聊天记录到向量数据库，支持知识库自动更新
"""

from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
import logging

from apps.history.models import ChatMessage, ChatSession
from apps.knowledge.services import RAGFlowService, VectorSearchService
from apps.tags.models import TagAssignment
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger('chatbot.tasks')


@shared_task(bind=True)
def sync_daily_chat_to_vector_db(self, date_str=None):
    """
    定时任务：每天凌晨1点执行
    从history模块获取昨日聊天记录，分类后同步到向量索引
    """
    try:
        # 确定处理日期
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()
        
        logger.info(f"开始同步{target_date}的聊天记录到向量数据库")
        
        # 获取指定日期的聊天记录
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        # 获取有价值的聊天消息（用户消息且内容有意义）
        chat_messages = ChatMessage.objects.filter(
            created_at__range=(start_time, end_time),
            message_type='user',
            content__isnull=False
        ).exclude(
            content__in=['', ' ', '。', '？', '!', '，']  # 排除无意义内容
        ).select_related('session', 'user')
        
        logger.info(f"找到 {chat_messages.count()} 条聊天记录待处理")
        
        # 按会话分组处理
        processed_sessions = set()
        synced_count = 0
        failed_count = 0
        
        for message in chat_messages:
            session_id = message.session.id
            
            # 避免重复处理同一会话
            if session_id in processed_sessions:
                continue
            
            try:
                # 处理整个会话的聊天记录
                session_result = _process_chat_session(message.session, target_date)
                
                if session_result['success']:
                    synced_count += session_result['synced_count']
                    processed_sessions.add(session_id)
                else:
                    failed_count += 1
                    logger.error(f"处理会话失败: {session_id} - {session_result['error']}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"处理会话异常: {session_id} - {str(e)}")
        
        # 更新任务状态
        logger.info(f"聊天记录同步完成 - 成功: {synced_count}, 失败: {failed_count}")
        
        return {
            'success': True,
            'date': target_date.isoformat(),
            'processed_sessions': len(processed_sessions),
            'synced_count': synced_count,
            'failed_count': failed_count
        }
        
    except Exception as e:
        logger.error(f"定时任务执行失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def _process_chat_session(session: ChatSession, target_date: datetime) -> dict:
    """处理单个聊天会话"""
    try:
        # 获取会话的所有消息
        messages = ChatMessage.objects.filter(
            session=session,
            created_at__date=target_date
        ).order_by('created_at')
        
        if messages.count() < 2:  # 至少需要一问一答
            return {'success': True, 'synced_count': 0, 'reason': 'insufficient_messages'}
        
        # 分析会话内容
        session_analysis = _analyze_chat_session(session, messages)
        
        # 只同步有价值的会话（有明确问题和回答）
        if not session_analysis.get('has_valuable_content'):
            return {'success': True, 'synced_count': 0, 'reason': 'no_valuable_content'}
        
        # 构建向量数据库文档
        documents = _build_knowledge_documents(session, messages, session_analysis)
        
        # 同步到RAGFlow
        ragflow_service = RAGFlowService()
        synced_count = 0
        
        for doc in documents:
            try:
                result = ragflow_service.upload_document(doc)
                if result.get('success'):
                    synced_count += 1
                    # 记录同步成功的消息
                    _mark_message_synced(doc['metadata']['message_ids'], result.get('document_id'))
                else:
                    logger.warning(f"文档上传失败: {doc['id']} - {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"上传文档异常: {doc['id']} - {str(e)}")
        
        return {
            'success': True,
            'synced_count': synced_count,
            'total_documents': len(documents)
        }
        
    except Exception as e:
        logger.error(f"处理会话失败: {session.id} - {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def _analyze_chat_session(session: ChatSession, messages) -> dict:
    """分析聊天会话内容的价值"""
    user_messages = messages.filter(message_type='user')
    bot_messages = messages.filter(message_type='bot')
    
    # 获取会话标签
    content_type = ContentType.objects.get_for_model(ChatSession)
    tags = TagAssignment.objects.filter(
        content_type=content_type,
        object_id=session.id
    ).values_list('tag__name', flat=True)
    
    # 判断是否有价值
    has_valuable_content = (
        user_messages.count() >= 1 and
        bot_messages.count() >= 1 and
        any(len(msg.content.strip()) > 10 for msg in user_messages) and  # 有实质性问题
        not any(tag in ['测试', '无效', '垃圾'] for tag in tags)  # 没有负面标签
    )
    
    # 提取主要话题
    topics = []
    for tag in tags:
        if tag not in ['已处理', '正面情感', '负面情感']:
            topics.append(tag)
    
    return {
        'has_valuable_content': has_valuable_content,
        'user_message_count': user_messages.count(),
        'bot_message_count': bot_messages.count(),
        'session_duration': (messages.last().created_at - messages.first().created_at).total_seconds(),
        'topics': topics,
        'tags': list(tags)
    }


def _build_knowledge_documents(session: ChatSession, messages, analysis: dict) -> list:
    """构建知识库文档"""
    documents = []
    
    # 按问答对组织内容
    qa_pairs = []
    current_question = None
    
    for message in messages:
        if message.message_type == 'user':
            if current_question:
                # 保存前一个问答对
                qa_pairs.append(current_question)
            current_question = {
                'question': message.content,
                'question_id': message.id,
                'answers': [],
                'timestamp': message.created_at
            }
        elif message.message_type == 'bot' and current_question:
            current_question['answers'].append({
                'content': message.content,
                'message_id': message.id,
                'timestamp': message.created_at
            })
    
    # 添加最后一个问答对
    if current_question:
        qa_pairs.append(current_question)
    
    # 为每个有效的问答对创建文档
    for i, qa in enumerate(qa_pairs):
        if not qa['answers']:  # 跳过没有回答的问题
            continue
        
        # 组合问答内容
        content_parts = [f"问题：{qa['question']}"]
        
        for j, answer in enumerate(qa['answers']):
            content_parts.append(f"回答{j+1}：{answer['content']}")
        
        content = "\n\n".join(content_parts)
        
        # 构建文档
        document = {
            'id': f"chat_qa_{session.id}_{i}_{qa['question_id']}",
            'content': content,
            'metadata': {
                'session_id': session.id,
                'user_id': session.user.id if session.user else None,
                'platform': session.platform,
                'app_name': session.app_name,
                'question_id': qa['question_id'],
                'message_ids': [qa['question_id']] + [ans['message_id'] for ans in qa['answers']],
                'timestamp': qa['timestamp'].isoformat(),
                'topics': analysis['topics'],
                'tags': analysis['tags'],
                'source': 'chat_history',
                'qa_pair_index': i,
                'session_duration': analysis['session_duration']
            }
        }
        
        documents.append(document)
    
    return documents


def _mark_message_synced(message_ids: list, document_id: str):
    """标记消息已同步"""
    ChatMessage.objects.filter(
        id__in=message_ids
    ).update(
        synced_to_vector_db=True,
        vector_doc_id=document_id
    )


@shared_task(bind=True)
def cleanup_old_chat_records(self, days_to_keep=90):
    """清理旧的聊天记录"""
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # 删除旧的聊天消息
        deleted_messages, _ = ChatMessage.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        # 删除没有消息的会话
        deleted_sessions, _ = ChatSession.objects.filter(
            messages__isnull=True
        ).delete()
        
        logger.info(f"清理完成 - 删除消息: {deleted_messages}, 删除会话: {deleted_sessions}")
        
        return {
            'success': True,
            'deleted_messages': deleted_messages,
            'deleted_sessions': deleted_sessions,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理旧记录失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def update_chat_statistics(self, date_str=None):
    """更新聊天统计数据"""
    try:
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date()
        
        from apps.chatbot.models import ChatStatistics
        
        # 计算统计数据
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        total_sessions = ChatSession.objects.filter(
            created_at__range=(start_time, end_time)
        ).count()
        
        total_messages = ChatMessage.objects.filter(
            created_at__range=(start_time, end_time)
        ).count()
        
        user_messages = ChatMessage.objects.filter(
            created_at__range=(start_time, end_time),
            message_type='user'
        ).count()
        
        bot_messages = ChatMessage.objects.filter(
            created_at__range=(start_time, end_time),
            message_type='bot'
        ).count()
        
        # 获取转人工数量
        handoff_count = ChatSession.objects.filter(
            created_at__range=(start_time, end_time),
            status='transferred_to_human'
        ).count()
        
        # 保存或更新统计数据
        stats, created = ChatStatistics.objects.update_or_create(
            date=target_date,
            defaults={
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'user_messages': user_messages,
                'bot_messages': bot_messages,
                'handoff_count': handoff_count,
                'handoff_rate': round((handoff_count / total_sessions * 100) if total_sessions > 0 else 0, 2)
            }
        )
        
        logger.info(f"统计数据更新完成 - 日期: {target_date}, 会话数: {total_sessions}")
        
        return {
            'success': True,
            'date': target_date.isoformat(),
            'statistics': {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'user_messages': user_messages,
                'bot_messages': bot_messages,
                'handoff_count': handoff_count
            }
        }
        
    except Exception as e:
        logger.error(f"更新统计数据失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        } 