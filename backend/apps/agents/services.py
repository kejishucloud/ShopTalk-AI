"""
智能体服务层
管理智能体的初始化、配置和生命周期
"""

import os
import logging
from typing import Dict, Any, List
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import requests

logger = logging.getLogger(__name__)

# 全局智能体实例
_agent_instances = {}


def initialize_agents():
    """初始化所有智能体"""
    try:
        # 导入智能体类
        from agents.tag_agent import TagAgent
        from agents.sentiment_agent import SentimentAgent
        from agents.memory_agent import MemoryAgent
        from agents.knowledge_agent import KnowledgeAgent
        from agents.chat_agent import ChatAgent
        from agents.base_agent import agent_manager
        
        # 读取配置
        agent_config = getattr(settings, 'AGENT_CONFIG', {})
        
        # 初始化标签智能体
        tag_config = agent_config.get('tag_agent', {})
        tag_agent = TagAgent(tag_config)
        agent_manager.register_agent(tag_agent)
        _agent_instances['tag_agent'] = tag_agent
        
        # 初始化情感智能体
        sentiment_config = agent_config.get('sentiment_agent', {})
        sentiment_agent = SentimentAgent(sentiment_config)
        agent_manager.register_agent(sentiment_agent)
        _agent_instances['sentiment_agent'] = sentiment_agent
        
        # 初始化记忆智能体
        memory_config = agent_config.get('memory_agent', {
            'max_short_memory': 50,
            'max_long_memory': 200,
            'context_window': 15,
            'memory_decay_hours': 48
        })
        memory_agent = MemoryAgent(memory_config)
        agent_manager.register_agent(memory_agent)
        _agent_instances['memory_agent'] = memory_agent
        
        # 初始化知识库智能体
        knowledge_config = agent_config.get('knowledge_agent', {
            'ragflow': {
                'api_endpoint': os.getenv('RAGFLOW_API_ENDPOINT', 'http://localhost:9380'),
                'api_key': os.getenv('RAGFLOW_API_KEY', ''),
                'dataset_id': os.getenv('RAGFLOW_DATASET_ID', '')
            },
            'top_k': 5,
            'similarity_threshold': 0.7,
            'max_tokens': 1000
        })
        knowledge_agent = KnowledgeAgent(knowledge_config)
        agent_manager.register_agent(knowledge_agent)
        _agent_instances['knowledge_agent'] = knowledge_agent
        
        # 初始化聊天智能体
        chat_config = agent_config.get('chat_agent', {
            'langflow': {
                'endpoint': os.getenv('LANGFLOW_ENDPOINT', 'http://localhost:7860'),
                'api_key': os.getenv('LANGFLOW_API_KEY', ''),
                'flow_id': os.getenv('LANGFLOW_FLOW_ID', '')
            },
            'llm': {
                'model': os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
                'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '1000'))
            }
        })
        chat_agent = ChatAgent(chat_config)
        agent_manager.register_agent(chat_agent)
        _agent_instances['chat_agent'] = chat_agent
        
        logger.info(f"Successfully initialized {len(_agent_instances)} agents")
        
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")


def get_agent_instance(agent_name: str):
    """获取智能体实例"""
    return _agent_instances.get(agent_name)


def get_all_agent_instances() -> Dict[str, Any]:
    """获取所有智能体实例"""
    return _agent_instances.copy()


def update_agent_config(agent_name: str, config: Dict[str, Any]):
    """更新智能体配置"""
    agent = get_agent_instance(agent_name)
    if agent:
        agent.update_config(config)
        logger.info(f"Updated config for agent: {agent_name}")
    else:
        logger.warning(f"Agent not found: {agent_name}")


def get_agent_status() -> Dict[str, Any]:
    """获取所有智能体状态"""
    status = {}
    for name, agent in _agent_instances.items():
        try:
            status[name] = agent.get_status()
        except Exception as e:
            status[name] = {'error': str(e), 'is_active': False}
    
    return status


def activate_agent(agent_name: str):
    """激活智能体"""
    agent = get_agent_instance(agent_name)
    if agent:
        agent.activate()
        logger.info(f"Activated agent: {agent_name}")
    else:
        logger.warning(f"Agent not found: {agent_name}")


def deactivate_agent(agent_name: str):
    """停用智能体"""
    agent = get_agent_instance(agent_name)
    if agent:
        agent.deactivate()
        logger.info(f"Deactivated agent: {agent_name}")
    else:
        logger.warning(f"Agent not found: {agent_name}")


async def process_chat_message(user_id: str, message: str, session_id: str = None, 
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
    """处理聊天消息的便捷方法"""
    try:
        from agents.base_agent import agent_manager
        
        input_data = {
            'user_id': user_id,
            'message': message,
            'session_id': session_id or 'default',
            'context': context or {}
        }
        
        result = await agent_manager.process_with_agent('chat_agent', input_data)
        return result
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }


async def analyze_user_tags(user_id: str, message: str, 
                           session_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """分析用户标签的便捷方法"""
    try:
        from agents.base_agent import agent_manager
        
        input_data = {
            'user_id': user_id,
            'message': message,
            'session_data': session_data or {},
            'user_history': []
        }
        
        result = await agent_manager.process_with_agent('tag_agent', input_data)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing user tags: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }


async def analyze_sentiment(user_id: str, message: str, 
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
    """分析情感的便捷方法"""
    try:
        from agents.base_agent import agent_manager
        
        input_data = {
            'user_id': user_id,
            'message': message,
            'context': context or {}
        }
        
        result = await agent_manager.process_with_agent('sentiment_agent', input_data)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }


async def query_knowledge(query: str, user_id: str = None, 
                         knowledge_base: str = None, 
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
    """查询知识库的便捷方法"""
    try:
        from agents.base_agent import agent_manager
        
        input_data = {
            'query': query,
            'user_id': user_id or 'anonymous',
            'knowledge_base': knowledge_base or 'general',
            'context': context or {}
        }
        
        result = await agent_manager.process_with_agent('knowledge_agent', input_data)
        return result
        
    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }


def cleanup_agents():
    """清理智能体资源"""
    try:
        # 清理内存智能体的过期记忆
        memory_agent = get_agent_instance('memory_agent')
        if memory_agent:
            memory_agent.clear_expired_memory()
        
        logger.info("Agent cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during agent cleanup: {e}")


class AgentManager:
    """智能体管理器的Django包装类"""
    
    @staticmethod
    def get_available_agents():
        """获取可用的智能体列表"""
        return list(_agent_instances.keys())
    
    @staticmethod
    async def run_agent_pipeline(agent_names: list, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行智能体流水线"""
        try:
            from agents.base_agent import agent_manager
            return await agent_manager.process_pipeline(agent_names, input_data)
        except Exception as e:
            logger.error(f"Error running agent pipeline: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    @staticmethod
    def get_agent_metrics() -> Dict[str, Any]:
        """获取智能体性能指标"""
        metrics = {
            'total_agents': len(_agent_instances),
            'active_agents': 0,
            'agent_details': {}
        }
        
        for name, agent in _agent_instances.items():
            try:
                status = agent.get_status()
                if status.get('is_active'):
                    metrics['active_agents'] += 1
                
                metrics['agent_details'][name] = {
                    'is_active': status.get('is_active', False),
                    'created_at': status.get('created_at'),
                    'config_size': len(status.get('config', {}))
                }
                
                # 特殊指标
                if name == 'knowledge_agent' and hasattr(agent, 'get_query_statistics'):
                    metrics['agent_details'][name]['query_stats'] = agent.get_query_statistics()
                
            except Exception as e:
                metrics['agent_details'][name] = {'error': str(e)}
        
        return metrics 


class KBResponder:
    """知识库响应器
    
    负责调用RAGFlow接口，根据用户查询检索知识库并生成回答
    """
    
    def __init__(self):
        """初始化知识库响应器"""
        self.config = get_ragflow_config()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        })
    
    def query_knowledge_base(self, query: str, user_id: str = None, 
                           filters: Dict = None, top_k: int = 5) -> Dict:
        """查询知识库
        
        Args:
            query: 用户查询内容
            user_id: 用户ID，用于个性化检索
            filters: 检索过滤条件
            top_k: 返回结果数量
            
        Returns:
            Dict: 知识库查询结果
        """
        try:
            # 构造请求体
            request_data = {
                'query': query,
                'top_k': top_k,
                'include_metadata': True,
                'stream': False
            }
            
            # 添加过滤条件
            if filters:
                request_data['filters'] = filters
            
            # 添加用户上下文
            if user_id:
                request_data['user_id'] = user_id
                # 获取用户标签作为检索上下文
                tag_manager = TagManager()
                user_tags = tag_manager.get_user_tags(user_id)
                if user_tags:
                    request_data['user_context'] = {
                        'tags': [tag.tag_name for tag in user_tags[:5]]  # 前5个标签
                    }
            
            # 发送请求到RAGFlow
            url = f"{self.config.base_url}/api/v1/retrieval"
            response = self.session.post(
                url,
                json=request_data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 处理返回结果
            processed_result = self._process_ragflow_response(result)
            
            logger.info(f"知识库查询成功: query={query}, results={len(processed_result.get('documents', []))}")
            
            return processed_result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RAGFlow请求失败: {str(e)}")
            return self._get_fallback_response(query)
        except Exception as e:
            logger.error(f"知识库查询失败: {str(e)}")
            return self._get_fallback_response(query)
    
    def _process_ragflow_response(self, response: Dict) -> Dict:
        """处理RAGFlow响应数据
        
        Args:
            response: RAGFlow原始响应
            
        Returns:
            Dict: 处理后的响应数据
        """
        processed = {
            'success': True,
            'query_id': response.get('query_id'),
            'documents': [],
            'answer': None,
            'metadata': {}
        }
        
        # 处理检索到的文档
        documents = response.get('documents', [])
        for doc in documents:
            processed_doc = {
                'content': doc.get('content', ''),
                'title': doc.get('metadata', {}).get('title', ''),
                'source': doc.get('metadata', {}).get('source', ''),
                'score': doc.get('score', 0.0),
                'chunk_id': doc.get('chunk_id'),
                'metadata': doc.get('metadata', {})
            }
            processed['documents'].append(processed_doc)
        
        # 处理生成的答案
        if 'answer' in response:
            processed['answer'] = {
                'content': response['answer'].get('content', ''),
                'confidence': response['answer'].get('confidence', 0.0),
                'sources': response['answer'].get('sources', [])
            }
        
        # 处理元数据
        processed['metadata'] = {
            'total_documents': response.get('total_documents', 0),
            'search_time': response.get('search_time', 0),
            'model_used': response.get('model_used', ''),
            'timestamp': timezone.now().isoformat()
        }
        
        return processed
    
    def generate_answer(self, query: str, documents: List[Dict], 
                       context: str = None) -> str:
        """基于检索文档生成答案
        
        Args:
            query: 用户查询
            documents: 检索到的文档列表
            context: 对话上下文
            
        Returns:
            str: 生成的答案
        """
        if not documents:
            return "抱歉，我没有找到相关的信息来回答您的问题。"
        
        # 构造上下文信息
        context_parts = []
        
        if context:
            context_parts.append(f"对话上下文：\n{context}")
        
        context_parts.append("相关知识：")
        for i, doc in enumerate(documents[:3], 1):  # 使用前3个最相关的文档
            context_parts.append(f"{i}. {doc['content'][:200]}...")
        
        context_parts.append(f"\n基于以上信息，请回答用户的问题：{query}")
        
        # 调用Langflow生成答案
        langflow_config = get_langflow_config()
        
        try:
            response = requests.post(
                f"{langflow_config.base_url}/api/v1/run/{langflow_config.flow_id}",
                json={
                    'inputs': {
                        'context': '\n'.join(context_parts),
                        'query': query
                    }
                },
                headers={
                    'Authorization': f'Bearer {langflow_config.api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=langflow_config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 提取生成的答案
            if 'outputs' in result:
                return result['outputs'].get('answer', '生成答案时出现问题。')
            
            return result.get('answer', '生成答案时出现问题。')
            
        except Exception as e:
            logger.error(f"Langflow生成答案失败: {str(e)}")
            return self._generate_simple_answer(query, documents)
    
    def _generate_simple_answer(self, query: str, documents: List[Dict]) -> str:
        """生成简单答案（备用方法）"""
        if not documents:
            return "抱歉，没有找到相关信息。"
        
        # 选择最相关的文档
        best_doc = documents[0]
        
        return f"根据我的知识库，{best_doc['content'][:150]}... 这个信息可能对您有帮助。"
    
    def _get_fallback_response(self, query: str) -> Dict:
        """获取备用响应"""
        return {
            'success': False,
            'documents': [],
            'answer': None,
            'error': '知识库服务暂时不可用，请稍后再试。',
            'metadata': {
                'timestamp': timezone.now().isoformat(),
                'fallback': True
            }
        }


class ChatIngestor:
    """聊天数据入库处理器
    
    负责将对话数据根据标签、关键词、意图分类，批量写入知识库
    支持话术知识库和产品知识库的分类存储
    """
    
    def __init__(self):
        """初始化聊天数据处理器"""
        self.config = get_knowledge_base_config()
        self.tag_manager = TagManager()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def process_conversation(self, conversation_data: Dict) -> Dict:
        """处理单个对话数据
        
        Args:
            conversation_data: 对话数据
            {
                'conversation_id': str,
                'user_id': str,
                'messages': List[Dict],
                'tags': List[str],
                'created_at': datetime
            }
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 分析对话内容
            analysis_result = self._analyze_conversation(conversation_data)
            
            # 分类对话类型
            conversation_type = self._classify_conversation_type(
                conversation_data, analysis_result
            )
            
            # 提取知识点
            knowledge_items = self._extract_knowledge_items(
                conversation_data, analysis_result, conversation_type
            )
            
            # 准备入库数据
            ingest_result = {
                'conversation_id': conversation_data['conversation_id'],
                'analysis': analysis_result,
                'type': conversation_type,
                'knowledge_items': knowledge_items,
                'processed_at': timezone.now()
            }
            
            return ingest_result
            
        except Exception as e:
            logger.error(f"处理对话数据失败: {conversation_data.get('conversation_id')}, 错误: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_conversation(self, conversation_data: Dict) -> Dict:
        """分析对话内容
        
        Args:
            conversation_data: 对话数据
            
        Returns:
            Dict: 分析结果
        """
        messages = conversation_data['messages']
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        # 情感分析
        sentiments = []
        for msg in user_messages:
            sentiment = self.sentiment_analyzer.analyze_sentiment(msg['content'])
            sentiments.append(sentiment)
        
        # 统计情感分布
        sentiment_stats = {
            'positive': sum(1 for s in sentiments if s.polarity == 'positive'),
            'negative': sum(1 for s in sentiments if s.polarity == 'negative'),
            'neutral': sum(1 for s in sentiments if s.polarity == 'neutral'),
            'average_score': sum(s.score for s in sentiments) / len(sentiments) if sentiments else 0.5
        }
        
        # 提取关键词
        all_text = ' '.join([msg['content'] for msg in user_messages])
        keywords = self._extract_keywords(all_text)
        
        # 检测意图
        intents = self._detect_intents(user_messages)
        
        return {
            'message_count': len(messages),
            'user_message_count': len(user_messages),
            'assistant_message_count': len(assistant_messages),
            'sentiment_stats': sentiment_stats,
            'keywords': keywords,
            'intents': intents,
            'conversation_length': sum(len(msg['content']) for msg in messages)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取实现
        # 实际应用中可以使用更复杂的NLP方法
        
        import re
        
        # 移除标点符号并分词
        words = re.findall(r'\b\w+\b', text)
        
        # 过滤停用词
        stop_words = {'的', '了', '和', '是', '在', '有', '我', '你', '他', '她', '它'}
        words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # 返回高频词
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10] if count > 1]
    
    def _detect_intents(self, user_messages: List[Dict]) -> List[str]:
        """检测用户意图"""
        intents = []
        
        # 意图关键词映射
        intent_keywords = {
            'product_inquiry': ['产品', '价格', '规格', '参数', '介绍'],
            'service_request': ['售后', '服务', '维修', '保修', '客服'],
            'complaint': ['投诉', '问题', '不满意', '差评', '退货'],
            'purchase': ['购买', '下单', '付款', '订单', '买'],
            'consultation': ['咨询', '询问', '了解', '请问', '想知道']
        }
        
        for msg in user_messages:
            content = msg['content']
            for intent, keywords in intent_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if intent not in intents:
                        intents.append(intent)
        
        return intents
    
    def _classify_conversation_type(self, conversation_data: Dict, 
                                  analysis_result: Dict) -> str:
        """分类对话类型
        
        Args:
            conversation_data: 对话数据
            analysis_result: 分析结果
            
        Returns:
            str: 对话类型 ('script', 'product', 'service', 'other')
        """
        intents = analysis_result.get('intents', [])
        keywords = analysis_result.get('keywords', [])
        
        # 话术类型判断
        script_indicators = ['怎么说', '话术', '回复', '应答', '处理方式']
        if any(indicator in ' '.join(keywords) for indicator in script_indicators):
            return 'script'
        
        # 产品类型判断
        if 'product_inquiry' in intents:
            return 'product'
        
        # 服务类型判断
        if 'service_request' in intents or 'complaint' in intents:
            return 'service'
        
        # 咨询类型判断
        if 'consultation' in intents:
            return 'consultation'
        
        return 'other'
    
    def _extract_knowledge_items(self, conversation_data: Dict, 
                                analysis_result: Dict, 
                                conversation_type: str) -> List[Dict]:
        """提取知识项
        
        Args:
            conversation_data: 对话数据
            analysis_result: 分析结果
            conversation_type: 对话类型
            
        Returns:
            List[Dict]: 知识项列表
        """
        knowledge_items = []
        messages = conversation_data['messages']
        
        # 提取问答对
        qa_pairs = self._extract_qa_pairs(messages)
        
        for qa in qa_pairs:
            knowledge_item = {
                'type': conversation_type,
                'question': qa['question'],
                'answer': qa['answer'],
                'keywords': analysis_result.get('keywords', []),
                'intents': analysis_result.get('intents', []),
                'sentiment': analysis_result.get('sentiment_stats', {}),
                'source': 'conversation',
                'source_id': conversation_data['conversation_id'],
                'created_at': conversation_data.get('created_at', timezone.now()),
                'metadata': {
                    'user_id': conversation_data.get('user_id'),
                    'conversation_length': analysis_result.get('conversation_length', 0),
                    'quality_score': self._calculate_quality_score(qa, analysis_result)
                }
            }
            knowledge_items.append(knowledge_item)
        
        return knowledge_items
    
    def _extract_qa_pairs(self, messages: List[Dict]) -> List[Dict]:
        """提取问答对"""
        qa_pairs = []
        
        for i in range(len(messages) - 1):
            current_msg = messages[i]
            next_msg = messages[i + 1]
            
            # 用户问题 + 助手回答
            if (current_msg['role'] == 'user' and 
                next_msg['role'] == 'assistant'):
                
                qa_pairs.append({
                    'question': current_msg['content'],
                    'answer': next_msg['content'],
                    'timestamp': current_msg.get('timestamp', timezone.now())
                })
        
        return qa_pairs
    
    def _calculate_quality_score(self, qa_pair: Dict, analysis_result: Dict) -> float:
        """计算知识质量分数"""
        score = 0.5  # 基础分数
        
        # 基于回答长度
        answer_length = len(qa_pair['answer'])
        if answer_length > 50:
            score += 0.2
        elif answer_length > 20:
            score += 0.1
        
        # 基于情感倾向
        sentiment_stats = analysis_result.get('sentiment_stats', {})
        if sentiment_stats.get('average_score', 0.5) > 0.6:
            score += 0.2
        
        # 基于意图明确性
        intents = analysis_result.get('intents', [])
        if len(intents) > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def batch_ingest_conversations(self, conversations: List[Dict]) -> Dict:
        """批量入库对话数据
        
        Args:
            conversations: 对话数据列表
            
        Returns:
            Dict: 批量处理结果
        """
        results = {
            'total': len(conversations),
            'processed': 0,
            'scripts_added': 0,
            'products_added': 0,
            'errors': []
        }
        
        try:
            with transaction.atomic():
                for conversation in conversations:
                    try:
                        # 处理对话
                        processed = self.process_conversation(conversation)
                        
                        if 'error' in processed:
                            results['errors'].append({
                                'conversation_id': conversation.get('conversation_id'),
                                'error': processed['error']
                            })
                            continue
                        
                        # 保存知识项
                        for item in processed['knowledge_items']:
                            if item['type'] == 'script':
                                self._save_to_scripts_kb(item)
                                results['scripts_added'] += 1
                            elif item['type'] == 'product':
                                self._save_to_products_kb(item)
                                results['products_added'] += 1
                        
                        results['processed'] += 1
                        
                    except Exception as e:
                        results['errors'].append({
                            'conversation_id': conversation.get('conversation_id'),
                            'error': str(e)
                        })
            
            logger.info(f"批量入库完成: 处理 {results['processed']}/{results['total']} 个对话")
            
        except Exception as e:
            logger.error(f"批量入库失败: {str(e)}")
            results['errors'].append({'global_error': str(e)})
        
        return results
    
    def _save_to_scripts_kb(self, knowledge_item: Dict):
        """保存到话术知识库"""
        # TODO: 实现实际的数据库保存逻辑
        # 这里可以使用Django ORM保存到话术知识库表
        logger.info(f"保存话术知识: {knowledge_item['question'][:50]}...")
    
    def _save_to_products_kb(self, knowledge_item: Dict):
        """保存到产品知识库"""
        # TODO: 实现实际的数据库保存逻辑
        # 这里可以使用Django ORM保存到产品知识库表
        logger.info(f"保存产品知识: {knowledge_item['question'][:50]}...")
    
    def cleanup_duplicate_knowledge(self) -> int:
        """清理重复的知识项
        
        Returns:
            int: 清理的重复项数量
        """
        # TODO: 实现重复知识项清理逻辑
        # 可以基于问题相似度、内容哈希等方法去重
        logger.info("开始清理重复知识项...")
        return 0 