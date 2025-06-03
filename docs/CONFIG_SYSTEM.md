# ShopTalk-AI 配置系统使用指南

## 概述

ShopTalk-AI 采用了分层配置管理系统，将配置分为两个层次：

1. **核心系统配置**：存储在环境变量中（`config.env`），包括数据库、缓存、文件存储等基础设施配置
2. **业务配置**：存储在数据库中，包括AI模型、电商平台、智能体等业务相关配置，可通过Web界面动态管理

## 配置分类

### 核心系统配置（环境变量）

这些配置存储在 `config.env` 文件中，需要重启服务才能生效：

- **基础配置**：DEBUG、SECRET_KEY、ALLOWED_HOSTS等
- **数据库配置**：PostgreSQL连接信息
- **缓存配置**：Redis连接信息
- **文件存储配置**：本地存储和云存储设置
- **安全配置**：加密密钥、JWT配置等
- **邮件配置**：SMTP服务器设置
- **监控配置**：日志、性能监控等

### 业务配置（数据库）

这些配置存储在数据库中，可通过Web界面实时修改：

#### 1. AI模型配置
- **OpenAI配置**：API密钥、基础URL、模型选择
- **Anthropic Claude配置**：API密钥、模型选择
- **智谱AI配置**：API密钥、模型选择
- **阿里通义千问配置**：API密钥、模型选择
- **百度文心一言配置**：API密钥、密钥配置
- **本地AI模型配置**：启用状态、服务URL

#### 2. 电商平台配置
- **淘宝配置**：启用状态、用户名、密码
- **京东配置**：启用状态、用户名、密码
- **拼多多配置**：启用状态、用户名、密码

#### 3. 社交平台配置
- **小红书配置**：启用状态、用户名、密码
- **抖音配置**：启用状态、用户名、密码
- **微信配置**：启用状态、App ID、App Secret

#### 4. 智能体配置
- **情感分析配置**：启用状态、模型选择、阈值设置
- **意图识别配置**：启用状态、模型选择
- **多媒体处理配置**：OCR、语音转文字等

#### 5. 浏览器自动化配置
- **基础设置**：无头模式、用户数据目录
- **反检测设置**：启用状态、代理配置
- **指纹浏览器**：AdsPower集成配置

#### 6. 知识库配置
- **向量数据库**：类型选择、连接信息
- **嵌入模型**：模型选择、维度设置
- **RAG集成**：RAGFlow配置

## 使用方法

### 1. 通过Web界面管理

访问系统配置管理页面：`/system-config`

- 选择配置分类标签
- 在对应的配置组中修改配置项
- 点击"保存配置"按钮提交更改
- 配置会实时生效，无需重启服务

### 2. 通过代码获取配置

```python
from apps.system_config.services import get_config, get_ai_config, get_platform_config

# 获取单个配置
api_key = get_config('OPENAI_API_KEY')
sentiment_enabled = get_config('SENTIMENT_ENABLED', False)

# 获取AI模型配置
openai_config = get_ai_config('openai')
# 返回: {'OPENAI_API_KEY': '...', 'OPENAI_BASE_URL': '...', 'OPENAI_MODEL': '...'}

# 获取平台配置
taobao_config = get_platform_config('taobao')
# 返回: {'TAOBAO_ENABLED': True, 'TAOBAO_USERNAME': '...', 'TAOBAO_PASSWORD': '...'}

# 检查平台是否启用
if is_platform_enabled('taobao'):
    # 执行淘宝相关操作
    pass
```

### 3. 通过代码设置配置

```python
from apps.system_config.services import set_config, ConfigService

# 设置单个配置
set_config('OPENAI_API_KEY', 'your-new-api-key')

# 批量设置配置
configs = {
    'OPENAI_API_KEY': 'new-key',
    'OPENAI_MODEL': 'gpt-4',
    'SENTIMENT_ENABLED': True
}
results = ConfigService.batch_set_configs(configs)
```

## 配置类型说明

系统支持以下配置类型：

- **string**：字符串类型
- **integer**：整数类型
- **float**：浮点数类型
- **boolean**：布尔值类型
- **json**：JSON对象类型
- **password**：密码类型（加密存储）
- **email**：邮箱地址类型
- **url**：URL地址类型
- **text**：长文本类型
- **choice**：选择类型（下拉选项）

## 安全考虑

1. **敏感信息加密**：密码、API密钥等敏感配置会自动加密存储
2. **权限控制**：只有管理员用户可以修改配置
3. **操作日志**：所有配置修改操作都会记录日志
4. **缓存机制**：配置值会缓存5分钟，提高访问性能

## 初始化配置

首次部署时，运行以下命令初始化配置数据：

```bash
cd backend
python manage.py init_configs
```

这会创建默认的配置分类、配置组和配置项。

## 配置迁移

如果需要从环境变量迁移到数据库配置：

1. 在数据库中创建对应的配置项
2. 将环境变量的值设置到数据库配置中
3. 修改代码使用新的配置服务
4. 从环境变量文件中移除已迁移的配置

## 最佳实践

1. **分类管理**：将相关配置归类到同一分类和组中
2. **描述完整**：为每个配置项提供清晰的描述信息
3. **默认值**：为配置项设置合理的默认值
4. **验证规则**：使用适当的配置类型和验证规则
5. **缓存策略**：合理使用缓存，平衡性能和实时性

## 故障排除

### 配置不生效
1. 检查配置项是否启用（`is_active=True`）
2. 清除配置缓存：`ConfigService.clear_cache()`
3. 检查配置值格式是否正确

### 配置丢失
1. 检查数据库连接是否正常
2. 确认配置项是否被误删
3. 查看操作日志确定问题原因

### 性能问题
1. 检查缓存是否正常工作
2. 避免频繁的配置查询
3. 使用批量获取接口减少数据库查询

## API接口

系统提供完整的REST API接口用于配置管理：

- `GET /api/v1/system-config/categories/` - 获取配置分类列表
- `GET /api/v1/system-config/categories/{id}/detail_with_configs/` - 获取分类详情
- `GET /api/v1/system-config/configs/` - 获取配置列表
- `POST /api/v1/system-config/configs/batch_update/` - 批量更新配置
- `GET /api/v1/system-config/configs/get_by_key/` - 根据key获取配置
- `POST /api/v1/system-config/configs/set_by_key/` - 根据key设置配置

详细的API文档可通过 `/api/docs/` 访问。 