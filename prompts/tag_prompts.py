"""
标签智能体提示词管理
包含用户标签分析、分类和标签应用相关的提示词
"""

from typing import List, Dict, Any
from .base_prompts import BasePrompts


class TagPrompts(BasePrompts):
    """标签智能体提示词类"""
    
    def __init__(self):
        super().__init__()
        self.tag_definitions = self._init_tag_definitions()
        self.tag_application_prompts = self._init_tag_application_prompts()
        self.analysis_patterns = self._init_analysis_patterns()
    
    def _init_tag_definitions(self) -> Dict[str, Dict[str, Any]]:
        """初始化标签定义"""
        return {
            'intent_tags': {
                'high_intent': {
                    'description': '购买意向强烈',
                    'keywords': ['购买', '下单', '买', '要', '怎么付款', '多少钱', '有货吗'],
                    'patterns': ['想买', '要买', '准备买', '马上要', '现在就']
                },
                'browsing': {
                    'description': '浏览了解阶段',
                    'keywords': ['看看', '了解', '比较', '对比', '什么样', '怎么样'],
                    'patterns': ['想了解', '想看看', '想知道', '告诉我']
                },
                'comparison': {
                    'description': '产品对比阶段',
                    'keywords': ['对比', '比较', '区别', '哪个好', '推荐', '选择'],
                    'patterns': ['A和B', '哪个更', '还是', '对比一下']
                }
            },
            'behavior_tags': {
                'price_sensitive': {
                    'description': '价格敏感型用户',
                    'keywords': ['便宜', '优惠', '打折', '降价', '性价比', '划算'],
                    'patterns': ['多少钱', '价格', '贵不贵', '有优惠吗']
                },
                'quality_focused': {
                    'description': '品质优先型用户',
                    'keywords': ['质量', '品质', '好不好', '耐用', '可靠', '品牌'],
                    'patterns': ['质量怎么样', '好用吗', '耐用吗', '品质如何']
                },
                'feature_focused': {
                    'description': '功能导向型用户',
                    'keywords': ['功能', '特点', '参数', '配置', '性能', '规格'],
                    'patterns': ['有什么功能', '参数', '配置如何', '性能怎样']
                }
            },
            'communication_tags': {
                'direct': {
                    'description': '直接沟通风格',
                    'keywords': ['直接', '简单', '快点', '直说', '不要啰嗦'],
                    'patterns': ['直接说', '简单点', '快点告诉我']
                },
                'detailed': {
                    'description': '详细了解风格',
                    'keywords': ['详细', '具体', '更多', '全面', '详情'],
                    'patterns': ['详细介绍', '具体说说', '更多信息']
                },
                'polite': {
                    'description': '礼貌沟通风格',
                    'keywords': ['谢谢', '麻烦', '请', '不好意思', '打扰'],
                    'patterns': ['谢谢您', '麻烦您', '请问', '不好意思']
                }
            },
            'demographic_tags': {
                'tech_savvy': {
                    'description': '技术型用户',
                    'keywords': ['参数', '配置', '技术', '规格', 'CPU', 'GPU'],
                    'patterns': ['技术参数', '配置要求', '规格说明']
                },
                'beginner': {
                    'description': '新手用户',
                    'keywords': ['新手', '不懂', '不会', '简单', '容易'],
                    'patterns': ['我不懂', '不会用', '简单点', '容易吗']
                },
                'experienced': {
                    'description': '经验丰富用户',
                    'keywords': ['用过', '买过', '知道', '了解', '经验'],
                    'patterns': ['我用过', '之前买过', '我知道', '有经验']
                }
            }
        }
    
    def _init_tag_application_prompts(self) -> Dict[str, Dict[str, List[str]]]:
        """初始化标签应用提示词"""
        return {
            'high_intent': {
                'prompts': [
                    "看您很有购买意向，我来为您详细介绍购买流程：",
                    "既然您准备购买，让我为您推荐最合适的选择：",
                    "我来为您快速定位最符合需求的产品："
                ],
                'actions': ['recommend_products', 'show_purchase_process', 'offer_assistance']
            },
            'price_sensitive': {
                'prompts': [
                    "我理解您对价格的关注，让我为您查找最优惠的选择：",
                    "考虑到性价比，这些产品值得您关注：",
                    "我来为您找找有优惠活动的产品："
                ],
                'actions': ['show_discounts', 'compare_prices', 'suggest_alternatives']
            },
            'quality_focused': {
                'prompts': [
                    "我看您很注重品质，这些高质量产品推荐给您：",
                    "品质优先的话，建议您考虑这些选择：",
                    "为了确保品质，推荐您关注这些品牌："
                ],
                'actions': ['show_premium_products', 'highlight_quality', 'brand_recommendations']
            },
            'detailed': {
                'prompts': [
                    "我为您准备了详细的产品信息：",
                    "让我为您全面介绍产品的各个方面：",
                    "详细对比信息如下："
                ],
                'actions': ['provide_details', 'show_specifications', 'detailed_comparison']
            },
            'direct': {
                'prompts': [
                    "直接推荐：",
                    "简单来说：",
                    "推荐这款："
                ],
                'actions': ['quick_recommendation', 'simple_answer', 'direct_response']
            }
        }
    
    def _init_analysis_patterns(self) -> Dict[str, List[str]]:
        """初始化分析模式"""
        return {
            'urgency_indicators': [
                '急', '马上', '立即', '现在', '今天', '尽快',
                '着急', '赶时间', '快点', '紧急'
            ],
            'hesitation_indicators': [
                '但是', '不过', '可是', '只是', '就是', '担心',
                '犹豫', '考虑', '想想', '再看看', '不确定'
            ],
            'satisfaction_indicators': [
                '满意', '不错', '好', '喜欢', '合适', '可以',
                '行', 'OK', '没问题', '挺好'
            ],
            'dissatisfaction_indicators': [
                '不满意', '不好', '不行', '不合适', '不喜欢',
                '差', '不够', '有问题', '不满'
            ]
        }
    
    def analyze_user_tags(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析用户标签"""
        message_lower = message.lower()
        detected_tags = []
        tag_scores = {}
        
        # 遍历所有标签类别
        for category, tags in self.tag_definitions.items():
            for tag_name, tag_info in tags.items():
                score = self._calculate_tag_score(message_lower, tag_info)
                if score > 0:
                    detected_tags.append(tag_name)
                    tag_scores[tag_name] = score
        
        # 分析特殊模式
        urgency_score = self._check_patterns(message_lower, self.analysis_patterns['urgency_indicators'])
        hesitation_score = self._check_patterns(message_lower, self.analysis_patterns['hesitation_indicators'])
        
        return {
            'detected_tags': detected_tags,
            'tag_scores': tag_scores,
            'urgency_level': urgency_score,
            'hesitation_level': hesitation_score,
            'primary_tag': max(tag_scores.keys(), key=tag_scores.get) if tag_scores else None
        }
    
    def _calculate_tag_score(self, message: str, tag_info: Dict[str, Any]) -> float:
        """计算标签得分"""
        score = 0
        
        # 关键词匹配
        keywords = tag_info.get('keywords', [])
        for keyword in keywords:
            if keyword in message:
                score += 1
        
        # 模式匹配
        patterns = tag_info.get('patterns', [])
        for pattern in patterns:
            if pattern in message:
                score += 2  # 模式匹配权重更高
        
        # 归一化
        total_indicators = len(keywords) + len(patterns)
        return score / total_indicators if total_indicators > 0 else 0
    
    def _check_patterns(self, message: str, patterns: List[str]) -> float:
        """检查特定模式"""
        matches = sum(1 for pattern in patterns if pattern in message)
        return matches / len(patterns) if patterns else 0
    
    def get_tag_based_prompts(self, primary_tag: str) -> List[str]:
        """根据标签获取提示词"""
        tag_prompts = self.tag_application_prompts.get(primary_tag, {})
        return tag_prompts.get('prompts', [])
    
    def get_tag_based_actions(self, primary_tag: str) -> List[str]:
        """根据标签获取建议动作"""
        tag_prompts = self.tag_application_prompts.get(primary_tag, {})
        return tag_prompts.get('actions', [])
    
    def get_tag_description(self, tag_name: str) -> str:
        """获取标签描述"""
        for category, tags in self.tag_definitions.items():
            if tag_name in tags:
                return tags[tag_name].get('description', tag_name)
        return tag_name
    
    def suggest_conversation_strategy(self, user_tags: List[str]) -> Dict[str, Any]:
        """建议对话策略"""
        strategies = {
            'communication_style': 'neutral',
            'detail_level': 'medium',
            'urgency_handling': 'normal',
            'focus_areas': []
        }
        
        # 根据标签调整策略
        if 'direct' in user_tags:
            strategies['communication_style'] = 'direct'
            strategies['detail_level'] = 'low'
        elif 'detailed' in user_tags:
            strategies['detail_level'] = 'high'
        
        if 'price_sensitive' in user_tags:
            strategies['focus_areas'].append('pricing')
        if 'quality_focused' in user_tags:
            strategies['focus_areas'].append('quality')
        if 'feature_focused' in user_tags:
            strategies['focus_areas'].append('features')
        
        if 'high_intent' in user_tags:
            strategies['urgency_handling'] = 'high'
            strategies['focus_areas'].append('purchase_assistance')
        
        return strategies
    
    def format_tag_summary(self, user_tags: List[str]) -> str:
        """格式化标签总结"""
        if not user_tags:
            return "暂无明确标签"
        
        tag_descriptions = [self.get_tag_description(tag) for tag in user_tags[:3]]
        return "、".join(tag_descriptions) 