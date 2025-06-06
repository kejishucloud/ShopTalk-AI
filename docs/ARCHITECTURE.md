# SmartTalk AI 系统架构文档

## 概述

SmartTalk AI 是一个基于Django的多平台AI智能客服系统，采用微服务架构设计，支持多个电商和社交平台的自动化客服功能。

## 系统架构

### 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   管理后台      │    │   移动端应用    │
│   (React)       │    │   (Django Admin)│    │   (可选)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   API网关       │
                    │   (Django REST) │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户管理      │    │   AI模型管理    │    │   平台集成      │
│   (apps.users)  │    │ (apps.ai_models)│    │ (apps.platforms)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   知识库管理    │    │   对话管理      │    │   数据分析      │
│ (apps.knowledge)│    │(apps.conversations)│  │ (apps.analytics)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AI引擎        │
                    │   (ai_engine)   │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   平台适配器    │    │   消息队列      │    │   数据存储      │
│(platform_adapters)│  │   (Celery)      │    │ (PostgreSQL)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件

#### 1. Django后端 (backend/)
- **用户管理** (apps.users): 用户认证、权限管理、用户配置
- **AI模型管理** (apps.ai_models): AI服务提供商、模型配置、使用日志
- **平台集成** (apps.platforms): 平台账号、自动回复规则、消息模板
- **知识库管理** (apps.knowledge): 商品信息、FAQ、话术模板、文档管理
- **对话管理** (apps.conversations): 对话会话、消息记录、AI代理配置
- **数据分析** (apps.analytics): 性能指标、使用统计、报表生成

#### 2. AI引擎 (ai_engine/)
- **智能代理** (agent.py): 核心AI客服代理逻辑
- **知识搜索** (knowledge_search.py): 向量搜索、语义匹配
- **意图识别** (intent_recognition.py): 用户意图分析
- **情感分析** (sentiment_analysis.py): 客户情感识别
- **回复生成** (response_generator.py): 智能回复生成
- **模型提供商** (model_providers/): 各种AI模型的统一接口

#### 3. 平台适配器 (platform_adapters/)
- **基础适配器** (base.py): 平台适配器抽象基类
- **电商平台**: 淘宝、京东、拼多多、抖店等
- **社交平台**: 小红书、微信、微博等
- **客服平台**: 千牛、京麦等

#### 4. 前端界面 (frontend/)
- **管理界面**: 系统配置、用户管理、数据监控
- **客服工作台**: 对话管理、知识库查询、人工接管
- **数据看板**: 性能指标、统计报表、趋势分析

## 数据流程

### 1. 消息处理流程

```
客户消息 → 平台适配器 → 消息队列 → AI代理 → 知识库搜索 → 回复生成 → 平台适配器 → 客户
```

详细步骤：
1. 客户在平台发送消息
2. 平台适配器接收消息并标准化
3. 消息进入Celery队列异步处理
4. AI代理分析消息（意图识别、情感分析）
5. 搜索相关知识库内容
6. 生成智能回复
7. 通过平台适配器发送回复

### 2. 知识库更新流程

```
文档上传 → 内容解析 → 文本分块 → 向量化 → 存储到向量数据库
```

### 3. 人工接管流程

```
AI置信度低 → 触发接管条件 → 通知人工客服 → 人工处理 → 更新知识库
```

## 技术栈

### 后端技术
- **框架**: Django 4.2 + Django REST Framework
- **数据库**: PostgreSQL (主数据库) + Redis (缓存)
- **消息队列**: Celery + Redis
- **AI模型**: OpenAI GPT、百度文心、阿里通义千问、智谱ChatGLM
- **向量搜索**: Sentence Transformers + 自定义向量存储
- **自动化**: Selenium (平台自动化)

### 前端技术
- **框架**: React 18 + TypeScript
- **UI库**: Material-UI
- **状态管理**: React Context + Hooks
- **图表**: Recharts
- **实时通信**: Socket.IO

### 部署技术
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx + Gunicorn
- **监控**: Sentry (错误监控)
- **日志**: Django Logging + ELK Stack (可选)

## 安全设计

### 1. 认证授权
- JWT Token认证
- 基于角色的权限控制 (RBAC)
- API访问频率限制

### 2. 数据安全
- 敏感数据加密存储
- API密钥安全管理
- 数据库连接加密

### 3. 平台安全
- 防止自动化检测的反爬虫策略
- 账号安全验证
- 异常行为监控

## 扩展性设计

### 1. 水平扩展
- 无状态服务设计
- 数据库读写分离
- 缓存层优化

### 2. 功能扩展
- 插件化平台适配器
- 可配置的AI模型切换
- 自定义知识库类型

### 3. 性能优化
- 异步消息处理
- 向量搜索优化
- 缓存策略优化

## 监控与运维

### 1. 系统监控
- 服务健康检查
- 性能指标监控
- 错误日志收集

### 2. 业务监控
- 对话质量评估
- 客户满意度统计
- AI模型性能分析

### 3. 运维自动化
- 自动化部署
- 数据备份策略
- 故障恢复机制

## 开发规范

### 1. 代码规范
- PEP 8 Python代码规范
- ESLint + Prettier 前端代码规范
- Git提交信息规范

### 2. 测试策略
- 单元测试覆盖率 > 80%
- 集成测试
- 端到端测试

### 3. 文档规范
- API文档 (Swagger)
- 代码注释
- 部署文档 