"""
聊天智能体
基于Langflow集成多个智能体，提供统一的对话接口
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base_agent import BaseAgent, agent_manager

# 尝试导入Langflow相关库
try:
    from langflow import LangflowClient
    LANGFLOW_AVAILABLE = True
except ImportError:
    LANGFLOW_AVAILABLE = False
    logging.warning("Langflow not available, using fallback implementation")

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available")


class ChatAgent(BaseAgent):
    """聊天智能体 - 整合所有智能体能力"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("chat_agent", config)
        
        # Langflow配置
        self.langflow_config = config.get('langflow', {})
        self.langflow_endpoint = self.langflow_config.get('endpoint', 'http://localhost:7860')
        self.langflow_api_key = self.langflow_config.get('api_key', '')
        self.flow_id = self.langflow_config.get('flow_id', '')
        
        # LLM配置
        self.llm_config = config.get('llm', {})
        self.model_name = self.llm_config.get('model', 'gpt-3.5-turbo')
        self.temperature = self.llm_config.get('temperature', 0.7)
        self.max_tokens = self.llm_config.get('max_tokens', 1000)
        
        # 初始化Langflow客户端
        if LANGFLOW_AVAILABLE and self.langflow_api_key:
            try:
                self.langflow_client = LangflowClient(
                    base_url=self.langflow_endpoint,
                    api_key=self.langflow_api_key
                )
                self.logger.info("Langflow client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Langflow client: {e}")
                self.langflow_client = None
        else:
            self.langflow_client = None
        
        # 初始化LLM
        if LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatOpenAI(
                    model_name=self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize LLM: {e}")
                self.llm = None
        else:
            self.llm = None
        
        # 对话流程配置
        self.conversation_flow = {
            'greeting': {
                'next_states': ['information_gathering', 'product_inquiry'],
                'agents': ['tag_agent', 'sentiment_agent', 'memory_agent'],
                'prompts': self._get_greeting_prompts()
            },
            'information_gathering': {
                'next_states': ['product_recommendation', 'knowledge_query'],
                'agents': ['tag_agent', 'sentiment_agent', 'memory_agent'],
                'prompts': self._get_info_gathering_prompts()
            },
            'product_inquiry': {
                'next_states': ['product_recommendation', 'price_negotiation'],
                'agents': ['knowledge_agent', 'tag_agent', 'sentiment_agent'],
                'prompts': self._get_product_inquiry_prompts()
            },
            'product_recommendation': {
                'next_states': ['price_negotiation', 'order_processing'],
                'agents': ['knowledge_agent', 'tag_agent'],
                'prompts': self._get_recommendation_prompts()
            },
            'price_negotiation': {
                'next_states': ['order_processing', 'product_recommendation'],
                'agents': ['sentiment_agent', 'tag_agent'],
                'prompts': self._get_negotiation_prompts()
            },
            'order_processing': {
                'next_states': ['after_sales', 'closing'],
                'agents': ['memory_agent', 'sentiment_agent'],
                'prompts': self._get_order_prompts()
            },
            'after_sales': {
                'next_states': ['closing', 'knowledge_query'],
                'agents': ['knowledge_agent', 'sentiment_agent'],
                'prompts': self._get_after_sales_prompts()
            },
            'closing': {
                'next_states': ['greeting'],
                'agents': ['sentiment_agent', 'memory_agent'],
                'prompts': self._get_closing_prompts()
            }
        }
        
        # 智能体优先级
        self.agent_priority = {
            'sentiment_agent': 1,  # 情感分析最高优先级
            'memory_agent': 2,     # 记忆管理次之
            'tag_agent': 3,        # 标签分析
            'knowledge_agent': 4   # 知识检索
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['user_id', 'message']
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话消息"""
        user_id = input_data['user_id']
        message = input_data['message']
        session_id = input_data.get('session_id', 'default')
        context = input_data.get('context', {})
        
        # 1. 并行调用智能体分析
        agent_results = await self._analyze_with_agents(input_data)
        
        # 2. 确定对话状态
        conversation_state = self._determine_conversation_state(agent_results, context)
        
        # 3. 生成回复
        if self.langflow_client:
            response = await self._generate_response_with_langflow(
                message, agent_results, conversation_state, context
            )
        else:
            response = await self._generate_response_fallback(
                message, agent_results, conversation_state, context
            )
        
        # 4. 更新对话历史
        await self._update_conversation_history(user_id, session_id, message, response, agent_results)
        
        # 5. 预测下一步动作
        next_actions = self._predict_next_actions(conversation_state, agent_results)
        
        result = {
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'response': response,
            'conversation_state': conversation_state,
            'agent_results': agent_results,
            'next_actions': next_actions,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Chat processed for user {user_id}: {conversation_state}")
        
        return result
    
    async def _analyze_with_agents(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """并行调用多个智能体进行分析"""
        agent_tasks = []
        agent_names = []
        
        # 根据优先级创建任务
        for agent_name in sorted(self.agent_priority.keys(), key=lambda x: self.agent_priority[x]):
            if agent_manager.get_agent(agent_name):
                agent_tasks.append(agent_manager.process_with_agent(agent_name, input_data))
                agent_names.append(agent_name)
        
        # 并行执行
        try:
            results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"Error in agent analysis: {e}")
            results = [{'success': False, 'error': str(e)} for _ in agent_tasks]
        
        # 整理结果
        agent_results = {}
        for i, (agent_name, result) in enumerate(zip(agent_names, results)):
            if isinstance(result, Exception):
                agent_results[agent_name] = {'success': False, 'error': str(result)}
            else:
                agent_results[agent_name] = result
        
        return agent_results
    
    def _determine_conversation_state(self, agent_results: Dict[str, Any], context: Dict[str, Any]) -> str:
        """根据智能体分析结果确定对话状态"""
        # 从记忆智能体获取当前状态
        memory_result = agent_results.get('memory_agent', {})
        if memory_result.get('success') and memory_result.get('data'):
            current_state = memory_result['data'].get('conversation_state', 'greeting')
        else:
            current_state = context.get('conversation_state', 'greeting')
        
        # 根据标签智能体结果调整状态
        tag_result = agent_results.get('tag_agent', {})
        if tag_result.get('success') and tag_result.get('data'):
            tags = tag_result['data'].get('tags', [])
            
            # 购买意向高 -> 产品推荐
            if 'high_intent' in tags:
                return 'product_recommendation'
            # 价格敏感 -> 价格协商
            elif 'price_sensitive' in tags and current_state in ['product_recommendation', 'product_inquiry']:
                return 'price_negotiation'
            # 投诉相关 -> 售后服务
            elif any(tag in tags for tag in ['complaint', 'disappointed']):
                return 'after_sales'
        
        # 根据情感分析调整状态
        sentiment_result = agent_results.get('sentiment_agent', {})
        if sentiment_result.get('success') and sentiment_result.get('data'):
            sentiment = sentiment_result['data'].get('sentiment', {})
            
            # 负面情感 -> 售后服务
            if sentiment.get('label') == 'negative' and sentiment.get('confidence', 0) > 0.7:
                return 'after_sales'
            # 积极情感且在推荐阶段 -> 订单处理
            elif sentiment.get('label') == 'positive' and current_state == 'product_recommendation':
                return 'order_processing'
        
        return current_state
    
    async def _generate_response_with_langflow(self, message: str, agent_results: Dict[str, Any],
                                             conversation_state: str, context: Dict[str, Any]) -> str:
        """使用Langflow生成回复"""
        try:
            # 构建Langflow输入
            flow_input = {
                'user_message': message,
                'conversation_state': conversation_state,
                'agent_results': json.dumps(agent_results, ensure_ascii=False),
                'context': json.dumps(context, ensure_ascii=False)
            }
            
            # 调用Langflow流程
            response = await self.langflow_client.run_flow(
                flow_id=self.flow_id,
                input_data=flow_input
            )
            
            if response and 'output' in response:
                return response['output']
            else:
                self.logger.warning("Invalid Langflow response, using fallback")
                return await self._generate_response_fallback(message, agent_results, conversation_state, context)
                
        except Exception as e:
            self.logger.error(f"Langflow generation error: {e}")
            return await self._generate_response_fallback(message, agent_results, conversation_state, context)
    
    async def _generate_response_fallback(self, message: str, agent_results: Dict[str, Any],
                                        conversation_state: str, context: Dict[str, Any]) -> str:
        """备用回复生成方法"""
        # 构建系统提示词
        system_prompt = self._build_system_prompt(conversation_state, agent_results)
        
        # 构建用户消息上下文
        user_context = self._build_user_context(agent_results, context)
        
        if self.llm and LANGCHAIN_AVAILABLE:
            # 使用LangChain LLM生成回复
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"用户上下文：{user_context}\n用户消息：{message}")
                ]
                
                response = await self.llm.agenerate([messages])
                return response.generations[0][0].text.strip()
                
            except Exception as e:
                self.logger.error(f"LLM generation error: {e}")
        
        # 基于规则的备用回复
        return self._generate_rule_based_response(message, agent_results, conversation_state)
    
    def _build_system_prompt(self, conversation_state: str, agent_results: Dict[str, Any]) -> str:
        """构建系统提示词"""
        base_prompt = """你是一个专业的AI客服助手，具备以下能力：
1. 理解用户情感和意图
2. 记住对话历史和用户偏好
3. 提供准确的产品信息和建议
4. 根据用户特征调整沟通风格

当前对话阶段：{conversation_state}

智能体分析结果：
{agent_analysis}

请根据分析结果，以自然、友好的方式回复用户，确保回复：
- 符合当前对话阶段的目标
- 考虑用户的情感状态和偏好
- 利用相关的知识库信息
- 推进对话向积极方向发展"""
        
        # 整理智能体分析结果
        agent_analysis = []
        
        # 情感分析
        sentiment_result = agent_results.get('sentiment_agent', {})
        if sentiment_result.get('success'):
            sentiment_data = sentiment_result.get('data', {}).get('sentiment', {})
            agent_analysis.append(f"情感状态：{sentiment_data.get('label', '未知')} (置信度: {sentiment_data.get('confidence', 0):.2f})")
        
        # 用户标签
        tag_result = agent_results.get('tag_agent', {})
        if tag_result.get('success'):
            tags = tag_result.get('data', {}).get('tags', [])
            if tags:
                agent_analysis.append(f"用户标签：{', '.join(tags)}")
        
        # 知识库结果
        knowledge_result = agent_results.get('knowledge_agent', {})
        if knowledge_result.get('success'):
            answer = knowledge_result.get('data', {}).get('answer', '')
            if answer:
                agent_analysis.append(f"知识库回答：{answer[:200]}...")
        
        return base_prompt.format(
            conversation_state=conversation_state,
            agent_analysis='\n'.join(agent_analysis) if agent_analysis else '暂无分析结果'
        )
    
    def _build_user_context(self, agent_results: Dict[str, Any], context: Dict[str, Any]) -> str:
        """构建用户上下文信息"""
        context_parts = []
        
        # 用户画像
        memory_result = agent_results.get('memory_agent', {})
        if memory_result.get('success'):
            memory_data = memory_result.get('data', {})
            user_profile = memory_data.get('context', {}).get('user_profile', {})
            if user_profile:
                context_parts.append(f"用户画像：{json.dumps(user_profile, ensure_ascii=False)}")
        
        # 会话历史
        recent_messages = context.get('recent_messages', [])
        if recent_messages:
            history = [f"{msg.get('type', 'user')}: {msg.get('message', '')}" for msg in recent_messages[-3:]]
            context_parts.append(f"最近对话：{'; '.join(history)}")
        
        return '\n'.join(context_parts) if context_parts else '无历史上下文'
    
    def _generate_rule_based_response(self, message: str, agent_results: Dict[str, Any], 
                                    conversation_state: str) -> str:
        """基于规则的回复生成"""
        # 获取预定义提示词
        state_prompts = self.conversation_flow.get(conversation_state, {}).get('prompts', [])
        
        # 根据情感选择合适的回复基调
        sentiment_result = agent_results.get('sentiment_agent', {})
        sentiment_label = 'neutral'
        if sentiment_result.get('success'):
            sentiment_label = sentiment_result.get('data', {}).get('sentiment', {}).get('label', 'neutral')
        
        # 根据用户标签调整回复风格
        tag_result = agent_results.get('tag_agent', {})
        user_tags = []
        if tag_result.get('success'):
            user_tags = tag_result.get('data', {}).get('tags', [])
        
        # 选择合适的回复模板
        if sentiment_label == 'negative':
            response = "我理解您的担忧，让我为您详细解答。"
        elif sentiment_label == 'positive':
            response = "很高兴您对我们的服务满意！"
        else:
            response = "我来为您详细介绍一下。"
        
        # 添加知识库信息
        knowledge_result = agent_results.get('knowledge_agent', {})
        if knowledge_result.get('success'):
            knowledge_answer = knowledge_result.get('data', {}).get('answer', '')
            if knowledge_answer:
                response += f"\n\n{knowledge_answer}"
        
        # 根据对话状态添加引导
        if conversation_state == 'product_inquiry':
            response += "\n\n您还想了解其他产品信息吗？"
        elif conversation_state == 'product_recommendation':
            if 'high_intent' in user_tags:
                response += "\n\n这款产品很适合您，需要我为您介绍购买流程吗？"
            else:
                response += "\n\n您觉得这个产品怎么样？还有什么疑问吗？"
        
        return response
    
    async def _update_conversation_history(self, user_id: str, session_id: str, 
                                         user_message: str, assistant_response: str,
                                         agent_results: Dict[str, Any]):
        """更新对话历史"""
        # 更新记忆智能体
        try:
            memory_input = {
                'user_id': user_id,
                'session_id': session_id,
                'message': assistant_response,
                'message_type': 'assistant',
                'metadata': {
                    'agent_results': agent_results,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            await agent_manager.process_with_agent('memory_agent', memory_input)
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation history: {e}")
    
    def _predict_next_actions(self, conversation_state: str, agent_results: Dict[str, Any]) -> List[str]:
        """预测下一步可能的动作"""
        flow_config = self.conversation_flow.get(conversation_state, {})
        possible_states = flow_config.get('next_states', [])
        
        # 根据智能体分析结果调整概率
        actions = []
        
        tag_result = agent_results.get('tag_agent', {})
        if tag_result.get('success'):
            tags = tag_result.get('data', {}).get('tags', [])
            
            if 'high_intent' in tags and 'order_processing' in possible_states:
                actions.append('order_processing')
            elif 'price_sensitive' in tags and 'price_negotiation' in possible_states:
                actions.append('price_negotiation')
        
        sentiment_result = agent_results.get('sentiment_agent', {})
        if sentiment_result.get('success'):
            sentiment = sentiment_result.get('data', {}).get('sentiment', {})
            
            if sentiment.get('label') == 'negative' and 'after_sales' in possible_states:
                actions.append('after_sales')
        
        # 添加默认可能状态
        actions.extend([state for state in possible_states if state not in actions])
        
        return actions
    
    def _get_greeting_prompts(self) -> List[str]:
        """获取问候阶段提示词"""
        return [
            "欢迎光临！我是您的专属购物助手，有什么可以帮您的吗？",
            "您好！很高兴为您服务，请问您今天想了解什么产品呢？",
            "欢迎！我可以为您提供产品咨询、下单协助等服务，请告诉我您的需求。"
        ]
    
    def _get_info_gathering_prompts(self) -> List[str]:
        """获取信息收集阶段提示词"""
        return [
            "为了更好地为您推荐，请告诉我您的具体需求或偏好。",
            "您能详细描述一下您想要的产品特点吗？",
            "请问您有什么特殊要求或预算范围吗？"
        ]
    
    def _get_product_inquiry_prompts(self) -> List[str]:
        """获取产品咨询阶段提示词"""
        return [
            "这款产品的详细信息如下：",
            "根据您的需求，我为您推荐这款产品：",
            "关于这个产品，我来为您详细介绍："
        ]
    
    def _get_recommendation_prompts(self) -> List[str]:
        """获取推荐阶段提示词"""
        return [
            "基于您的偏好，我推荐以下产品：",
            "这几款产品很适合您：",
            "根据您的需求，建议您考虑："
        ]
    
    def _get_negotiation_prompts(self) -> List[str]:
        """获取价格协商阶段提示词"""
        return [
            "关于价格，我们有以下优惠：",
            "让我为您查询最新的促销活动：",
            "我理解您对价格的关注，我们可以这样："
        ]
    
    def _get_order_prompts(self) -> List[str]:
        """获取订单处理阶段提示词"""
        return [
            "好的，我来为您办理购买手续：",
            "请确认您的订单信息：",
            "我们开始下单流程："
        ]
    
    def _get_after_sales_prompts(self) -> List[str]:
        """获取售后服务阶段提示词"""
        return [
            "我来帮您解决这个问题：",
            "关于您的问题，处理方案如下：",
            "请不要担心，我们会妥善处理："
        ]
    
    def _get_closing_prompts(self) -> List[str]:
        """获取结束阶段提示词"""
        return [
            "感谢您的咨询，祝您购物愉快！",
            "如有其他问题，随时联系我们！",
            "谢谢您的信任，期待下次为您服务！"
        ] 