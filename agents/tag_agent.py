"""
用户打标签智能体
基于用户行为和对话内容自动为用户添加标签
"""

import re
import jieba
from typing import Dict, Any, List, Set
from datetime import datetime, timedelta
import json

from .base_agent import BaseAgent


class TagAgent(BaseAgent):
    """用户打标签智能体"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("tag_agent", config)
        
        # 预定义标签规则
        self.tag_rules = {
            # 购买意向标签
            'high_intent': {
                'keywords': ['想买', '购买', '下单', '要多少钱', '价格', '优惠', '打折'],
                'patterns': [r'什么时候.*买', r'想.*了解', r'需要.*个']
            },
            'low_intent': {
                'keywords': ['看看', '了解', '随便问问', '先看看'],
                'patterns': [r'先.*看看', r'随便.*问']
            },
            
            # 价格敏感度标签
            'price_sensitive': {
                'keywords': ['便宜', '打折', '优惠', '促销', '活动', '降价', '性价比'],
                'patterns': [r'有.*优惠', r'多少.*钱', r'价格.*怎么样']
            },
            'price_insensitive': {
                'keywords': ['品质', '质量', '高端', '奢侈', '不在乎价格'],
                'patterns': [r'质量.*怎么样', r'品质.*如何']
            },
            
            # 产品偏好标签
            'electronics_lover': {
                'keywords': ['手机', '电脑', '数码', '电子产品', '科技'],
                'patterns': [r'.*手机.*', r'.*电脑.*', r'.*数码.*']
            },
            'fashion_lover': {
                'keywords': ['衣服', '鞋子', '包包', '时尚', '潮流', '搭配'],
                'patterns': [r'.*衣服.*', r'.*时尚.*', r'.*搭配.*']
            },
            
            # 购买频次标签
            'frequent_buyer': {
                'keywords': ['经常买', '老客户', '之前买过', '又来了'],
                'patterns': [r'经常.*买', r'之前.*买过']
            },
            'new_customer': {
                'keywords': ['第一次', '新客户', '刚知道', '朋友推荐'],
                'patterns': [r'第一次.*买', r'刚.*知道']
            },
            
            # 沟通风格标签
            'polite': {
                'keywords': ['请问', '谢谢', '麻烦', '不好意思', '劳烦'],
                'patterns': [r'请.*问', r'谢谢.*', r'不好意思.*']
            },
            'direct': {
                'keywords': ['直接', '快点', '简单说', '别废话'],
                'patterns': [r'直接.*说', r'快.*点', r'简单.*说']
            },
            
            # 决策风格标签
            'decisive': {
                'keywords': ['马上要', '立即', '现在就', '赶紧'],
                'patterns': [r'马上.*要', r'立即.*', r'现在.*就']
            },
            'hesitant': {
                'keywords': ['考虑', '想想', '犹豫', '再看看', '不确定'],
                'patterns': [r'考虑.*一下', r'想.*想', r'再.*看看']
            }
        }
        
        # 行为权重配置
        self.behavior_weights = {
            'message_count': 0.1,        # 消息数量
            'session_duration': 0.15,    # 会话时长
            'quick_response': 0.1,       # 快速回复
            'product_inquiry': 0.2,      # 产品询问
            'price_inquiry': 0.15,       # 价格询问
            'purchase_action': 0.3       # 购买行为
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['user_id', 'message']
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户消息并生成标签"""
        user_id = input_data['user_id']
        message = input_data['message']
        session_data = input_data.get('session_data', {})
        user_history = input_data.get('user_history', [])
        
        # 分析当前消息
        content_tags = self._analyze_message_content(message)
        
        # 分析用户行为
        behavior_tags = self._analyze_user_behavior(session_data, user_history)
        
        # 合并标签
        all_tags = self._merge_tags(content_tags, behavior_tags)
        
        # 计算标签置信度
        tag_scores = self._calculate_tag_scores(all_tags, message, session_data)
        
        # 过滤低置信度标签
        filtered_tags = self._filter_tags(tag_scores)
        
        result = {
            'user_id': user_id,
            'tags': filtered_tags,
            'content_tags': content_tags,
            'behavior_tags': behavior_tags,
            'tag_scores': tag_scores,
            'analysis_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"Generated tags for user {user_id}: {filtered_tags}")
        
        return result
    
    def _analyze_message_content(self, message: str) -> List[str]:
        """分析消息内容生成标签"""
        tags = []
        message_lower = message.lower()
        
        # 分词
        words = list(jieba.cut(message))
        
        for tag_name, rule in self.tag_rules.items():
            # 检查关键词
            keyword_matches = sum(1 for keyword in rule['keywords'] 
                                if keyword in message_lower)
            
            # 检查正则模式
            pattern_matches = sum(1 for pattern in rule.get('patterns', [])
                                if re.search(pattern, message))
            
            # 如果有匹配，添加标签
            if keyword_matches > 0 or pattern_matches > 0:
                tags.append(tag_name)
        
        return tags
    
    def _analyze_user_behavior(self, session_data: Dict[str, Any], 
                             user_history: List[Dict[str, Any]]) -> List[str]:
        """分析用户行为生成标签"""
        tags = []
        
        # 分析会话数据
        if session_data:
            # 消息频率
            message_count = session_data.get('message_count', 0)
            if message_count > 10:
                tags.append('active_user')
            elif message_count > 5:
                tags.append('engaged_user')
            
            # 会话时长
            session_duration = session_data.get('duration_minutes', 0)
            if session_duration > 30:
                tags.append('long_session')
            elif session_duration > 10:
                tags.append('medium_session')
            
            # 响应速度
            avg_response_time = session_data.get('avg_response_time', 0)
            if avg_response_time < 10:
                tags.append('quick_responder')
        
        # 分析历史行为
        if user_history:
            total_sessions = len(user_history)
            if total_sessions > 5:
                tags.append('frequent_visitor')
            
            # 分析购买历史
            purchase_sessions = [s for s in user_history 
                               if s.get('has_purchase', False)]
            if purchase_sessions:
                tags.append('previous_buyer')
                if len(purchase_sessions) > 2:
                    tags.append('loyal_customer')
        
        return tags
    
    def _merge_tags(self, content_tags: List[str], behavior_tags: List[str]) -> List[str]:
        """合并内容标签和行为标签"""
        all_tags = list(set(content_tags + behavior_tags))
        
        # 处理冲突标签
        conflicts = [
            ('high_intent', 'low_intent'),
            ('price_sensitive', 'price_insensitive'),
            ('decisive', 'hesitant'),
            ('polite', 'direct')
        ]
        
        for tag1, tag2 in conflicts:
            if tag1 in all_tags and tag2 in all_tags:
                # 保留出现频率更高的标签，这里简化为保留第一个
                all_tags.remove(tag2)
        
        return all_tags
    
    def _calculate_tag_scores(self, tags: List[str], message: str, 
                            session_data: Dict[str, Any]) -> Dict[str, float]:
        """计算标签置信度分数"""
        scores = {}
        
        for tag in tags:
            score = 0.5  # 基础分数
            
            # 基于关键词频率调整分数
            if tag in self.tag_rules:
                rule = self.tag_rules[tag]
                keyword_count = sum(1 for keyword in rule['keywords']
                                  if keyword in message.lower())
                score += keyword_count * 0.1
                
                pattern_count = sum(1 for pattern in rule.get('patterns', [])
                                  if re.search(pattern, message))
                score += pattern_count * 0.15
            
            # 基于行为数据调整分数
            if session_data:
                if tag == 'active_user' and session_data.get('message_count', 0) > 15:
                    score += 0.2
                elif tag == 'quick_responder' and session_data.get('avg_response_time', 100) < 5:
                    score += 0.2
            
            # 限制分数范围
            scores[tag] = min(max(score, 0.0), 1.0)
        
        return scores
    
    def _filter_tags(self, tag_scores: Dict[str, float], threshold: float = 0.6) -> List[str]:
        """过滤低置信度标签"""
        return [tag for tag, score in tag_scores.items() if score >= threshold]
    
    def add_custom_rule(self, tag_name: str, keywords: List[str], patterns: List[str] = None):
        """添加自定义标签规则"""
        self.tag_rules[tag_name] = {
            'keywords': keywords,
            'patterns': patterns or []
        }
        self.logger.info(f"Added custom tag rule: {tag_name}")
    
    def remove_tag_rule(self, tag_name: str):
        """移除标签规则"""
        if tag_name in self.tag_rules:
            del self.tag_rules[tag_name]
            self.logger.info(f"Removed tag rule: {tag_name}")
    
    def get_available_tags(self) -> List[str]:
        """获取所有可用标签"""
        return list(self.tag_rules.keys())
    
    def analyze_tag_distribution(self, user_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析标签分布统计"""
        tag_counts = {}
        total_users = len(user_tags)
        
        for user_tag_data in user_tags:
            for tag in user_tag_data.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 计算标签使用率
        tag_rates = {
            tag: count / total_users if total_users > 0 else 0
            for tag, count in tag_counts.items()
        }
        
        return {
            'total_users': total_users,
            'tag_counts': tag_counts,
            'tag_rates': tag_rates,
            'most_common_tags': sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        } 