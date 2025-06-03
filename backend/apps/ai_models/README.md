# AI模型管理功能

ShopTalk-AI系统的AI模型管理模块，支持多种AI模型的配置、调用、监控和统计。

## 功能特性

### 1. 模型提供商管理
- 支持多种AI提供商：OpenAI、Anthropic、Azure OpenAI、Google AI、百度千帆、阿里云通义千问、腾讯混元等
- 自定义API支持
- 提供商配置管理

### 2. AI模型配置
- 模型参数配置（温度、Token限制、Top-p等）
- 定价信息管理
- 能力标签管理
- 优先级和状态控制
- API密钥安全存储

### 3. 模型调用服务
- 统一的模型调用接口
- 异步调用支持
- 自动成本计算
- 调用记录详细追踪
- 错误处理和重试机制

### 4. 负载均衡
- 多种均衡策略：轮询、加权、随机、最少连接、响应时间优先、成本优化
- 故障转移支持
- 健康检查机制
- 动态权重调整

### 5. 配额管理
- 多维度配额控制：调用次数、Token数量、成本
- 按用户、按模型的配额限制
- 自动配额重置
- 超限保护

### 6. 性能监控
- 实时健康状态监控
- 性能指标统计
- 成功率、响应时间、成本分析
- 趋势数据分析

## API接口

### 模型调用
```bash
# 调用指定模型
POST /api/v1/ai-models/models/call/
{
    "model_id": 1,
    "input_text": "你好，请介绍一下你自己",
    "temperature": 0.7,
    "max_tokens": 1000,
    "session_id": "chat_session_123"
}

# 响应
{
    "success": true,
    "output_text": "您好！我是一个AI助手...",
    "input_tokens": 15,
    "output_tokens": 45,
    "total_tokens": 60,
    "response_time": 1.23,
    "cost": 0.000012,
    "request_id": "req_abc123"
}
```

### 模型对比
```bash
# 多模型对比测试
POST /api/v1/ai-models/models/compare/
{
    "model_ids": [1, 2, 3],
    "input_text": "请解释人工智能的发展趋势",
    "parameters": {
        "temperature": 0.8,
        "max_tokens": 500
    }
}
```

### 负载均衡调用
```bash
# 通过负载均衡器调用
POST /api/v1/ai-models/load-balancers/1/call/
{
    "input_text": "分析这段文本的情感倾向",
    "temperature": 0.5
}
```

### 模型健康检查
```bash
# 获取模型健康状态
GET /api/v1/ai-models/models/1/health/

# 响应
{
    "model_id": 1,
    "model_name": "GPT-3.5-Turbo",
    "health_status": {
        "status": "healthy",
        "message": "运行正常",
        "success_rate": 98.5,
        "avg_response_time": 1.2,
        "total_calls": 1500
    },
    "is_active": true
}
```

### 性能统计
```bash
# 获取调用统计
GET /api/v1/ai-models/call-records/statistics/?model_id=1&date_from=2024-01-01

# 获取性能趋势
GET /api/v1/ai-models/performance/trends/?model_id=1&days=30
```

### 配额管理
```bash
# 获取用户配额
GET /api/v1/ai-models/quotas/my_quotas/

# 重置配额
POST /api/v1/ai-models/quotas/1/reset/
```

## 配置示例

### 1. 添加OpenAI模型
```python
# 创建提供商
provider = AIModelProvider.objects.create(
    name="OpenAI",
    provider_type="openai",
    base_url="https://api.openai.com/v1",
    is_active=True
)

# 创建模型
model = AIModel.objects.create(
    provider=provider,
    name="GPT-3.5-Turbo",
    model_id="gpt-3.5-turbo",
    model_type="chat",
    capabilities=["conversation", "text_generation"],
    max_tokens=4096,
    context_window=4096,
    default_temperature=0.7,
    input_price_per_1k=0.001,
    output_price_per_1k=0.002,
    api_key="your-openai-api-key",
    is_active=True,
    priority=10
)
```

### 2. 配置负载均衡器
```python
# 创建负载均衡器
balancer = ModelLoadBalancer.objects.create(
    name="主要对话模型组",
    strategy="weighted",
    enable_fallback=True,
    max_retries=3,
    health_check_enabled=True
)

# 添加模型权重
ModelWeight.objects.create(
    load_balancer=balancer,
    model=gpt35_model,
    weight=70
)
ModelWeight.objects.create(
    load_balancer=balancer,
    model=claude_model,
    weight=30
)
```

### 3. 设置用户配额
```python
# 设置每日配额
ModelQuota.objects.create(
    model=model,
    user=user,
    quota_type="daily",
    max_calls=1000,
    max_tokens=100000,
    max_cost=10.00,
    reset_at=timezone.now() + timedelta(days=1)
)
```

## 定时任务

系统包含以下定时任务：

1. **性能统计更新** (`update_daily_model_performance`)
   - 执行时间：每天凌晨2点
   - 功能：更新所有模型的每日性能统计

2. **配额重置** (`reset_model_quotas`)
   - 执行时间：根据配额类型自动执行
   - 功能：重置到期的配额使用量

3. **健康检查** (`health_check_models`)
   - 执行时间：每5分钟
   - 功能：检查所有模型的健康状态

4. **记录清理** (`cleanup_old_call_records`)
   - 执行时间：每天凌晨3点
   - 功能：清理30天前的调用记录

5. **成本报告** (`generate_cost_report`)
   - 执行时间：每周执行
   - 功能：生成模型使用成本统计报告

## 使用场景

### 1. 智能客服对话
```python
# 在智能体中使用AI模型
from apps.ai_models.services import ModelCallService

service = ModelCallService()
result = await service.call_model(
    model=chatbot_model,
    input_text=user_message,
    session_id=chat_session_id,
    user=current_user
)

if result['success']:
    bot_response = result['output_text']
    # 处理回复...
```

### 2. 多模型A/B测试
```python
# 使用负载均衡器进行A/B测试
from apps.ai_models.services import LoadBalancerService

service = LoadBalancerService()
result = await service.call_with_load_balancer(
    load_balancer=ab_test_balancer,
    input_text=test_prompt,
    parameters={'temperature': 0.8}
)
```

### 3. 成本优化
```python
# 根据成本选择最经济的模型
models = AIModel.objects.filter(
    capabilities__contains=['conversation'],
    is_active=True
).order_by('input_price_per_1k', 'output_price_per_1k')

cheapest_model = models.first()
```

## 监控和报警

- 模型健康状态监控
- 成本超限报警
- 性能下降通知
- 配额耗尽提醒
- 错误率过高报警

## 扩展性

- 支持新的AI提供商
- 自定义负载均衡策略
- 插件化的模型适配器
- 可配置的性能指标
- 灵活的配额策略

## 安全考虑

- API密钥加密存储
- 调用记录脱敏
- 访问权限控制
- 审计日志记录
- 敏感数据保护 