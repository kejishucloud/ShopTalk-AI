"""
知识智能体提示词管理
包含知识检索、回答生成和知识分类相关的提示词
"""

from typing import List, Dict, Any
from .base_prompts import BasePrompts


class KnowledgePrompts(BasePrompts):
    """知识智能体提示词类"""
    
    def __init__(self):
        super().__init__()
        self.answer_templates = self._init_answer_templates()
        self.fallback_responses = self._init_fallback_responses()
        self.suggestion_templates = self._init_suggestion_templates()
    
    def _init_answer_templates(self) -> Dict[str, str]:
        """初始化回答模板"""
        return {
            'faq': "根据常见问题解答：{content}",
            'product': "关于该产品：{content}",
            'policy': "根据相关政策：{content}",
            'general': "{content}"
        }
    
    def _init_fallback_responses(self) -> Dict[str, List[str]]:
        """初始化备用回答"""
        return {
            'polite': [
                "抱歉，我暂时没有找到相关信息。您可以尝试换个问法，或者联系人工客服获得更详细的帮助。",
                "很抱歉，关于这个问题我需要更多时间来查询准确信息。建议您稍后再试，或联系专业客服。"
            ],
            'direct': [
                "暂时没有找到相关信息。",
                "这个问题超出了我目前的知识范围。建议您咨询我们的专业客服人员。"
            ],
            'helpful': [
                "关于您的问题，我需要了解更多信息才能给出准确回答。请问您能提供更多详细信息吗？",
                "我正在努力为您查找相关信息。同时，您可以尝试描述得更具体一些，这样我能提供更精准的帮助。"
            ]
        }
    
    def _init_suggestion_templates(self) -> Dict[str, List[str]]:
        """初始化建议模板"""
        return {
            'product_related': [
                "您可以查看产品详情页面了解更多信息",
                "建议您关注产品的用户评价和使用体验"
            ],
            'faq_related': [
                "如有其他疑问，可查看完整的常见问题列表",
                "您也可以搜索相关关键词获取更多帮助"
            ],
            'purchase_related': [
                "关注我们的优惠活动可获得更好价格",
                "如需下单，我可以为您提供购买指导"
            ]
        }
    
    def get_answer_template(self, knowledge_type: str) -> str:
        """获取回答模板"""
        return self.answer_templates.get(knowledge_type, self.answer_templates['general'])
    
    def get_fallback_response(self, user_type: str = 'helpful') -> str:
        """获取备用回答"""
        responses = self.fallback_responses.get(user_type, self.fallback_responses['helpful'])
        return self.get_random_prompt(responses)
    
    def get_suggestions(self, context_type: str) -> List[str]:
        """获取建议列表"""
        return self.suggestion_templates.get(context_type, []) 