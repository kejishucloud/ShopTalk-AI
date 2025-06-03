"""
AI模型管理服务类
提供模型调用、负载均衡、性能监控等功能
"""

import time
import asyncio
import logging
import random
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import F, Avg
from django.db import models
from django.conf import settings
import aiohttp

# AI相关导入 - 这些依赖可能需要单独安装
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from .models import (
    AIModel, ModelCallRecord, ModelPerformance, ModelLoadBalancer,
    ModelWeight, ModelQuota
)

logger = logging.getLogger('ai_models')


class ModelCallService:
    """模型调用服务"""
    
    def __init__(self):
        self.client_cache = {}
    
    def get_client(self, model: AIModel):
        """获取模型客户端"""
        cache_key = f"{model.provider.provider_type}_{model.id}"
        
        if cache_key not in self.client_cache:
            if model.provider.provider_type == 'openai':
                self.client_cache[cache_key] = openai.OpenAI(
                    api_key=model.api_key or settings.OPENAI_API_KEY,
                    base_url=model.provider.base_url or None
                )
            elif model.provider.provider_type == 'anthropic':
                self.client_cache[cache_key] = anthropic.Anthropic(
                    api_key=model.api_key or settings.ANTHROPIC_API_KEY
                )
            elif model.provider.provider_type == 'azure':
                self.client_cache[cache_key] = openai.AzureOpenAI(
                    api_key=model.api_key,
                    azure_endpoint=model.provider.base_url,
                    api_version=model.provider.api_version or "2024-02-15-preview"
                )
            else:
                # 自定义API或其他提供商
                self.client_cache[cache_key] = self._create_custom_client(model)
        
        return self.client_cache[cache_key]
    
    def _create_custom_client(self, model: AIModel):
        """创建自定义客户端"""
        return {
            'base_url': model.provider.base_url,
            'api_key': model.api_key,
            'model_id': model.model_id,
            'additional_config': model.additional_config
        }
    
    async def call_model(
        self,
        model: AIModel,
        input_text: str,
        parameters: Dict[str, Any] = None,
        session_id: str = "",
        user=None,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Dict[str, Any]:
        """
        调用AI模型
        """
        start_time = time.time()
        request_id = self._generate_request_id()
        
        # 检查配额
        quota_check = self._check_quota(model, user)
        if not quota_check['allowed']:
            return {
                'success': False,
                'error': quota_check['error'],
                'error_type': 'quota_exceeded'
            }
        
        # 准备调用参数
        call_params = self._prepare_call_parameters(model, parameters)
        
        try:
            # 根据提供商类型调用不同的API
            if model.provider.provider_type in ['openai', 'azure']:
                result = await self._call_openai_compatible(model, input_text, call_params)
            elif model.provider.provider_type == 'anthropic':
                result = await self._call_anthropic(model, input_text, call_params)
            elif model.provider.provider_type in ['baidu', 'alibaba', 'tencent']:
                result = await self._call_chinese_provider(model, input_text, call_params)
            else:
                result = await self._call_custom_api(model, input_text, call_params)
            
            response_time = time.time() - start_time
            
            # 记录调用
            record = self._create_call_record(
                model=model,
                session_id=session_id,
                user=user,
                input_text=input_text,
                parameters=call_params,
                result=result,
                response_time=response_time,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # 更新配额
            if result['success']:
                self._update_quota(model, user, record)
            
            result['request_id'] = request_id
            result['response_time'] = response_time
            result['record_id'] = record.id
            
            return result
            
        except Exception as e:
            logger.error(f"模型调用失败: {model.name} - {str(e)}")
            response_time = time.time() - start_time
            
            # 记录失败的调用
            self._create_call_record(
                model=model,
                session_id=session_id,
                user=user,
                input_text=input_text,
                parameters=call_params,
                result={'success': False, 'error': str(e)},
                response_time=response_time,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                'success': False,
                'error': str(e),
                'error_type': 'call_failed',
                'request_id': request_id,
                'response_time': response_time
            }
    
    async def _call_openai_compatible(self, model: AIModel, input_text: str, params: Dict) -> Dict:
        """调用OpenAI兼容API"""
        try:
            client = self.get_client(model)
            
            messages = [{"role": "user", "content": input_text}]
            
            response = await client.chat.completions.create(
                model=model.model_id,
                messages=messages,
                temperature=params.get('temperature', model.default_temperature),
                max_tokens=params.get('max_tokens', model.max_tokens),
                top_p=params.get('top_p', model.default_top_p),
                **params.get('additional_params', {})
            )
            
            return {
                'success': True,
                'output_text': response.choices[0].message.content,
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'cost': model.calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'cost': 0
            }
    
    async def _call_anthropic(self, model: AIModel, input_text: str, params: Dict) -> Dict:
        """调用Anthropic API"""
        try:
            client = self.get_client(model)
            
            response = await client.messages.create(
                model=model.model_id,
                max_tokens=params.get('max_tokens', model.max_tokens),
                temperature=params.get('temperature', model.default_temperature),
                messages=[{"role": "user", "content": input_text}]
            )
            
            # Anthropic的token计算可能需要单独处理
            input_tokens = len(input_text) // 4  # 粗略估算
            output_tokens = len(response.content[0].text) // 4
            
            return {
                'success': True,
                'output_text': response.content[0].text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': model.calculate_cost(input_tokens, output_tokens)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'cost': 0
            }
    
    async def _call_chinese_provider(self, model: AIModel, input_text: str, params: Dict) -> Dict:
        """调用中国AI提供商API"""
        try:
            # 这里需要根据具体的提供商实现
            # 例如百度文心、阿里通义千问等
            headers = {
                'Authorization': f'Bearer {model.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model.model_id,
                'messages': [{'role': 'user', 'content': input_text}],
                'temperature': params.get('temperature', model.default_temperature),
                'max_tokens': params.get('max_tokens', model.max_tokens)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    model.provider.base_url,
                    headers=headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        # 根据不同提供商的响应格式解析
                        return self._parse_chinese_provider_response(result, model)
                    else:
                        return {
                            'success': False,
                            'error': result.get('error', {}).get('message', 'API调用失败'),
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'total_tokens': 0,
                            'cost': 0
                        }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'cost': 0
            }
    
    async def _call_custom_api(self, model: AIModel, input_text: str, params: Dict) -> Dict:
        """调用自定义API"""
        try:
            client_config = self.get_client(model)
            
            headers = {
                'Authorization': f'Bearer {client_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': client_config["model_id"],
                'input': input_text,
                'parameters': params,
                **client_config.get("additional_config", {})
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    client_config["base_url"],
                    headers=headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            'success': True,
                            'output_text': result.get('output', ''),
                            'input_tokens': result.get('usage', {}).get('input_tokens', 0),
                            'output_tokens': result.get('usage', {}).get('output_tokens', 0),
                            'total_tokens': result.get('usage', {}).get('total_tokens', 0),
                            'cost': model.calculate_cost(
                                result.get('usage', {}).get('input_tokens', 0),
                                result.get('usage', {}).get('output_tokens', 0)
                            )
                        }
                    else:
                        return {
                            'success': False,
                            'error': result.get('error', 'API调用失败'),
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'total_tokens': 0,
                            'cost': 0
                        }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'cost': 0
            }
    
    def _parse_chinese_provider_response(self, result: Dict, model: AIModel) -> Dict:
        """解析中国AI提供商的响应"""
        # 这里需要根据不同提供商的具体格式实现
        # 示例格式
        output_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = result.get('usage', {})
        
        return {
            'success': True,
            'output_text': output_text,
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0),
            'cost': model.calculate_cost(
                usage.get('prompt_tokens', 0),
                usage.get('completion_tokens', 0)
            )
        }
    
    def _prepare_call_parameters(self, model: AIModel, parameters: Dict[str, Any] = None) -> Dict:
        """准备调用参数"""
        params = {
            'temperature': model.default_temperature,
            'max_tokens': model.max_tokens,
            'top_p': model.default_top_p
        }
        
        if parameters:
            params.update(parameters)
        
        # 验证参数范围
        params['temperature'] = max(0.0, min(2.0, params['temperature']))
        params['top_p'] = max(0.0, min(1.0, params['top_p']))
        params['max_tokens'] = max(1, min(model.max_tokens, params['max_tokens']))
        
        return params
    
    def _check_quota(self, model: AIModel, user) -> Dict[str, Any]:
        """检查配额限制"""
        if not user:
            return {'allowed': True}
        
        quotas = ModelQuota.objects.filter(
            model=model,
            user=user,
            is_active=True
        )
        
        for quota in quotas:
            if quota.is_exceeded():
                return {
                    'allowed': False,
                    'error': f'{quota.get_quota_type_display()}配额已超限'
                }
        
        return {'allowed': True}
    
    def _update_quota(self, model: AIModel, user, record: ModelCallRecord):
        """更新配额使用量"""
        if not user:
            return
        
        quotas = ModelQuota.objects.filter(
            model=model,
            user=user,
            is_active=True
        )
        
        for quota in quotas:
            quota.used_calls = F('used_calls') + 1
            quota.used_tokens = F('used_tokens') + record.total_tokens
            quota.used_cost = F('used_cost') + record.cost
            quota.save(update_fields=['used_calls', 'used_tokens', 'used_cost'])
    
    def _create_call_record(
        self,
        model: AIModel,
        session_id: str,
        user,
        input_text: str,
        parameters: Dict,
        result: Dict,
        response_time: float,
        request_id: str,
        ip_address: str,
        user_agent: str
    ) -> ModelCallRecord:
        """创建调用记录"""
        status = 'success' if result.get('success') else 'failed'
        
        return ModelCallRecord.objects.create(
            model=model,
            session_id=session_id,
            user=user,
            input_text=input_text,
            parameters=parameters,
            output_text=result.get('output_text', ''),
            status=status,
            error_message=result.get('error', ''),
            input_tokens=result.get('input_tokens', 0),
            output_tokens=result.get('output_tokens', 0),
            response_time=response_time,
            cost=result.get('cost', 0),
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        timestamp = str(time.time())
        random_str = str(random.randint(1000, 9999))
        return hashlib.md5(f"{timestamp}_{random_str}".encode()).hexdigest()[:16]


class LoadBalancerService:
    """负载均衡服务"""
    
    def __init__(self):
        self.model_call_service = ModelCallService()
        self.round_robin_counters = {}
    
    async def call_with_load_balancer(
        self,
        load_balancer: ModelLoadBalancer,
        input_text: str,
        parameters: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """通过负载均衡器调用模型"""
        
        # 获取健康的模型
        healthy_models = self._get_healthy_models(load_balancer)
        
        if not healthy_models:
            return {
                'success': False,
                'error': '没有可用的健康模型',
                'error_type': 'no_healthy_models'
            }
        
        # 根据策略选择模型
        selected_model = self._select_model(load_balancer, healthy_models)
        
        retries = 0
        max_retries = load_balancer.max_retries
        
        while retries <= max_retries:
            try:
                result = await self.model_call_service.call_model(
                    model=selected_model,
                    input_text=input_text,
                    parameters=parameters,
                    **kwargs
                )
                
                if result['success']:
                    return result
                
                # 如果失败且启用故障转移
                if load_balancer.enable_fallback and retries < max_retries:
                    # 标记模型为不健康
                    self._mark_model_unhealthy(load_balancer, selected_model)
                    
                    # 重新获取健康模型
                    healthy_models = self._get_healthy_models(load_balancer)
                    if healthy_models:
                        selected_model = self._select_model(load_balancer, healthy_models)
                        retries += 1
                        
                        # 等待重试延迟
                        if load_balancer.retry_delay > 0:
                            await asyncio.sleep(load_balancer.retry_delay)
                        continue
                
                return result
                
            except Exception as e:
                logger.error(f"负载均衡调用失败: {str(e)}")
                
                if retries < max_retries and load_balancer.enable_fallback:
                    self._mark_model_unhealthy(load_balancer, selected_model)
                    retries += 1
                    
                    if load_balancer.retry_delay > 0:
                        await asyncio.sleep(load_balancer.retry_delay)
                    continue
                
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'load_balancer_failed'
                }
        
        return {
            'success': False,
            'error': f'重试{max_retries}次后仍然失败',
            'error_type': 'max_retries_exceeded'
        }
    
    def _get_healthy_models(self, load_balancer: ModelLoadBalancer) -> List[Tuple[AIModel, int]]:
        """获取健康的模型及其权重"""
        weights = ModelWeight.objects.filter(
            load_balancer=load_balancer,
            model__is_active=True,
            is_healthy=True,
            weight__gt=0
        ).select_related('model')
        
        return [(weight.model, weight.weight) for weight in weights]
    
    def _select_model(self, load_balancer: ModelLoadBalancer, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """根据策略选择模型"""
        if load_balancer.strategy == 'round_robin':
            return self._round_robin_select(load_balancer, healthy_models)
        elif load_balancer.strategy == 'weighted':
            return self._weighted_select(healthy_models)
        elif load_balancer.strategy == 'random':
            return self._random_select(healthy_models)
        elif load_balancer.strategy == 'least_connections':
            return self._least_connections_select(healthy_models)
        elif load_balancer.strategy == 'response_time':
            return self._response_time_select(healthy_models)
        elif load_balancer.strategy == 'cost_optimized':
            return self._cost_optimized_select(healthy_models)
        else:
            return healthy_models[0][0]  # 默认选择第一个
    
    def _round_robin_select(self, load_balancer: ModelLoadBalancer, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """轮询选择"""
        lb_id = load_balancer.id
        if lb_id not in self.round_robin_counters:
            self.round_robin_counters[lb_id] = 0
        
        index = self.round_robin_counters[lb_id] % len(healthy_models)
        self.round_robin_counters[lb_id] += 1
        
        return healthy_models[index][0]
    
    def _weighted_select(self, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """加权选择"""
        total_weight = sum(weight for _, weight in healthy_models)
        random_weight = random.randint(1, total_weight)
        
        current_weight = 0
        for model, weight in healthy_models:
            current_weight += weight
            if random_weight <= current_weight:
                return model
        
        return healthy_models[0][0]
    
    def _random_select(self, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """随机选择"""
        return random.choice(healthy_models)[0]
    
    def _least_connections_select(self, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """最少连接选择"""
        # 简化实现：选择最近调用次数最少的模型
        model_calls = {}
        for model, _ in healthy_models:
            recent_calls = ModelCallRecord.objects.filter(
                model=model,
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).count()
            model_calls[model] = recent_calls
        
        return min(model_calls.keys(), key=lambda m: model_calls[m])
    
    def _response_time_select(self, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """响应时间优先选择"""
        # 选择平均响应时间最短的模型
        model_response_times = {}
        for model, _ in healthy_models:
            avg_response_time = ModelCallRecord.objects.filter(
                model=model,
                status='success',
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
            
            model_response_times[model] = avg_response_time
        
        return min(model_response_times.keys(), key=lambda m: model_response_times[m])
    
    def _cost_optimized_select(self, healthy_models: List[Tuple[AIModel, int]]) -> AIModel:
        """成本优化选择"""
        # 选择成本最低的模型
        cost_models = [(model, model.input_price_per_1k + model.output_price_per_1k) for model, _ in healthy_models]
        return min(cost_models, key=lambda x: x[1])[0]
    
    def _mark_model_unhealthy(self, load_balancer: ModelLoadBalancer, model: AIModel):
        """标记模型为不健康"""
        ModelWeight.objects.filter(
            load_balancer=load_balancer,
            model=model
        ).update(is_healthy=False, last_health_check=timezone.now())


class PerformanceMonitorService:
    """性能监控服务"""
    
    def update_daily_performance(self, date: datetime.date = None):
        """更新每日性能统计"""
        if not date:
            date = timezone.now().date()
        
        # 获取所有活跃模型
        models = AIModel.objects.filter(is_active=True)
        
        for model in models:
            # 获取当日调用记录
            records = ModelCallRecord.objects.filter(
                model=model,
                created_at__date=date
            )
            
            if not records.exists():
                continue
            
            # 计算统计数据
            total_calls = records.count()
            successful_calls = records.filter(status='success').count()
            failed_calls = total_calls - successful_calls
            
            # Token统计
            total_input_tokens = sum(r.input_tokens for r in records)
            total_output_tokens = sum(r.output_tokens for r in records)
            total_tokens = total_input_tokens + total_output_tokens
            
            # 性能指标
            successful_records = records.filter(status='success')
            if successful_records.exists():
                avg_response_time = sum(r.response_time for r in successful_records) / successful_records.count()
            else:
                avg_response_time = 0.0
            
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0.0
            
            # 成本统计
            total_cost = sum(r.cost for r in records)
            avg_cost_per_call = total_cost / total_calls if total_calls > 0 else 0
            
            # 更新或创建性能记录
            performance, created = ModelPerformance.objects.update_or_create(
                model=model,
                date=date,
                defaults={
                    'total_calls': total_calls,
                    'successful_calls': successful_calls,
                    'failed_calls': failed_calls,
                    'total_input_tokens': total_input_tokens,
                    'total_output_tokens': total_output_tokens,
                    'total_tokens': total_tokens,
                    'average_response_time': avg_response_time,
                    'success_rate': success_rate,
                    'total_cost': total_cost,
                    'average_cost_per_call': avg_cost_per_call
                }
            )
            
            logger.info(f"更新模型 {model.name} 在 {date} 的性能统计")
    
    def get_model_health_status(self, model: AIModel) -> Dict[str, Any]:
        """获取模型健康状态"""
        # 获取最近1小时的调用记录
        recent_records = ModelCallRecord.objects.filter(
            model=model,
            created_at__gte=timezone.now() - timedelta(hours=1)
        )
        
        if not recent_records.exists():
            return {
                'status': 'unknown',
                'message': '暂无调用数据'
            }
        
        # 计算成功率
        total_calls = recent_records.count()
        successful_calls = recent_records.filter(status='success').count()
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        # 计算平均响应时间
        successful_records = recent_records.filter(status='success')
        if successful_records.exists():
            avg_response_time = sum(r.response_time for r in successful_records) / successful_records.count()
        else:
            avg_response_time = 0
        
        # 判断健康状态
        if success_rate >= 95 and avg_response_time < 5.0:
            status = 'healthy'
            message = '运行正常'
        elif success_rate >= 80 and avg_response_time < 10.0:
            status = 'warning'
            message = '性能略有下降'
        else:
            status = 'unhealthy'
            message = '性能异常，需要关注'
        
        return {
            'status': status,
            'message': message,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_calls': total_calls
        } 