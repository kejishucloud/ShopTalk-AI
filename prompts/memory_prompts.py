"""
记忆智能体提示词管理
包含记忆存储、用户画像和个性化相关的提示词
"""

from typing import List, Dict, Any
from .base_prompts import BasePrompts


class MemoryPrompts(BasePrompts):
    """记忆智能体提示词类"""
    
    def __init__(self):
        super().__init__()
        self.profile_templates = self._init_profile_templates()
        self.memory_categories = self._init_memory_categories()
        self.personalization_prompts = self._init_personalization_prompts()
    
    def _init_profile_templates(self) -> Dict[str, str]:
        """初始化用户画像模板"""
        return {
            'greeting_new': "欢迎新用户！我会记住您的偏好，为您提供更好的服务。",
            'greeting_returning': "欢迎回来！根据我们之前的交流，我记得您{preferences}。",
            'preference_updated': "好的，我已经记录了您的偏好：{preference}",
            'summary_intro': "根据我对您的了解：{user_summary}",
            'recommendation_based': "基于您之前的{behavior}，我推荐：{recommendation}"
        }
    
    def _init_memory_categories(self) -> Dict[str, List[str]]:
        """初始化记忆分类"""
        return {
            'preferences': [
                "产品偏好", "价格敏感度", "品牌倾向", "功能需求",
                "颜色喜好", "尺寸要求", "使用场景", "购买频率"
            ],
            'behaviors': [
                "浏览历史", "购买记录", "咨询历史", "互动频率",
                "反馈记录", "投诉历史", "推荐接受度", "决策时间"
            ],
            'personal_info': [
                "年龄范围", "性别", "地域", "职业",
                "兴趣爱好", "生活方式", "家庭状况", "收入水平"
            ],
            'communication_style': [
                "沟通偏好", "回复风格", "详细程度偏好", "语言习惯",
                "提问方式", "反馈风格", "表达习惯", "互动频率"
            ]
        }
    
    def _init_personalization_prompts(self) -> Dict[str, Dict[str, List[str]]]:
        """初始化个性化提示词"""
        return {
            'user_types': {
                'decisive': [
                    "您决策果断，我直接为您推荐最优选择：",
                    "基于您的快速决策风格，建议您考虑：",
                    "为了节省您的时间，我推荐："
                ],
                'analytical': [
                    "我知道您注重详细分析，让我为您详细对比：",
                    "根据您喜欢深入了解的特点，详细信息如下：",
                    "考虑到您的分析型决策风格，我提供完整对比："
                ],
                'price_sensitive': [
                    "考虑到您对价格的关注，我为您找到了优惠：",
                    "您关注性价比，这些选择很适合：",
                    "根据您的价格敏感度，推荐以下划算选择："
                ],
                'quality_focused': [
                    "您注重品质，这些高质量产品值得考虑：",
                    "基于您对品质的追求，推荐：",
                    "考虑到您的品质要求，这些产品符合标准："
                ]
            },
            'interaction_history': {
                'frequent_user': [
                    "作为我们的老朋友，",
                    "根据我们的多次交流，",
                    "基于您一直以来的信任，"
                ],
                'occasional_user': [
                    "很高兴再次为您服务，",
                    "欢迎回来，",
                    "根据我们之前的交流，"
                ],
                'new_user': [
                    "欢迎初次使用我们的服务，",
                    "作为新用户，",
                    "我很高兴认识您，"
                ]
            }
        }
    
    def get_personalized_greeting(self, user_profile: Dict[str, Any]) -> str:
        """获取个性化问候语"""
        interaction_count = user_profile.get('interaction_count', 0)
        preferences = user_profile.get('preferences', {})
        
        if interaction_count == 0:
            return self.profile_templates['greeting_new']
        else:
            pref_text = self._format_preferences(preferences)
            return self.format_prompt(
                self.profile_templates['greeting_returning'],
                preferences=pref_text
            )
    
    def get_personalized_response_prefix(self, user_type: str) -> str:
        """获取个性化回应前缀"""
        user_prompts = self.personalization_prompts['user_types'].get(user_type, [])
        if user_prompts:
            return self.get_random_prompt(user_prompts)
        return ""
    
    def get_interaction_history_prefix(self, user_profile: Dict[str, Any]) -> str:
        """获取交互历史前缀"""
        interaction_count = user_profile.get('interaction_count', 0)
        
        if interaction_count > 10:
            user_type = 'frequent_user'
        elif interaction_count > 0:
            user_type = 'occasional_user'
        else:
            user_type = 'new_user'
        
        prompts = self.personalization_prompts['interaction_history'].get(user_type, [])
        return self.get_random_prompt(prompts)
    
    def format_user_summary(self, user_profile: Dict[str, Any]) -> str:
        """格式化用户总结"""
        summary_parts = []
        
        # 偏好总结
        preferences = user_profile.get('preferences', {})
        if preferences:
            pref_summary = self._format_preferences(preferences)
            summary_parts.append(f"偏好：{pref_summary}")
        
        # 行为总结
        behavior_data = user_profile.get('behavior_data', {})
        if behavior_data:
            behavior_summary = self._format_behaviors(behavior_data)
            summary_parts.append(f"行为特点：{behavior_summary}")
        
        # 交互历史
        interaction_count = user_profile.get('interaction_count', 0)
        if interaction_count > 0:
            summary_parts.append(f"交互{interaction_count}次")
        
        return "；".join(summary_parts) if summary_parts else "暂无详细信息"
    
    def _format_preferences(self, preferences: Dict[str, Any]) -> str:
        """格式化偏好信息"""
        pref_items = []
        
        # 产品偏好
        if 'product_types' in preferences:
            types = preferences['product_types']
            if types:
                pref_items.append(f"喜欢{', '.join(types[:2])}")
        
        # 价格偏好
        if 'price_range' in preferences:
            price_range = preferences['price_range']
            pref_items.append(f"预算{price_range}")
        
        # 品牌偏好
        if 'preferred_brands' in preferences:
            brands = preferences['preferred_brands']
            if brands:
                pref_items.append(f"偏爱{', '.join(brands[:2])}")
        
        return "，".join(pref_items) if pref_items else "偏好待了解"
    
    def _format_behaviors(self, behavior_data: Dict[str, Any]) -> str:
        """格式化行为信息"""
        behavior_items = []
        
        # 决策风格
        decision_style = behavior_data.get('decision_style')
        if decision_style:
            behavior_items.append(f"{decision_style}型决策")
        
        # 购买频率
        purchase_frequency = behavior_data.get('purchase_frequency')
        if purchase_frequency:
            behavior_items.append(f"{purchase_frequency}购买")
        
        # 咨询习惯
        inquiry_style = behavior_data.get('inquiry_style')
        if inquiry_style:
            behavior_items.append(f"{inquiry_style}咨询")
        
        return "，".join(behavior_items) if behavior_items else "行为模式分析中"
    
    def get_memory_update_prompts(self) -> Dict[str, str]:
        """获取记忆更新提示词"""
        return {
            'preference_learned': "我记住了您的偏好：{preference}",
            'behavior_noted': "注意到您的行为特点：{behavior}",
            'profile_updated': "已更新您的个人资料",
            'memory_consolidated': "整理了我们的对话记录"
        }
    
    def get_recommendation_explanations(self) -> Dict[str, str]:
        """获取推荐解释模板"""
        return {
            'based_on_preference': "基于您偏好{preference}，推荐：{recommendation}",
            'based_on_history': "根据您的{history_type}，建议：{recommendation}",
            'based_on_similar_users': "类似用户都选择了：{recommendation}",
            'based_on_trends': "当前趋势显示：{recommendation}"
        } 