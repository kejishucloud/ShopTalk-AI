"""
上下文记忆对话智能体
管理对话历史，维护上下文信息，提供上下文感知的对话能力
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import hashlib

from .base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    """上下文记忆对话智能体"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("memory_agent", config)
        
        # 配置参数
        self.max_short_memory = config.get('max_short_memory', 20)  # 短期记忆最大条数
        self.max_long_memory = config.get('max_long_memory', 100)   # 长期记忆最大条数
        self.context_window = config.get('context_window', 10)      # 上下文窗口大小
        self.memory_decay_hours = config.get('memory_decay_hours', 24)  # 记忆衰减时间
        
        # 内存存储（实际应用中应该使用数据库）
        self.short_memory: Dict[str, deque] = {}  # 用户短期记忆
        self.long_memory: Dict[str, List] = {}    # 用户长期记忆
        self.session_context: Dict[str, Dict] = {}  # 会话上下文
        
        # 重要信息关键词
        self.important_keywords = {
            'personal_info': ['姓名', '电话', '地址', '邮箱', '年龄', '生日'],
            'preferences': ['喜欢', '不喜欢', '偏好', '习惯', '风格'],
            'purchase_intent': ['想买', '购买', '下单', '价格', '预算'],
            'complaints': ['投诉', '问题', '故障', '不满意', '退货', '退款'],
            'compliments': ['满意', '好评', '推荐', '赞', '棒', '不错'],
            'product_interests': ['关注', '了解', '咨询', '询问', '感兴趣']
        }
        
        # 会话状态
        self.conversation_states = [
            'greeting', 'information_gathering', 'product_recommendation',
            'price_negotiation', 'order_processing', 'after_sales', 'closing'
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['user_id', 'message']
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话并更新记忆"""
        user_id = input_data['user_id']
        message = input_data['message']
        session_id = input_data.get('session_id', 'default')
        message_type = input_data.get('message_type', 'user')  # user/assistant
        timestamp = input_data.get('timestamp', datetime.now().isoformat())
        
        # 创建消息记录
        message_record = {
            'message': message,
            'type': message_type,
            'timestamp': timestamp,
            'session_id': session_id,
            'metadata': input_data.get('metadata', {})
        }
        
        # 更新短期记忆
        self._update_short_memory(user_id, message_record)
        
        # 提取并更新重要信息到长期记忆
        important_info = self._extract_important_info(message, message_type)
        if important_info:
            self._update_long_memory(user_id, important_info)
        
        # 更新会话上下文
        self._update_session_context(user_id, session_id, message_record)
        
        # 生成上下文摘要
        context = self._generate_context(user_id, session_id)
        
        # 预测下一步意图
        next_intent = self._predict_next_intent(user_id, session_id)
        
        result = {
            'user_id': user_id,
            'session_id': session_id,
            'context': context,
            'next_intent': next_intent,
            'conversation_state': self._get_conversation_state(user_id, session_id),
            'memory_stats': self._get_memory_stats(user_id),
            'updated_at': datetime.now().isoformat()
        }
        
        self.logger.info(f"Updated memory for user {user_id}, session {session_id}")
        
        return result
    
    def _update_short_memory(self, user_id: str, message_record: Dict[str, Any]):
        """更新短期记忆"""
        if user_id not in self.short_memory:
            self.short_memory[user_id] = deque(maxlen=self.max_short_memory)
        
        self.short_memory[user_id].append(message_record)
    
    def _extract_important_info(self, message: str, message_type: str) -> Dict[str, Any]:
        """提取重要信息"""
        important_info = {}
        message_lower = message.lower()
        
        # 只处理用户消息
        if message_type != 'user':
            return important_info
        
        for category, keywords in self.important_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if category not in important_info:
                        important_info[category] = []
                    
                    # 提取包含关键词的句子
                    sentences = message.split('。')
                    for sentence in sentences:
                        if keyword in sentence:
                            important_info[category].append({
                                'content': sentence.strip(),
                                'keyword': keyword,
                                'timestamp': datetime.now().isoformat(),
                                'confidence': self._calculate_info_confidence(sentence, keyword)
                            })
        
        return important_info
    
    def _calculate_info_confidence(self, sentence: str, keyword: str) -> float:
        """计算信息置信度"""
        base_confidence = 0.5
        
        # 句子长度影响置信度
        if len(sentence) > 10:
            base_confidence += 0.2
        
        # 关键词位置影响置信度
        keyword_position = sentence.find(keyword) / len(sentence)
        if keyword_position < 0.3:  # 关键词在前面，置信度高
            base_confidence += 0.2
        
        # 是否包含确定性词汇
        certainty_words = ['是', '确实', '肯定', '一定', '绝对']
        if any(word in sentence for word in certainty_words):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _update_long_memory(self, user_id: str, important_info: Dict[str, Any]):
        """更新长期记忆"""
        if user_id not in self.long_memory:
            self.long_memory[user_id] = []
        
        memory_record = {
            'info': important_info,
            'timestamp': datetime.now().isoformat(),
            'hash': hashlib.md5(str(important_info).encode()).hexdigest()
        }
        
        # 检查是否已存在相似信息
        existing_hashes = [record.get('hash') for record in self.long_memory[user_id]]
        if memory_record['hash'] not in existing_hashes:
            self.long_memory[user_id].append(memory_record)
            
            # 限制长期记忆大小
            if len(self.long_memory[user_id]) > self.max_long_memory:
                self.long_memory[user_id] = self.long_memory[user_id][-self.max_long_memory:]
    
    def _update_session_context(self, user_id: str, session_id: str, message_record: Dict[str, Any]):
        """更新会话上下文"""
        session_key = f"{user_id}:{session_id}"
        
        if session_key not in self.session_context:
            self.session_context[session_key] = {
                'start_time': datetime.now().isoformat(),
                'message_count': 0,
                'topics': [],
                'entities': {},
                'conversation_flow': []
            }
        
        context = self.session_context[session_key]
        context['message_count'] += 1
        context['last_update'] = datetime.now().isoformat()
        
        # 提取主题
        topics = self._extract_topics(message_record['message'])
        for topic in topics:
            if topic not in context['topics']:
                context['topics'].append(topic)
        
        # 提取实体
        entities = self._extract_entities(message_record['message'])
        for entity_type, entity_value in entities.items():
            context['entities'][entity_type] = entity_value
        
        # 记录对话流程
        context['conversation_flow'].append({
            'type': message_record['type'],
            'timestamp': message_record['timestamp'],
            'topic': topics[0] if topics else 'general'
        })
    
    def _extract_topics(self, message: str) -> List[str]:
        """提取消息主题"""
        topics = []
        
        # 简单的基于关键词的主题提取
        topic_keywords = {
            'product': ['商品', '产品', '手机', '电脑', '衣服', '鞋子'],
            'price': ['价格', '多少钱', '便宜', '贵', '优惠', '折扣'],
            'shipping': ['快递', '配送', '邮费', '运费', '发货', '物流'],
            'service': ['服务', '客服', '售后', '维修', '保修'],
            'payment': ['付款', '支付', '结账', '订单', '下单'],
            'complaint': ['投诉', '问题', '故障', '不满意', '退货']
        }
        
        message_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics or ['general']
    
    def _extract_entities(self, message: str) -> Dict[str, str]:
        """提取命名实体"""
        entities = {}
        
        # 简单的实体提取（实际应用中可以使用NER模型）
        import re
        
        # 提取手机号
        phone_pattern = r'1[3-9]\d{9}'
        phone_match = re.search(phone_pattern, message)
        if phone_match:
            entities['phone'] = phone_match.group()
        
        # 提取邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            entities['email'] = email_match.group()
        
        # 提取金额
        money_pattern = r'(\d+(\.\d{1,2})?)\s*(元|块|万|千)'
        money_match = re.search(money_pattern, message)
        if money_match:
            entities['amount'] = money_match.group()
        
        return entities
    
    def _generate_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """生成当前对话上下文"""
        context = {
            'recent_messages': [],
            'user_profile': {},
            'session_summary': {},
            'relevant_history': []
        }
        
        # 获取最近消息
        if user_id in self.short_memory:
            recent_messages = list(self.short_memory[user_id])[-self.context_window:]
            context['recent_messages'] = recent_messages
        
        # 生成用户画像
        context['user_profile'] = self._generate_user_profile(user_id)
        
        # 会话摘要
        session_key = f"{user_id}:{session_id}"
        if session_key in self.session_context:
            session_data = self.session_context[session_key]
            context['session_summary'] = {
                'duration_minutes': self._calculate_session_duration(session_data),
                'message_count': session_data['message_count'],
                'topics': session_data['topics'],
                'entities': session_data['entities']
            }
        
        # 相关历史信息
        context['relevant_history'] = self._get_relevant_history(user_id, context['recent_messages'])
        
        return context
    
    def _generate_user_profile(self, user_id: str) -> Dict[str, Any]:
        """生成用户画像"""
        profile = {
            'preferences': {},
            'behavior_patterns': {},
            'interaction_style': 'unknown',
            'purchase_history': []
        }
        
        if user_id in self.long_memory:
            for record in self.long_memory[user_id]:
                info = record['info']
                
                # 提取偏好信息
                if 'preferences' in info:
                    for pref in info['preferences']:
                        profile['preferences'][pref['keyword']] = pref['content']
                
                # 提取个人信息
                if 'personal_info' in info:
                    for personal in info['personal_info']:
                        profile[personal['keyword']] = personal['content']
        
        # 分析行为模式
        if user_id in self.short_memory:
            messages = list(self.short_memory[user_id])
            profile['behavior_patterns'] = self._analyze_behavior_patterns(messages)
        
        return profile
    
    def _analyze_behavior_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析用户行为模式"""
        patterns = {
            'avg_message_length': 0,
            'response_speed': 'medium',
            'question_frequency': 0,
            'politeness_level': 'medium'
        }
        
        if not messages:
            return patterns
        
        user_messages = [msg for msg in messages if msg['type'] == 'user']
        
        if user_messages:
            # 平均消息长度
            total_length = sum(len(msg['message']) for msg in user_messages)
            patterns['avg_message_length'] = total_length / len(user_messages)
            
            # 问题频率
            question_count = sum(1 for msg in user_messages if '?' in msg['message'] or '？' in msg['message'])
            patterns['question_frequency'] = question_count / len(user_messages)
            
            # 礼貌程度
            polite_words = ['请', '谢谢', '不好意思', '麻烦', '劳烦']
            polite_count = sum(1 for msg in user_messages 
                             if any(word in msg['message'] for word in polite_words))
            politeness_ratio = polite_count / len(user_messages)
            
            if politeness_ratio > 0.3:
                patterns['politeness_level'] = 'high'
            elif politeness_ratio > 0.1:
                patterns['politeness_level'] = 'medium'
            else:
                patterns['politeness_level'] = 'low'
        
        return patterns
    
    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> float:
        """计算会话时长（分钟）"""
        try:
            start_time = datetime.fromisoformat(session_data['start_time'])
            last_update = datetime.fromisoformat(session_data.get('last_update', session_data['start_time']))
            duration = (last_update - start_time).total_seconds() / 60
            return round(duration, 2)
        except:
            return 0.0
    
    def _get_relevant_history(self, user_id: str, recent_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取相关历史信息"""
        relevant_history = []
        
        if user_id not in self.long_memory:
            return relevant_history
        
        # 提取最近消息的关键词
        recent_keywords = set()
        for msg in recent_messages:
            if msg['type'] == 'user':
                # 简单的关键词提取
                words = msg['message'].split()
                recent_keywords.update(words)
        
        # 查找相关的历史记录
        for record in self.long_memory[user_id]:
            record_text = str(record['info'])
            if any(keyword in record_text for keyword in recent_keywords):
                relevant_history.append(record)
        
        return relevant_history[-5:]  # 返回最近5条相关记录
    
    def _predict_next_intent(self, user_id: str, session_id: str) -> str:
        """预测下一步意图"""
        session_key = f"{user_id}:{session_id}"
        
        if session_key not in self.session_context:
            return 'information_gathering'
        
        session_data = self.session_context[session_key]
        topics = session_data.get('topics', [])
        flow = session_data.get('conversation_flow', [])
        
        # 基于话题和对话流程预测意图
        if 'price' in topics and len(flow) > 3:
            return 'price_negotiation'
        elif 'product' in topics:
            return 'product_recommendation'
        elif 'complaint' in topics:
            return 'after_sales'
        elif 'payment' in topics:
            return 'order_processing'
        else:
            return 'information_gathering'
    
    def _get_conversation_state(self, user_id: str, session_id: str) -> str:
        """获取当前对话状态"""
        session_key = f"{user_id}:{session_id}"
        
        if session_key not in self.session_context:
            return 'greeting'
        
        session_data = self.session_context[session_key]
        message_count = session_data.get('message_count', 0)
        
        # 基于消息数量和内容判断对话状态
        if message_count <= 2:
            return 'greeting'
        elif message_count <= 5:
            return 'information_gathering'
        elif message_count <= 10:
            return 'product_recommendation'
        else:
            return 'order_processing'
    
    def _get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        stats = {
            'short_memory_count': 0,
            'long_memory_count': 0,
            'session_count': 0,
            'oldest_memory': None,
            'total_interactions': 0
        }
        
        if user_id in self.short_memory:
            stats['short_memory_count'] = len(self.short_memory[user_id])
        
        if user_id in self.long_memory:
            stats['long_memory_count'] = len(self.long_memory[user_id])
            if self.long_memory[user_id]:
                stats['oldest_memory'] = self.long_memory[user_id][0]['timestamp']
        
        # 统计会话数量
        user_sessions = [key for key in self.session_context.keys() if key.startswith(f"{user_id}:")]
        stats['session_count'] = len(user_sessions)
        
        # 统计总交互次数
        for session_key in user_sessions:
            stats['total_interactions'] += self.session_context[session_key].get('message_count', 0)
        
        return stats
    
    def clear_expired_memory(self):
        """清理过期记忆"""
        current_time = datetime.now()
        expired_threshold = current_time - timedelta(hours=self.memory_decay_hours)
        
        # 清理过期的长期记忆
        for user_id in list(self.long_memory.keys()):
            valid_memories = []
            for record in self.long_memory[user_id]:
                try:
                    record_time = datetime.fromisoformat(record['timestamp'])
                    if record_time > expired_threshold:
                        valid_memories.append(record)
                except:
                    continue
            
            if valid_memories:
                self.long_memory[user_id] = valid_memories
            else:
                del self.long_memory[user_id]
        
        self.logger.info("Expired memory cleared")
    
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户完整摘要"""
        return {
            'user_id': user_id,
            'profile': self._generate_user_profile(user_id),
            'memory_stats': self._get_memory_stats(user_id),
            'recent_activity': list(self.short_memory.get(user_id, []))[-5:],
            'important_info': self.long_memory.get(user_id, [])[-10:]
        } 