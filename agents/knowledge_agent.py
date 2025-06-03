"""
知识库智能体
基于RAGFlow实现知识检索和智能问答
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base_agent import BaseAgent

# 尝试导入RAGFlow SDK
try:
    from ragflow import RAGFlow
    RAGFLOW_AVAILABLE = True
except ImportError:
    RAGFLOW_AVAILABLE = False
    logging.warning("RAGFlow SDK not available, using fallback implementation")


class KnowledgeAgent(BaseAgent):
    """知识库智能体"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("knowledge_agent", config)
        
        # RAGFlow配置
        self.ragflow_config = config.get('ragflow', {})
        self.api_endpoint = self.ragflow_config.get('api_endpoint', 'http://localhost:9380')
        self.api_key = self.ragflow_config.get('api_key', '')
        self.dataset_id = self.ragflow_config.get('dataset_id', '')
        
        # 知识库配置
        self.knowledge_bases = config.get('knowledge_bases', {})
        self.default_kb = config.get('default_knowledge_base', 'general')
        
        # 检索配置
        self.top_k = config.get('top_k', 5)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        
        # 初始化RAGFlow客户端
        if RAGFLOW_AVAILABLE and self.api_key:
            try:
                self.ragflow_client = RAGFlow(api_key=self.api_key, base_url=self.api_endpoint)
                self.logger.info("RAGFlow client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize RAGFlow client: {e}")
                self.ragflow_client = None
        else:
            self.ragflow_client = None
        
        # 本地知识库缓存
        self.local_knowledge_cache = {}
        
        # 查询历史
        self.query_history = []
        
        # 知识类型映射
        self.knowledge_type_mapping = {
            'product': ['商品信息', '产品参数', '规格说明'],
            'faq': ['常见问题', '使用说明', '故障排除'],
            'policy': ['购买政策', '退换货政策', '服务条款'],
            'script': ['销售话术', '客服话术', '沟通技巧']
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['query']
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理知识库查询"""
        query = input_data['query']
        user_id = input_data.get('user_id', 'anonymous')
        knowledge_base = input_data.get('knowledge_base', self.default_kb)
        context = input_data.get('context', {})
        
        # 记录查询历史
        query_record = {
            'query': query,
            'user_id': user_id,
            'knowledge_base': knowledge_base,
            'timestamp': datetime.now().isoformat()
        }
        self.query_history.append(query_record)
        
        # 1. 查询预处理
        processed_query = self._preprocess_query(query, context)
        
        # 2. 知识检索
        if self.ragflow_client:
            # 使用RAGFlow进行检索
            search_results = await self._search_with_ragflow(processed_query, knowledge_base)
        else:
            # 使用本地知识库
            search_results = await self._search_local_knowledge(processed_query, knowledge_base)
        
        # 3. 结果排序和过滤
        filtered_results = self._filter_and_rank_results(search_results, query, context)
        
        # 4. 生成回答
        answer = await self._generate_answer(query, filtered_results, context)
        
        # 5. 后处理
        final_answer = self._postprocess_answer(answer, context)
        
        result = {
            'query': query,
            'answer': final_answer,
            'knowledge_sources': filtered_results,
            'knowledge_base': knowledge_base,
            'confidence': self._calculate_confidence(filtered_results, answer),
            'search_stats': {
                'total_results': len(search_results),
                'filtered_results': len(filtered_results),
                'search_time': datetime.now().isoformat()
            }
        }
        
        self.logger.info(f"Knowledge query processed: {query[:50]}... -> {len(filtered_results)} results")
        
        return result
    
    def _preprocess_query(self, query: str, context: Dict[str, Any]) -> str:
        """查询预处理"""
        processed_query = query.strip()
        
        # 移除停用词和无意义词汇
        stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '些', '什么', '怎么', '哪里'}
        words = processed_query.split()
        words = [word for word in words if word not in stop_words]
        
        # 添加上下文信息
        if context.get('user_tags'):
            user_tags = context['user_tags']
            # 根据用户标签调整查询
            if 'electronics_lover' in user_tags:
                processed_query += ' 电子产品'
            elif 'fashion_lover' in user_tags:
                processed_query += ' 时尚服装'
        
        # 意图识别增强
        if context.get('intent'):
            intent = context['intent']
            if intent == 'price_inquiry':
                processed_query += ' 价格 费用'
            elif intent == 'product_comparison':
                processed_query += ' 对比 区别'
        
        return processed_query
    
    async def _search_with_ragflow(self, query: str, knowledge_base: str) -> List[Dict[str, Any]]:
        """使用RAGFlow进行知识检索"""
        try:
            # 使用RAGFlow API进行检索
            search_params = {
                'question': query,
                'dataset_ids': [self.dataset_id] if self.dataset_id else [],
                'top_k': self.top_k,
                'similarity_threshold': self.similarity_threshold
            }
            
            # 调用RAGFlow检索API
            response = await self._call_ragflow_api('/v1/retrieval', search_params)
            
            if response and 'data' in response:
                results = []
                for item in response['data']:
                    result = {
                        'content': item.get('content', ''),
                        'title': item.get('title', ''),
                        'source': item.get('source', ''),
                        'score': item.get('score', 0.0),
                        'metadata': item.get('metadata', {}),
                        'knowledge_type': self._classify_knowledge_type(item.get('content', ''))
                    }
                    results.append(result)
                
                return results
            
            return []
            
        except Exception as e:
            self.logger.error(f"RAGFlow search error: {e}")
            # 回退到本地搜索
            return await self._search_local_knowledge(query, knowledge_base)
    
    async def _call_ragflow_api(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """调用RAGFlow API"""
        try:
            url = f"{self.api_endpoint}{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"RAGFlow API call failed: {e}")
            return None
    
    async def _search_local_knowledge(self, query: str, knowledge_base: str) -> List[Dict[str, Any]]:
        """本地知识库搜索（备用方案）"""
        results = []
        
        # 从Django模型中获取知识
        try:
            from backend.apps.knowledge.models import FAQ, Product, Script, Document
            
            # 搜索FAQ
            faqs = FAQ.objects.filter(
                question__icontains=query,
                is_active=True
            ).order_by('-priority')[:self.top_k//2]
            
            for faq in faqs:
                results.append({
                    'content': f"问题：{faq.question}\n答案：{faq.answer}",
                    'title': faq.question,
                    'source': 'FAQ',
                    'score': 0.8,  # 默认分数
                    'metadata': {'category': faq.category, 'faq_id': faq.id},
                    'knowledge_type': 'faq'
                })
            
            # 搜索产品信息
            products = Product.objects.filter(
                name__icontains=query,
                status='active'
            )[:self.top_k//2]
            
            for product in products:
                results.append({
                    'content': f"商品：{product.name}\n描述：{product.description}\n价格：{product.price}",
                    'title': product.name,
                    'source': 'Product',
                    'score': 0.75,
                    'metadata': {'category': product.category, 'product_id': product.id},
                    'knowledge_type': 'product'
                })
            
        except Exception as e:
            self.logger.error(f"Local knowledge search error: {e}")
        
        return results
    
    def _classify_knowledge_type(self, content: str) -> str:
        """分类知识类型"""
        content_lower = content.lower()
        
        for knowledge_type, keywords in self.knowledge_type_mapping.items():
            if any(keyword in content_lower for keyword in keywords):
                return knowledge_type
        
        return 'general'
    
    def _filter_and_rank_results(self, results: List[Dict[str, Any]], 
                                query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤和排序搜索结果"""
        if not results:
            return []
        
        # 过滤低相关性结果
        filtered_results = [
            result for result in results 
            if result.get('score', 0) >= self.similarity_threshold
        ]
        
        # 基于上下文重新评分
        for result in filtered_results:
            original_score = result.get('score', 0)
            context_bonus = self._calculate_context_bonus(result, context)
            result['score'] = min(original_score + context_bonus, 1.0)
        
        # 按分数排序
        filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 去重
        seen_content = set()
        unique_results = []
        for result in filtered_results:
            content_hash = hash(result.get('content', ''))
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results[:self.top_k]
    
    def _calculate_context_bonus(self, result: Dict[str, Any], context: Dict[str, Any]) -> float:
        """计算上下文奖励分数"""
        bonus = 0.0
        
        # 用户标签匹配
        user_tags = context.get('user_tags', [])
        result_type = result.get('knowledge_type', '')
        
        if 'price_sensitive' in user_tags and '价格' in result.get('content', ''):
            bonus += 0.1
        
        if 'electronics_lover' in user_tags and result_type == 'product':
            bonus += 0.1
        
        # 会话主题匹配
        session_topics = context.get('session_topics', [])
        content = result.get('content', '').lower()
        
        for topic in session_topics:
            if topic in content:
                bonus += 0.05
        
        # 历史查询相关性
        recent_queries = context.get('recent_queries', [])
        for query in recent_queries[-3:]:  # 最近3次查询
            if any(word in content for word in query.split()):
                bonus += 0.03
        
        return min(bonus, 0.3)  # 最大奖励0.3
    
    async def _generate_answer(self, query: str, knowledge_sources: List[Dict[str, Any]], 
                             context: Dict[str, Any]) -> str:
        """基于知识源生成回答"""
        if not knowledge_sources:
            return self._get_fallback_answer(query, context)
        
        # 构建回答
        answer_parts = []
        
        # 主要回答（来自最相关的知识源）
        primary_source = knowledge_sources[0]
        primary_content = primary_source.get('content', '')
        
        # 根据知识类型调整回答格式
        knowledge_type = primary_source.get('knowledge_type', 'general')
        
        if knowledge_type == 'faq':
            answer_parts.append(f"根据常见问题解答：{primary_content}")
        elif knowledge_type == 'product':
            answer_parts.append(f"关于该产品：{primary_content}")
        elif knowledge_type == 'policy':
            answer_parts.append(f"根据相关政策：{primary_content}")
        else:
            answer_parts.append(primary_content)
        
        # 补充信息（来自其他相关知识源）
        if len(knowledge_sources) > 1:
            supplementary_info = []
            for source in knowledge_sources[1:3]:  # 最多2个补充源
                if source.get('score', 0) > 0.6:  # 只包含高相关性的补充信息
                    content = source.get('content', '')[:200]  # 限制长度
                    supplementary_info.append(content)
            
            if supplementary_info:
                answer_parts.append(f"\n\n补充信息：\n{'; '.join(supplementary_info)}")
        
        # 添加建议
        suggestions = self._generate_suggestions(query, knowledge_sources, context)
        if suggestions:
            answer_parts.append(f"\n\n建议：{suggestions}")
        
        return ''.join(answer_parts)
    
    def _get_fallback_answer(self, query: str, context: Dict[str, Any]) -> str:
        """获取备用回答"""
        fallback_responses = [
            "抱歉，我暂时没有找到相关信息。您可以尝试换个问法，或者联系人工客服获得更详细的帮助。",
            "关于您的问题，我需要了解更多信息才能给出准确回答。请问您能提供更多详细信息吗？",
            "很抱歉，这个问题超出了我目前的知识范围。建议您咨询我们的专业客服人员。"
        ]
        
        # 根据上下文选择合适的回答
        user_tags = context.get('user_tags', [])
        if 'polite' in user_tags:
            return fallback_responses[0]
        elif 'direct' in user_tags:
            return fallback_responses[2]
        else:
            return fallback_responses[1]
    
    def _generate_suggestions(self, query: str, knowledge_sources: List[Dict[str, Any]], 
                            context: Dict[str, Any]) -> str:
        """生成相关建议"""
        suggestions = []
        
        # 基于知识类型给出建议
        knowledge_types = [source.get('knowledge_type') for source in knowledge_sources]
        
        if 'product' in knowledge_types:
            suggestions.append("您可以查看产品详情页面了解更多信息")
        
        if 'faq' in knowledge_types:
            suggestions.append("如有其他疑问，可查看完整的常见问题列表")
        
        # 基于用户标签给出个性化建议
        user_tags = context.get('user_tags', [])
        if 'price_sensitive' in user_tags:
            suggestions.append("关注我们的优惠活动可获得更好价格")
        
        if 'high_intent' in user_tags:
            suggestions.append("如需下单，我可以为您提供购买指导")
        
        return "；".join(suggestions)
    
    def _postprocess_answer(self, answer: str, context: Dict[str, Any]) -> str:
        """回答后处理"""
        # 长度限制
        if len(answer) > self.max_tokens:
            answer = answer[:self.max_tokens] + "..."
        
        # 根据用户沟通风格调整
        user_tags = context.get('user_tags', [])
        
        if 'direct' in user_tags:
            # 直接用户，去除客套话
            answer = answer.replace("很高兴为您服务", "").replace("如有其他问题请告诉我", "")
        elif 'polite' in user_tags:
            # 礼貌用户，添加友好表达
            if not any(word in answer for word in ['谢谢', '感谢', '希望']):
                answer += "\n\n希望这些信息对您有帮助！"
        
        return answer.strip()
    
    def _calculate_confidence(self, knowledge_sources: List[Dict[str, Any]], answer: str) -> float:
        """计算回答置信度"""
        if not knowledge_sources:
            return 0.1
        
        # 基于搜索结果的平均分数
        avg_score = sum(source.get('score', 0) for source in knowledge_sources) / len(knowledge_sources)
        
        # 基于回答长度（适中长度置信度更高）
        answer_length = len(answer)
        length_factor = 1.0
        if answer_length < 50:
            length_factor = 0.8
        elif answer_length > 500:
            length_factor = 0.9
        
        # 基于知识源数量
        source_factor = min(len(knowledge_sources) / 3, 1.0)
        
        confidence = avg_score * length_factor * source_factor
        return min(max(confidence, 0.0), 1.0)
    
    def add_knowledge_source(self, knowledge_type: str, content: str, metadata: Dict[str, Any] = None):
        """添加本地知识源"""
        if knowledge_type not in self.local_knowledge_cache:
            self.local_knowledge_cache[knowledge_type] = []
        
        knowledge_item = {
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'type': knowledge_type
        }
        
        self.local_knowledge_cache[knowledge_type].append(knowledge_item)
        self.logger.info(f"Added knowledge item to {knowledge_type}")
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        if not self.query_history:
            return {'total_queries': 0}
        
        total_queries = len(self.query_history)
        
        # 统计查询频率
        from collections import Counter
        knowledge_base_counts = Counter(q['knowledge_base'] for q in self.query_history)
        user_counts = Counter(q['user_id'] for q in self.query_history)
        
        # 最近查询
        recent_queries = self.query_history[-10:]
        
        return {
            'total_queries': total_queries,
            'knowledge_base_distribution': dict(knowledge_base_counts),
            'top_users': dict(user_counts.most_common(5)),
            'recent_queries': recent_queries,
            'average_queries_per_hour': self._calculate_query_rate()
        }
    
    def _calculate_query_rate(self) -> float:
        """计算每小时查询率"""
        if len(self.query_history) < 2:
            return 0.0
        
        try:
            first_query = datetime.fromisoformat(self.query_history[0]['timestamp'])
            last_query = datetime.fromisoformat(self.query_history[-1]['timestamp'])
            
            hours_diff = (last_query - first_query).total_seconds() / 3600
            if hours_diff > 0:
                return len(self.query_history) / hours_diff
        except:
            pass
        
        return 0.0 