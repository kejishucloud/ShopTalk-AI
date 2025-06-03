"""
智能体控制器模块
提供智能体各功能模块的业务逻辑接口
"""

import logging
from typing import Dict, List, Optional, Any
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
import json

from .services import (
    TagManager, SentimentAnalyzer, ContextManager, 
    KBResponder, ChatIngestor
)

logger = logging.getLogger(__name__)


class AgentController:
    """智能体控制器基类"""
    
    def __init__(self):
        self.tag_manager = TagManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.context_manager = ContextManager()
        self.kb_responder = KBResponder()
        self.chat_ingestor = ChatIngestor()
    
    def _create_response(self, success: bool = True, data: Any = None, 
                        message: str = "", error: str = "") -> Dict:
        """创建标准化响应"""
        response = {
            'success': success,
            'timestamp': timezone.now().isoformat(),
            'message': message
        }
        
        if success:
            response['data'] = data
        else:
            response['error'] = error
        
        return response


class UserTagController(AgentController):
    """用户标签控制器
    
    处理用户标签相关的业务逻辑
    """
    
    def analyze_and_update_tags(self, user_id: str, message: str) -> Dict:
        """分析消息并更新用户标签
        
        Args:
            user_id: 用户ID
            message: 用户消息内容
            
        Returns:
            Dict: 操作结果
        """
        try:
            # 分析消息获取标签
            tags = self.tag_manager.analyze_message_tags(user_id, message)
            
            if not tags:
                return self._create_response(
                    success=True,
                    data={'tags': [], 'updated': False},
                    message="未检测到新标签"
                )
            
            # 更新用户标签
            success = self.tag_manager.update_user_tags(user_id, tags)
            
            if success:
                # 获取更新后的标签
                updated_tags = self.tag_manager.get_user_tags(user_id)
                
                return self._create_response(
                    success=True,
                    data={
                        'new_tags': [tag.__dict__ for tag in tags],
                        'all_tags': [tag.__dict__ for tag in updated_tags],
                        'updated': True
                    },
                    message=f"成功更新 {len(tags)} 个标签"
                )
            else:
                return self._create_response(
                    success=False,
                    error="标签更新失败"
                )
                
        except Exception as e:
            logger.error(f"标签分析更新失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"标签分析更新失败: {str(e)}"
            )
    
    def get_user_tags(self, user_id: str) -> Dict:
        """获取用户所有标签
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户标签数据
        """
        try:
            tags = self.tag_manager.get_user_tags(user_id)
            
            # 按权重排序
            sorted_tags = sorted(tags, key=lambda x: x.weight, reverse=True)
            
            return self._create_response(
                success=True,
                data={
                    'user_id': user_id,
                    'tags': [tag.__dict__ for tag in sorted_tags],
                    'tag_count': len(sorted_tags)
                },
                message=f"获取到 {len(sorted_tags)} 个用户标签"
            )
            
        except Exception as e:
            logger.error(f"获取用户标签失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"获取用户标签失败: {str(e)}"
            )
    
    def update_tag_weight(self, user_id: str, tag_name: str, weight: float) -> Dict:
        """手动更新标签权重
        
        Args:
            user_id: 用户ID
            tag_name: 标签名称
            weight: 新权重值
            
        Returns:
            Dict: 操作结果
        """
        try:
            # 获取现有标签
            existing_tags = self.tag_manager._get_existing_tags(user_id)
            
            if tag_name not in existing_tags:
                return self._create_response(
                    success=False,
                    error=f"标签 {tag_name} 不存在"
                )
            
            # 更新权重
            tag = existing_tags[tag_name]
            tag.weight = weight
            
            # 保存更新
            success = self.tag_manager._save_tags(user_id, existing_tags)
            
            if success:
                return self._create_response(
                    success=True,
                    data={'tag_name': tag_name, 'new_weight': weight},
                    message=f"成功更新标签 {tag_name} 权重为 {weight}"
                )
            else:
                return self._create_response(
                    success=False,
                    error="权重更新失败"
                )
                
        except Exception as e:
            logger.error(f"更新标签权重失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"更新标签权重失败: {str(e)}"
            )


class SentimentController(AgentController):
    """情感分析控制器
    
    处理情感分析相关的业务逻辑
    """
    
    def analyze_text_sentiment(self, text: str, user_id: str = None) -> Dict:
        """分析文本情感
        
        Args:
            text: 待分析的文本
            user_id: 用户ID（可选）
            
        Returns:
            Dict: 情感分析结果
        """
        try:
            # 执行情感分析
            result = self.sentiment_analyzer.analyze_sentiment(text)
            
            # 如果提供了用户ID，可以保存分析历史
            if user_id:
                self._save_sentiment_history(user_id, text, result)
            
            return self._create_response(
                success=True,
                data={
                    'text': text,
                    'sentiment': result.__dict__,
                    'user_id': user_id
                },
                message="情感分析完成"
            )
            
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"情感分析失败: {str(e)}"
            )
    
    def batch_analyze_sentiment(self, texts: List[str], user_id: str = None) -> Dict:
        """批量情感分析
        
        Args:
            texts: 待分析的文本列表
            user_id: 用户ID（可选）
            
        Returns:
            Dict: 批量分析结果
        """
        try:
            results = []
            
            for text in texts:
                result = self.sentiment_analyzer.analyze_sentiment(text)
                results.append({
                    'text': text,
                    'sentiment': result.__dict__
                })
            
            # 统计情感分布
            sentiment_stats = self._calculate_sentiment_stats(results)
            
            return self._create_response(
                success=True,
                data={
                    'results': results,
                    'statistics': sentiment_stats,
                    'total_count': len(texts),
                    'user_id': user_id
                },
                message=f"批量分析完成，共 {len(texts)} 条文本"
            )
            
        except Exception as e:
            logger.error(f"批量情感分析失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"批量情感分析失败: {str(e)}"
            )
    
    def _save_sentiment_history(self, user_id: str, text: str, result) -> bool:
        """保存情感分析历史"""
        # TODO: 实现情感分析历史保存逻辑
        # 可以保存到数据库或缓存中
        return True
    
    def _calculate_sentiment_stats(self, results: List[Dict]) -> Dict:
        """计算情感统计"""
        stats = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'average_score': 0.0
        }
        
        if not results:
            return stats
        
        total_score = 0.0
        for result in results:
            sentiment = result['sentiment']
            polarity = sentiment['polarity']
            score = sentiment['score']
            
            stats[polarity] += 1
            total_score += score
        
        stats['average_score'] = total_score / len(results)
        
        return stats


class ContextController(AgentController):
    """上下文控制器
    
    处理对话上下文相关的业务逻辑
    """
    
    def add_message_to_context(self, session_id: str, message: Dict) -> Dict:
        """添加消息到上下文
        
        Args:
            session_id: 会话ID
            message: 消息数据
            
        Returns:
            Dict: 操作结果
        """
        try:
            # 确保消息格式正确
            if not all(key in message for key in ['role', 'content']):
                return self._create_response(
                    success=False,
                    error="消息格式不正确，必须包含 role 和 content"
                )
            
            # 添加时间戳
            if 'timestamp' not in message:
                message['timestamp'] = timezone.now()
            
            # 添加到上下文
            success = self.context_manager.add_message(session_id, message)
            
            if success:
                # 获取更新后的上下文
                context = self.context_manager.get_context(session_id)
                
                return self._create_response(
                    success=True,
                    data={
                        'session_id': session_id,
                        'message_added': message,
                        'context_length': len(context.messages) if context else 0,
                        'has_summary': bool(context.summary) if context else False
                    },
                    message="消息已添加到上下文"
                )
            else:
                return self._create_response(
                    success=False,
                    error="添加消息到上下文失败"
                )
                
        except Exception as e:
            logger.error(f"添加消息到上下文失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"添加消息到上下文失败: {str(e)}"
            )
    
    def get_session_context(self, session_id: str, format_for_llm: bool = False) -> Dict:
        """获取会话上下文
        
        Args:
            session_id: 会话ID
            format_for_llm: 是否格式化为LLM可用格式
            
        Returns:
            Dict: 上下文数据
        """
        try:
            if format_for_llm:
                # 获取格式化的上下文字符串
                context_text = self.context_manager.get_context_for_llm(session_id)
                
                return self._create_response(
                    success=True,
                    data={
                        'session_id': session_id,
                        'context_text': context_text,
                        'formatted_for_llm': True
                    },
                    message="获取LLM格式上下文成功"
                )
            else:
                # 获取完整上下文数据
                context = self.context_manager.get_context(session_id)
                
                if context:
                    return self._create_response(
                        success=True,
                        data={
                            'session_id': context.session_id,
                            'messages': context.messages,
                            'summary': context.summary,
                            'updated_at': context.updated_at.isoformat(),
                            'message_count': len(context.messages)
                        },
                        message="获取上下文成功"
                    )
                else:
                    return self._create_response(
                        success=True,
                        data={'session_id': session_id, 'context': None},
                        message="会话上下文不存在"
                    )
                    
        except Exception as e:
            logger.error(f"获取会话上下文失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"获取会话上下文失败: {str(e)}"
            )
    
    def clear_session_context(self, session_id: str) -> Dict:
        """清理会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 操作结果
        """
        try:
            # TODO: 实现上下文清理逻辑
            # 可以从Redis和数据库中删除对应的上下文数据
            
            return self._create_response(
                success=True,
                data={'session_id': session_id},
                message="会话上下文已清理"
            )
            
        except Exception as e:
            logger.error(f"清理会话上下文失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"清理会话上下文失败: {str(e)}"
            )


class KnowledgeController(AgentController):
    """知识库控制器
    
    处理知识库查询和响应相关的业务逻辑
    """
    
    def query_and_respond(self, query: str, user_id: str = None, 
                         session_id: str = None, filters: Dict = None) -> Dict:
        """查询知识库并生成响应
        
        Args:
            query: 用户查询
            user_id: 用户ID
            session_id: 会话ID
            filters: 查询过滤条件
            
        Returns:
            Dict: 查询和响应结果
        """
        try:
            # 获取上下文信息
            context_text = ""
            if session_id:
                context_text = self.context_manager.get_context_for_llm(session_id)
            
            # 查询知识库
            kb_result = self.kb_responder.query_knowledge_base(
                query=query,
                user_id=user_id,
                filters=filters
            )
            
            if not kb_result['success']:
                return self._create_response(
                    success=False,
                    error=kb_result.get('error', '知识库查询失败')
                )
            
            # 生成答案
            documents = kb_result.get('documents', [])
            answer = self.kb_responder.generate_answer(query, documents, context_text)
            
            # 如果有会话ID，将问答添加到上下文
            if session_id:
                user_message = {
                    'role': 'user',
                    'content': query,
                    'timestamp': timezone.now()
                }
                assistant_message = {
                    'role': 'assistant', 
                    'content': answer,
                    'timestamp': timezone.now()
                }
                
                self.context_manager.add_message(session_id, user_message)
                self.context_manager.add_message(session_id, assistant_message)
            
            return self._create_response(
                success=True,
                data={
                    'query': query,
                    'answer': answer,
                    'knowledge_base_result': kb_result,
                    'context_used': bool(context_text),
                    'user_id': user_id,
                    'session_id': session_id
                },
                message="知识库查询和响应完成"
            )
            
        except Exception as e:
            logger.error(f"知识库查询响应失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"知识库查询响应失败: {str(e)}"
            )
    
    def search_knowledge_only(self, query: str, user_id: str = None, 
                             filters: Dict = None, top_k: int = 5) -> Dict:
        """仅搜索知识库（不生成答案）
        
        Args:
            query: 查询内容
            user_id: 用户ID
            filters: 过滤条件
            top_k: 返回结果数量
            
        Returns:
            Dict: 搜索结果
        """
        try:
            result = self.kb_responder.query_knowledge_base(
                query=query,
                user_id=user_id,
                filters=filters,
                top_k=top_k
            )
            
            return self._create_response(
                success=result['success'],
                data=result,
                message="知识库搜索完成" if result['success'] else "",
                error=result.get('error', '') if not result['success'] else ""
            )
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"知识库搜索失败: {str(e)}"
            )


class ChatIngestionController(AgentController):
    """聊天数据入库控制器
    
    处理对话数据分析和入库相关的业务逻辑
    """
    
    def process_single_conversation(self, conversation_data: Dict) -> Dict:
        """处理单个对话
        
        Args:
            conversation_data: 对话数据
            
        Returns:
            Dict: 处理结果
        """
        try:
            result = self.chat_ingestor.process_conversation(conversation_data)
            
            if 'error' in result:
                return self._create_response(
                    success=False,
                    error=result['error']
                )
            
            return self._create_response(
                success=True,
                data=result,
                message="对话处理完成"
            )
            
        except Exception as e:
            logger.error(f"对话处理失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"对话处理失败: {str(e)}"
            )
    
    def batch_ingest_conversations(self, conversations: List[Dict]) -> Dict:
        """批量入库对话数据
        
        Args:
            conversations: 对话数据列表
            
        Returns:
            Dict: 批量处理结果
        """
        try:
            result = self.chat_ingestor.batch_ingest_conversations(conversations)
            
            return self._create_response(
                success=True,
                data=result,
                message=f"批量入库完成: {result['processed']}/{result['total']}"
            )
            
        except Exception as e:
            logger.error(f"批量入库失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"批量入库失败: {str(e)}"
            )


class ComprehensiveAgentController(AgentController):
    """综合智能体控制器
    
    提供完整的智能体对话处理流程
    """
    
    def process_user_message(self, user_id: str, session_id: str, 
                           message: str, enable_kb: bool = True) -> Dict:
        """处理用户消息的完整流程
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            enable_kb: 是否启用知识库查询
            
        Returns:
            Dict: 处理结果
        """
        try:
            processing_result = {
                'user_id': user_id,
                'session_id': session_id,
                'message': message,
                'timestamp': timezone.now().isoformat(),
                'steps': {}
            }
            
            # 1. 情感分析
            sentiment_result = self.sentiment_analyzer.analyze_sentiment(message)
            processing_result['steps']['sentiment'] = sentiment_result.__dict__
            
            # 2. 标签分析和更新
            tag_result = self.tag_manager.analyze_message_tags(user_id, message)
            if tag_result:
                self.tag_manager.update_user_tags(user_id, tag_result)
                processing_result['steps']['tags'] = [tag.__dict__ for tag in tag_result]
            
            # 3. 添加到上下文
            user_msg = {
                'role': 'user',
                'content': message,
                'timestamp': timezone.now()
            }
            self.context_manager.add_message(session_id, user_msg)
            processing_result['steps']['context_updated'] = True
            
            # 4. 知识库查询（如果启用）
            answer = "收到您的消息，我正在处理中..."
            if enable_kb:
                context_text = self.context_manager.get_context_for_llm(session_id)
                kb_result = self.kb_responder.query_knowledge_base(
                    query=message,
                    user_id=user_id
                )
                
                if kb_result['success']:
                    documents = kb_result.get('documents', [])
                    answer = self.kb_responder.generate_answer(message, documents, context_text)
                    processing_result['steps']['knowledge_base'] = {
                        'used': True,
                        'documents_found': len(documents)
                    }
                else:
                    processing_result['steps']['knowledge_base'] = {
                        'used': False,
                        'error': kb_result.get('error')
                    }
            
            # 5. 添加助手回复到上下文
            assistant_msg = {
                'role': 'assistant',
                'content': answer,
                'timestamp': timezone.now()
            }
            self.context_manager.add_message(session_id, assistant_msg)
            
            processing_result['answer'] = answer
            
            return self._create_response(
                success=True,
                data=processing_result,
                message="用户消息处理完成"
            )
            
        except Exception as e:
            logger.error(f"用户消息处理失败: {str(e)}")
            return self._create_response(
                success=False,
                error=f"用户消息处理失败: {str(e)}"
            ) 