"""
AI智能客服代理核心模块
"""
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .knowledge_search import KnowledgeSearchEngine
from .intent_recognition import IntentRecognizer
from .sentiment_analysis import SentimentAnalyzer
from .response_generator import ResponseGenerator
from .model_providers import ModelProviderFactory

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """代理回复结果"""
    content: str
    confidence: float
    intent: Optional[str] = None
    entities: Optional[Dict] = None
    sentiment: Optional[str] = None
    knowledge_used: Optional[List[Dict]] = None
    should_handover: bool = False
    metadata: Optional[Dict] = None


class SmartTalkAgent:
    """SmartTalk AI智能客服代理"""
    
    def __init__(self, agent_config: Dict):
        """
        初始化AI代理
        
        Args:
            agent_config: 代理配置信息
        """
        self.config = agent_config
        self.agent_id = agent_config.get('id')
        self.name = agent_config.get('name', 'SmartTalk Agent')
        
        # 初始化各个组件
        self.knowledge_engine = KnowledgeSearchEngine(agent_config.get('knowledge_bases', []))
        self.intent_recognizer = IntentRecognizer(agent_config.get('intent_config', {}))
        self.sentiment_analyzer = SentimentAnalyzer()
        self.response_generator = ResponseGenerator(agent_config)
        
        # 初始化AI模型提供商
        model_config = agent_config.get('ai_model', {})
        self.model_provider = ModelProviderFactory.create_provider(model_config)
        
        # 代理设置
        self.system_prompt = agent_config.get('system_prompt', self._default_system_prompt())
        self.personality = agent_config.get('personality', '')
        self.max_context_length = agent_config.get('max_context_length', 10)
        self.confidence_threshold = agent_config.get('confidence_threshold', 0.8)
        self.temperature = agent_config.get('temperature', 0.7)
        
        # 功能开关
        self.enable_knowledge_search = agent_config.get('enable_knowledge_search', True)
        self.enable_intent_recognition = agent_config.get('enable_intent_recognition', True)
        self.enable_sentiment_analysis = agent_config.get('enable_sentiment_analysis', True)
        
        logger.info(f"AI代理 {self.name} 初始化完成")
    
    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        return """你是一个专业的AI客服助手，名字叫SmartTalk。你的任务是：

1. 友好、专业地回答客户问题
2. 基于知识库提供准确信息
3. 识别客户意图并给出合适回复
4. 在无法解决问题时，及时转接人工客服
5. 保持耐心和礼貌的服务态度

回复要求：
- 简洁明了，重点突出
- 语言亲切自然
- 提供具体有用的信息
- 必要时主动询问更多细节"""
    
    async def process_message(
        self, 
        message: str, 
        conversation_context: Dict,
        customer_info: Optional[Dict] = None
    ) -> AgentResponse:
        """
        处理客户消息
        
        Args:
            message: 客户消息内容
            conversation_context: 对话上下文
            customer_info: 客户信息
            
        Returns:
            AgentResponse: 代理回复结果
        """
        start_time = time.time()
        
        try:
            # 1. 意图识别
            intent_result = None
            if self.enable_intent_recognition:
                intent_result = await self.intent_recognizer.recognize(message)
                logger.debug(f"意图识别结果: {intent_result}")
            
            # 2. 情感分析
            sentiment_result = None
            if self.enable_sentiment_analysis:
                sentiment_result = await self.sentiment_analyzer.analyze(message)
                logger.debug(f"情感分析结果: {sentiment_result}")
            
            # 3. 知识库搜索
            knowledge_results = []
            if self.enable_knowledge_search:
                knowledge_results = await self.knowledge_engine.search(
                    query=message,
                    intent=intent_result.get('intent') if intent_result else None,
                    context=conversation_context
                )
                logger.debug(f"知识库搜索结果: {len(knowledge_results)} 条")
            
            # 4. 构建对话上下文
            enhanced_context = self._build_enhanced_context(
                message=message,
                conversation_context=conversation_context,
                intent_result=intent_result,
                sentiment_result=sentiment_result,
                knowledge_results=knowledge_results,
                customer_info=customer_info
            )
            
            # 5. 生成回复
            response = await self.response_generator.generate(
                message=message,
                context=enhanced_context,
                model_provider=self.model_provider
            )
            
            # 6. 判断是否需要人工接管
            should_handover = self._should_handover_to_human(
                intent_result=intent_result,
                sentiment_result=sentiment_result,
                confidence=response.get('confidence', 0.0),
                conversation_context=conversation_context
            )
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"消息处理完成，耗时: {execution_time:.2f}ms")
            
            return AgentResponse(
                content=response.get('content', ''),
                confidence=response.get('confidence', 0.0),
                intent=intent_result.get('intent') if intent_result else None,
                entities=intent_result.get('entities') if intent_result else None,
                sentiment=sentiment_result.get('sentiment') if sentiment_result else None,
                knowledge_used=knowledge_results,
                should_handover=should_handover,
                metadata={
                    'execution_time': execution_time,
                    'model_used': self.model_provider.model_name,
                    'knowledge_count': len(knowledge_results)
                }
            )
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {str(e)}", exc_info=True)
            return AgentResponse(
                content="抱歉，我遇到了一些技术问题，请稍后再试或联系人工客服。",
                confidence=0.0,
                should_handover=True,
                metadata={'error': str(e)}
            )
    
    def _build_enhanced_context(
        self,
        message: str,
        conversation_context: Dict,
        intent_result: Optional[Dict],
        sentiment_result: Optional[Dict],
        knowledge_results: List[Dict],
        customer_info: Optional[Dict]
    ) -> Dict:
        """构建增强的对话上下文"""
        
        enhanced_context = {
            'system_prompt': self.system_prompt,
            'personality': self.personality,
            'current_message': message,
            'conversation_history': conversation_context.get('conversation_history', []),
            'customer_info': customer_info or {},
        }
        
        # 添加意图信息
        if intent_result:
            enhanced_context['current_intent'] = intent_result.get('intent')
            enhanced_context['entities'] = intent_result.get('entities', {})
        
        # 添加情感信息
        if sentiment_result:
            enhanced_context['customer_sentiment'] = sentiment_result.get('sentiment')
            enhanced_context['sentiment_score'] = sentiment_result.get('score', 0.0)
        
        # 添加知识库信息
        if knowledge_results:
            enhanced_context['relevant_knowledge'] = knowledge_results[:5]  # 只取前5条最相关的
        
        # 添加商品上下文
        if conversation_context.get('product_context'):
            enhanced_context['product_context'] = conversation_context['product_context']
        
        return enhanced_context
    
    def _should_handover_to_human(
        self,
        intent_result: Optional[Dict],
        sentiment_result: Optional[Dict],
        confidence: float,
        conversation_context: Dict
    ) -> bool:
        """判断是否需要转接人工客服"""
        
        # 1. 置信度过低
        if confidence < self.confidence_threshold:
            logger.info(f"置信度过低 ({confidence:.2f}), 建议转接人工")
            return True
        
        # 2. 负面情感过强
        if sentiment_result:
            sentiment = sentiment_result.get('sentiment')
            score = sentiment_result.get('score', 0.0)
            if sentiment == 'negative' and score < -0.7:
                logger.info(f"客户情感过于负面 ({score:.2f}), 建议转接人工")
                return True
        
        # 3. 特定意图需要人工处理
        if intent_result:
            intent = intent_result.get('intent')
            human_required_intents = ['complaint', 'return_refund', 'technical_support']
            if intent in human_required_intents:
                logger.info(f"意图 {intent} 需要人工处理")
                return True
        
        # 4. 连续无法解决问题
        failed_attempts = conversation_context.get('failed_attempts', 0)
        if failed_attempts >= 3:
            logger.info(f"连续 {failed_attempts} 次无法解决问题, 建议转接人工")
            return True
        
        return False
    
    async def update_knowledge_base(self, knowledge_base_id: str) -> bool:
        """更新知识库"""
        try:
            return await self.knowledge_engine.update_knowledge_base(knowledge_base_id)
        except Exception as e:
            logger.error(f"更新知识库失败: {str(e)}")
            return False
    
    def get_performance_metrics(self) -> Dict:
        """获取代理性能指标"""
        return {
            'model_provider': self.model_provider.provider_name,
            'model_name': self.model_provider.model_name,
            'knowledge_bases_count': len(self.knowledge_engine.knowledge_bases),
            'confidence_threshold': self.confidence_threshold,
            'features_enabled': {
                'knowledge_search': self.enable_knowledge_search,
                'intent_recognition': self.enable_intent_recognition,
                'sentiment_analysis': self.enable_sentiment_analysis,
            }
        }


class AgentManager:
    """AI代理管理器"""
    
    def __init__(self):
        self.agents: Dict[str, SmartTalkAgent] = {}
        logger.info("AI代理管理器初始化完成")
    
    def create_agent(self, agent_config: Dict) -> SmartTalkAgent:
        """创建AI代理"""
        agent_id = agent_config.get('id')
        if not agent_id:
            raise ValueError("代理配置必须包含ID")
        
        agent = SmartTalkAgent(agent_config)
        self.agents[agent_id] = agent
        
        logger.info(f"创建AI代理: {agent_id}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[SmartTalkAgent]:
        """获取AI代理"""
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """移除AI代理"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"移除AI代理: {agent_id}")
            return True
        return False
    
    def list_agents(self) -> List[str]:
        """列出所有代理ID"""
        return list(self.agents.keys())
    
    def get_agent_metrics(self, agent_id: str) -> Optional[Dict]:
        """获取代理性能指标"""
        agent = self.get_agent(agent_id)
        if agent:
            return agent.get_performance_metrics()
        return None


# 全局代理管理器实例
agent_manager = AgentManager() 