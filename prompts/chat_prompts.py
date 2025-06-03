"""
聊天智能体提示词管理
包含对话各阶段的提示词模板和系统提示词
"""

from typing import List, Dict, Any
from .base_prompts import BasePrompts


class ChatPrompts(BasePrompts):
    """聊天智能体提示词类"""
    
    def __init__(self):
        super().__init__()
        self.conversation_prompts = self._init_conversation_prompts()
        self.system_prompts = self._init_system_prompts()
        self.response_templates = self._init_response_templates()
    
    def _init_conversation_prompts(self) -> Dict[str, List[str]]:
        """初始化各对话阶段的提示词"""
        return {
            'greeting': self._get_greeting_prompts(),
            'information_gathering': self._get_info_gathering_prompts(),
            'product_inquiry': self._get_product_inquiry_prompts(),  
            'product_recommendation': self._get_recommendation_prompts(),
            'price_negotiation': self._get_negotiation_prompts(),
            'order_processing': self._get_order_prompts(),
            'after_sales': self._get_after_sales_prompts(),
            'closing': self._get_closing_prompts()
        }
    
    def _init_system_prompts(self) -> Dict[str, str]:
        """初始化系统提示词"""
        return {
            'base_system': self._get_base_system_prompt(),
            'greeting_system': self._get_greeting_system_prompt(),
            'sales_system': self._get_sales_system_prompt(),
            'service_system': self._get_service_system_prompt()
        }
    
    def _init_response_templates(self) -> Dict[str, Dict[str, str]]:
        """初始化回复模板"""
        return {
            'sentiment_based': {
                'positive': "很高兴您对我们的服务满意！{content}",
                'negative': "我理解您的担忧，让我为您详细解答。{content}",
                'neutral': "我来为您详细介绍一下。{content}"
            },
            'user_type_based': {
                'high_intent': "这款产品很适合您，{content}需要我为您介绍购买流程吗？",
                'price_sensitive': "关于价格，我们有优惠活动，{content}让我为您查询最新优惠。",
                'information_seeker': "让我为您详细介绍，{content}您还想了解哪些方面？"
            }
        }
    
    def get_conversation_prompts(self, state: str) -> List[str]:
        """获取指定对话状态的提示词"""
        return self.conversation_prompts.get(state, [])
    
    def get_system_prompt(self, prompt_type: str = 'base_system') -> str:
        """获取系统提示词"""
        return self.system_prompts.get(prompt_type, self.system_prompts['base_system'])
    
    def get_response_template(self, template_type: str, template_key: str) -> str:
        """获取回复模板"""
        return self.response_templates.get(template_type, {}).get(template_key, "{content}")
    
    def build_system_prompt(self, conversation_state: str, agent_analysis: str) -> str:
        """构建完整的系统提示词"""
        base_prompt = """你是一个专业的AI客服助手，具备以下能力：

1. 商品咨询和推荐
2. 价格协商和优惠信息
3. 订单处理和售后服务
4. 用户情感理解和回应

当前对话状态：{conversation_state}

智能体分析结果：
{agent_analysis}

请根据上述信息，以专业、友好的态度回复用户。保持回复简洁明了，并引导对话朝着有利的方向发展。"""
        
        return base_prompt.format(
            conversation_state=conversation_state,
            agent_analysis=agent_analysis
        )
    
    def _get_base_system_prompt(self) -> str:
        """基础系统提示词"""
        return """你是一个专业的AI购物助手，具备以下核心能力：
- 产品咨询和推荐
- 价格协商和优惠查询  
- 订单处理和购买指导
- 售后服务和问题解决
- 用户情感理解和个性化回应

请始终保持友好、专业的服务态度，准确理解用户需求，提供有价值的建议。"""
    
    def _get_greeting_system_prompt(self) -> str:
        """问候阶段系统提示词"""
        return """作为专业的购物助手，请主动了解用户需求：
- 热情欢迎用户
- 快速识别用户意图
- 引导用户表达具体需求
- 为后续服务做好准备"""
    
    def _get_sales_system_prompt(self) -> str:
        """销售阶段系统提示词"""  
        return """作为销售顾问，请注重：
- 准确理解产品需求
- 提供个性化推荐
- 突出产品价值和优势
- 适时引导购买决策"""
    
    def _get_service_system_prompt(self) -> str:
        """服务阶段系统提示词"""
        return """作为客服代表，请专注于：
- 快速定位问题
- 提供有效解决方案
- 保持耐心和同理心
- 确保客户满意度"""
    
    def _get_greeting_prompts(self) -> List[str]:
        """问候阶段提示词"""
        return [
            "欢迎光临！我是您的专属购物助手，有什么可以帮您的吗？",
            "您好！很高兴为您服务，请问您今天想了解什么产品呢？",
            "欢迎！我可以为您提供产品咨询、下单协助等服务，请告诉我您的需求。",
            "您好！我是智能购物助手，可以帮您挑选产品、比较价格、处理订单，有什么需要吗？"
        ]
    
    def _get_info_gathering_prompts(self) -> List[str]:
        """信息收集阶段提示词"""
        return [
            "为了更好地为您推荐，请告诉我您的具体需求或偏好。",
            "您能详细描述一下您想要的产品特点吗？",
            "请问您有什么特殊要求或预算范围吗？",
            "了解您的使用场景有助于我推荐合适的产品，能简单介绍一下吗？",
            "为了给您最佳建议，请告诉我您最看重产品的哪些方面？"
        ]
    
    def _get_product_inquiry_prompts(self) -> List[str]:
        """产品咨询阶段提示词"""
        return [
            "这款产品的详细信息如下：",
            "根据您的需求，我为您推荐这款产品：",
            "关于这个产品，我来为您详细介绍：",
            "让我为您介绍这款产品的主要特点：",
            "这款产品非常适合您的需求，具体优势包括："
        ]
    
    def _get_recommendation_prompts(self) -> List[str]:
        """推荐阶段提示词"""
        return [
            "基于您的偏好，我推荐以下产品：",
            "这几款产品很适合您：",
            "根据您的需求，建议您考虑：",
            "综合您的要求，以下产品值得关注：",
            "为您精选了几款高性价比产品："
        ]
    
    def _get_negotiation_prompts(self) -> List[str]:
        """价格协商阶段提示词"""
        return [
            "关于价格，我们有以下优惠：",
            "让我为您查询最新的促销活动：",
            "我理解您对价格的关注，我们可以这样：",
            "目前有专属优惠可以为您申请：",
            "价格方面我来帮您争取最大优惠："
        ]
    
    def _get_order_prompts(self) -> List[str]:
        """订单处理阶段提示词"""
        return [
            "好的，我来为您办理购买手续：",
            "请确认您的订单信息：", 
            "我们开始下单流程：",
            "让我为您核对订单详情：",
            "现在为您处理订单，请稍候："
        ]
    
    def _get_after_sales_prompts(self) -> List[str]:
        """售后服务阶段提示词"""
        return [
            "我来帮您解决这个问题：",
            "关于您的问题，处理方案如下：",
            "请不要担心，我们会妥善处理：",
            "让我为您查看具体情况：",
            "我理解您的困扰，我们立即处理："
        ]
    
    def _get_closing_prompts(self) -> List[str]:
        """结束阶段提示词"""
        return [
            "感谢您的咨询，祝您购物愉快！",
            "如有其他问题，随时联系我们！",
            "谢谢您的信任，期待下次为您服务！",
            "购物愉快！有任何问题都可以随时找我。",
            "感谢选择我们，祝您使用愉快！"
        ] 