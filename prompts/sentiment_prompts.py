"""
情感智能体提示词管理
包含情感分析、情感回应和情感引导相关的提示词
"""

from typing import List, Dict, Any
from .base_prompts import BasePrompts


class SentimentPrompts(BasePrompts):
    """情感智能体提示词类"""
    
    def __init__(self):
        super().__init__()
        self.response_templates = self._init_response_templates()
        self.emotion_patterns = self._init_emotion_patterns()
        self.sentiment_indicators = self._init_sentiment_indicators()
    
    def _init_response_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """初始化情感回应模板"""
        return {
            'positive': {
                'high': [
                    "很高兴听到您的满意评价！",
                    "您的赞扬是我们前进的动力！",
                    "感谢您的认可，我们会继续努力！"
                ],
                'medium': [
                    "很高兴您对我们的服务满意！",
                    "您的满意是我们的目标！",
                    "感谢您的支持！"
                ],
                'low': [
                    "感谢您的反馈！",
                    "很高兴为您服务！"
                ]
            },
            'negative': {
                'high': [
                    "我深深理解您的不满，让我们立即为您解决这个问题。",
                    "非常抱歉给您带来了困扰，我会全力帮您处理。",
                    "我理解您的愤怒，请允许我为您提供解决方案。"
                ],
                'medium': [
                    "我理解您的担忧，让我为您详细解答。",
                    "抱歉让您感到不满，我来帮您解决。",
                    "我明白您的困惑，让我为您说明一下。"
                ],
                'low': [
                    "我理解您的疑虑，让我为您解释。",
                    "关于您的疑问，我来为您澄清。"
                ]
            },
            'neutral': {
                'default': [
                    "我来为您详细介绍一下。",
                    "让我为您提供相关信息。",
                    "关于您的问题，我为您解答。"
                ]
            }
        }
    
    def _init_emotion_patterns(self) -> Dict[str, List[str]]:
        """初始化情感模式识别词汇"""
        return {
            'angry': [
                "生气", "愤怒", "火大", "气死了", "烦死了", "太气人了",
                "受不了", "忍无可忍", "什么破", "垃圾", "坑爹"
            ],
            'happy': [
                "开心", "高兴", "快乐", "爽", "舒服", "满意", "不错",
                "太好了", "给力", "赞", "棒", "完美"
            ],
            'sad': [
                "难过", "伤心", "郁闷", "沮丧", "失落", "失望",
                "遗憾", "可惜", "无语", "心累"
            ],
            'surprised': [
                "惊讶", "震惊", "意外", "没想到", "想不到", "真的吗",
                "不会吧", "天哪", "我的天", "不敢相信"
            ],
            'worried': [
                "担心", "焦虑", "紧张", "不安", "忧虑", "害怕",
                "怕", "担忧", "不放心", "疑虑"
            ],
            'satisfied': [
                "满意", "舒心", "放心", "安心", "称心", "如意",
                "满足", "认可", "赞同", "同意"
            ],
            'disappointed': [
                "失望", "遗憾", "可惜", "无语", "郁闷", "不如意",
                "不满", "不爽", "别扭", "憋屈"
            ]
        }
    
    def _init_sentiment_indicators(self) -> Dict[str, List[str]]:
        """初始化情感指示词"""
        return {
            'intensity_high': [
                "非常", "特别", "超级", "极其", "超", "太", "真",
                "相当", "十分", "很是", "格外"
            ],
            'intensity_medium': [
                "很", "挺", "比较", "还", "稍微", "有点", "略"
            ],
            'negation': [
                "不", "没", "无", "非", "未", "否", "别", "莫",
                "不是", "没有", "不会", "不能"
            ],
            'positive_amplifiers': [
                "真的", "确实", "的确", "绝对", "肯定", "一定",
                "完全", "彻底", "十足", "百分百"
            ]
        }
    
    def get_response_by_sentiment(self, sentiment_label: str, intensity: str = 'medium') -> str:
        """根据情感获取回应模板"""
        templates = self.response_templates.get(sentiment_label, {})
        if intensity in templates:
            responses = templates[intensity]
        else:
            # 降级到可用的强度级别
            available_intensities = list(templates.keys())
            if available_intensities:
                responses = templates[available_intensities[0]]
            else:
                responses = self.response_templates['neutral']['default']
        
        return self.get_random_prompt(responses)
    
    def detect_emotion_patterns(self, text: str) -> Dict[str, float]:
        """检测文本中的情感模式"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    score += 1
            emotion_scores[emotion] = score / len(patterns) if patterns else 0
        
        return emotion_scores
    
    def get_emotion_guidance(self, detected_emotion: str) -> List[str]:
        """获取情感引导策略"""
        guidance_map = {
            'angry': [
                "表示理解和同情",
                "道歉并承诺解决",
                "提供具体解决方案",
                "保持冷静和耐心"
            ],
            'happy': [
                "表达感谢和认可",
                "分享积极情绪",
                "趁机推荐相关产品",
                "巩固良好关系"
            ],
            'sad': [
                "表示同情和理解",
                "提供安慰和支持",
                "寻找解决问题的方式",
                "给予希望和鼓励"
            ],
            'worried': [
                "解释和澄清疑虑",
                "提供保障和承诺",
                "分享成功案例",
                "建立信任关系"
            ],
            'disappointed': [
                "真诚道歉",
                "了解具体原因",
                "提供补偿方案",
                "承诺改进措施"
            ]
        }
        
        return guidance_map.get(detected_emotion, ["保持专业和友好的态度"])
    
    def analyze_sentiment_trend(self, messages: List[str]) -> Dict[str, Any]:
        """分析情感趋势"""
        if not messages:
            return {'trend': 'stable', 'direction': 'neutral'}
        
        sentiment_scores = []
        for message in messages:
            # 简单的情感计分
            positive_count = sum(1 for word in self.emotion_patterns['happy'] if word in message)
            negative_count = sum(1 for word in self.emotion_patterns['angry'] + self.emotion_patterns['sad'] if word in message)
            
            if positive_count > negative_count:
                sentiment_scores.append(1)
            elif negative_count > positive_count:
                sentiment_scores.append(-1)
            else:
                sentiment_scores.append(0)
        
        # 分析趋势
        if len(sentiment_scores) < 2:
            return {'trend': 'stable', 'direction': 'neutral'}
        
        recent_avg = sum(sentiment_scores[-3:]) / min(3, len(sentiment_scores))
        overall_avg = sum(sentiment_scores) / len(sentiment_scores)
        
        if recent_avg > overall_avg + 0.3:
            trend = 'improving'
        elif recent_avg < overall_avg - 0.3:
            trend = 'declining'
        else:
            trend = 'stable'
        
        if recent_avg > 0.3:
            direction = 'positive'
        elif recent_avg < -0.3:
            direction = 'negative'
        else:
            direction = 'neutral'
        
        return {
            'trend': trend,
            'direction': direction,
            'recent_score': recent_avg,
            'overall_score': overall_avg
        } 