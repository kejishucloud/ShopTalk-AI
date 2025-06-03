# SmartTalk AI - 智能客服系统

🤖 一个功能强大的多平台AI智能客服系统，支持淘宝、京东、拼多多、抖音、小红书等主流电商和社交平台。

## ✨ 核心特性

### 🎯 多平台支持
- **电商平台**: 淘宝、京东、拼多多
- **社交平台**: 小红书、抖音
- **扩展性**: 可轻松添加新平台适配器

### 🧠 AI智能引擎
- **多模型支持**: OpenAI GPT、百度文心、阿里通义千问、智谱ChatGLM
- **智能对话**: 意图识别、情感分析、上下文理解
- **知识库**: 商品信息、FAQ、话术模板、向量搜索

### 🛠 技术架构
- **后端框架**: Django 4.2 + DRF
- **数据库**: PostgreSQL + Redis
- **异步任务**: Celery
- **浏览器自动化**: Playwright (支持反检测)
- **AI模型**: 统一接口，支持多种AI服务

### 📊 管理功能
- **用户管理**: 多角色权限控制
- **对话管理**: 完整的会话记录和分析
- **数据分析**: 实时监控和统计报表
- **知识库管理**: 可视化编辑和维护

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 16+ (前端开发)
- PostgreSQL 12+
- Redis 6+

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd SmartTalk-AI

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
python scripts/install_playwright.py
```

### 3. 配置环境

```bash
# 复制环境变量模板
cp backend/env_example.txt backend/.env

# 编辑环境变量
nano backend/.env
```

必需的环境变量：
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/smarttalk
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-api-key
```

### 4. 初始化数据库

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

### 5. 启动系统

```bash
# 方式1: 一键启动所有服务
python scripts/start_system.py

# 方式2: 手动启动各个服务
# 启动Django服务器
cd backend && python manage.py runserver

# 启动Celery工作进程
cd backend && python manage.py celery worker -l info

# 启动Celery定时任务
cd backend && python manage.py celery beat -l info
```

### 6. 访问系统

- **Web界面**: http://localhost:8000
- **管理后台**: http://localhost:8000/admin
- **API文档**: http://localhost:8000/api/docs

## 📱 平台配置

### 淘宝平台

```python
from platform_adapters.adapter_factory import PlatformAdapterFactory

# 配置淘宝适配器
taobao_config = {
    'platform': 'taobao',
    'username': 'your_username',
    'password': 'your_password',
    'headless': False,
    'user_data_dir': './browser_data/taobao'
}

# 创建适配器实例
factory = PlatformAdapterFactory()
adapter = factory.create_adapter('taobao', taobao_config)

# 初始化并使用
await adapter.initialize()
messages = await adapter.get_messages()
await adapter.send_message('user123', '您好，有什么可以帮助您的吗？')
```

### 小红书平台

```python
# 配置小红书适配器
xiaohongshu_config = {
    'platform': 'xiaohongshu',
    'headless': False,
    'user_data_dir': './browser_data/xiaohongshu'
}

adapter = factory.create_adapter('xiaohongshu', xiaohongshu_config)
await adapter.initialize()

# 发布内容
content = {
    'title': '产品推荐',
    'text': '这是一个很棒的产品...',
    'images': ['./images/product1.jpg'],
    'tags': ['好物推荐', '种草']
}
await adapter.publish_content(content)
```

### 京东平台

```python
# 配置京东适配器
jingdong_config = {
    'platform': 'jingdong',
    'shop_id': 'your_shop_id',
    'headless': False
}

adapter = factory.create_adapter('jingdong', jingdong_config)
await adapter.initialize()

# 获取订单信息
orders = await adapter.get_orders()
```

## 🤖 AI代理使用

### 基本配置

```python
from ai_engine.agent import SmartTalkAgent

# 创建AI代理
agent = SmartTalkAgent({
    'ai_model': 'openai',
    'model_name': 'gpt-3.5-turbo',
    'api_key': 'your-api-key',
    'knowledge_base_id': 'kb_001'
})

# 处理用户消息
response = await agent.process_message(
    user_id='user123',
    message='我想了解这个产品的价格',
    platform='taobao'
)
```

### 知识库集成

```python
# 添加商品信息到知识库
product_info = {
    'name': 'iPhone 15 Pro',
    'price': 7999,
    'description': '最新款iPhone...',
    'features': ['A17芯片', '钛金属边框', '三摄系统']
}

await agent.knowledge_base.add_product(product_info)

# 添加FAQ
faq = {
    'question': '支持什么支付方式？',
    'answer': '我们支持支付宝、微信支付、银行卡等多种支付方式。'
}

await agent.knowledge_base.add_faq(faq)
```

## 🔧 系统管理

### 检查系统状态

```bash
# 运行系统检查
python scripts/check_system.py
```

### 平台适配器管理

```bash
# 查看所有可用适配器
python -c "from platform_adapters.adapter_factory import PlatformAdapterFactory; print(PlatformAdapterFactory.list_adapters())"

# 测试特定平台适配器
python scripts/test_adapter.py --platform taobao
```

### 数据库管理

```bash
# 创建数据库备份
python manage.py dbbackup

# 恢复数据库
python manage.py dbrestore

# 清理过期数据
python manage.py cleanup_old_data --days 30
```

## 📊 监控和分析

### 实时监控

- **对话监控**: 实时查看客服对话状态
- **系统性能**: CPU、内存、数据库连接监控
- **错误日志**: 自动收集和分析错误信息

### 数据分析

- **对话统计**: 消息数量、响应时间、满意度
- **平台分析**: 各平台活跃度和转化率
- **AI效果**: 意图识别准确率、知识库命中率

## 🛡 安全特性

### 反检测机制

- **指纹浏览器**: 支持Adspower等指纹浏览器
- **User-Agent随机化**: 模拟真实用户行为
- **人性化操作**: 随机延迟和鼠标轨迹
- **代理支持**: HTTP/SOCKS代理轮换

### 数据安全

- **加密存储**: 敏感数据AES加密
- **访问控制**: 基于角色的权限管理
- **审计日志**: 完整的操作记录
- **备份策略**: 自动数据备份和恢复

## 🔌 扩展开发

### 添加新平台适配器

1. 继承基础适配器类：

```python
from platform_adapters.base import BasePlatformAdapter

class NewPlatformAdapter(BasePlatformAdapter):
    def __init__(self, config):
        super().__init__(config)
        self.platform_name = "new_platform"
    
    async def send_message(self, user_id: str, message: str) -> bool:
        # 实现发送消息逻辑
        pass
    
    async def get_messages(self, limit: int = 50) -> List[Dict]:
        # 实现获取消息逻辑
        pass
```

2. 注册到适配器工厂：

```python
# 在 adapter_factory.py 中添加
ADAPTER_CLASSES['new_platform'] = NewPlatformAdapter
```

### 自定义AI模型

```python
from ai_engine.models.base import BaseAIModel

class CustomAIModel(BaseAIModel):
    async def generate_response(self, prompt: str, context: Dict) -> str:
        # 实现自定义AI模型逻辑
        pass
```

## 📚 API文档

### REST API

- **用户管理**: `/api/users/`
- **对话管理**: `/api/conversations/`
- **知识库**: `/api/knowledge/`
- **平台管理**: `/api/platforms/`
- **分析报告**: `/api/analytics/`

### WebSocket API

- **实时消息**: `/ws/messages/`
- **系统状态**: `/ws/status/`
- **通知推送**: `/ws/notifications/`

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

- **文档**: [完整文档](docs/)
- **问题反馈**: [GitHub Issues](https://github.com/kejishucloud/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/kejishucloud/discussions)

## 🎯 路线图

- [ ] 支持更多AI模型（Claude、Gemini等）
- [ ] 移动端APP开发
- [ ] 语音对话功能
- [ ] 多语言支持
- [ ] 插件系统
- [ ] 云端部署方案

---

**SmartTalk AI** - 让AI客服更智能，让业务更高效！ 🚀 