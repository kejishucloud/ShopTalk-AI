# ShopTalk AI 前端系统

## 项目简介

ShopTalk AI 是一个功能强大的智能客服管理平台前端系统，采用现代化的技术栈构建，提供科技感十足的用户界面和丰富的交互功能。

### 技术栈

- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts + Vue-ECharts
- **样式**: SCSS
- **HTTP 客户端**: Axios
- **实时通信**: Socket.IO (可选)

### 主要功能模块

1. **登录与个人中心**
   - 用户登录认证
   - 个人信息管理
   - 权限控制

2. **智能对话系统**
   - 实时聊天界面
   - 多会话管理
   - 文件上传支持
   - 快捷话术
   - 模式切换 (知识库/大模型/混合)

3. **标签与关键词管理**
   - 标签CRUD操作
   - 关键词触发规则
   - 优先级管理

4. **知识库管理**
   - 话术知识库
   - 产品知识库
   - 批量导入
   - 向量同步

5. **大模型管理**
   - 模型配置
   - 测试功能
   - 状态监控

6. **平台接入管理**
   - 多渠道接入
   - 流量监控
   - 状态管理

7. **运营监控与分析**
   - 数据统计
   - 图表分析
   - 报表导出

## 安装使用

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install

# 或使用 pnpm
pnpm install
```

### 开发环境

```bash
# 启动开发服务器
npm run dev

# 或
yarn dev
```

访问 http://localhost:3000 查看应用

### 生产构建

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 代码规范

```bash
# 代码检查
npm run lint

# 代码格式化
npm run format
```

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API 接口
│   │   ├── auth.ts        # 认证相关
│   │   └── request.ts     # HTTP 请求配置
│   ├── components/        # 公共组件
│   ├── layouts/           # 布局组件
│   │   └── MainLayout.vue # 主布局
│   ├── router/            # 路由配置
│   │   └── index.ts       # 路由定义
│   ├── stores/            # 状态管理
│   │   └── user.ts        # 用户状态
│   ├── styles/            # 样式文件
│   │   ├── index.scss     # 全局样式
│   │   └── variables.scss # 样式变量
│   ├── types/             # TypeScript 类型定义
│   │   └── user.ts        # 用户类型
│   ├── views/             # 页面组件
│   │   ├── Login.vue      # 登录页面
│   │   ├── Dashboard.vue  # 仪表盘
│   │   ├── Chat.vue       # 聊天界面
│   │   └── ...            # 其他页面
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── index.html             # HTML 模板
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
├── vite.config.ts         # Vite 配置
└── README.md              # 项目说明
```

## 设计特色

### 科技感 UI 设计

- **深色主题**: 采用深蓝色背景配色方案
- **渐变效果**: 大量使用科技感渐变色
- **动画交互**: 丰富的CSS3动画和过渡效果
- **霓虹发光**: 特殊文字和边框的霓虹灯效果
- **毛玻璃**: 现代化的毛玻璃材质效果

### 响应式设计

- 兼容 PC、平板、手机等不同屏幕尺寸
- 灵活的网格布局系统
- 自适应的组件尺寸

### 组件化开发

- 高度可复用的组件设计
- 统一的设计语言
- 模块化的代码结构

## API 接口说明

### 后端接口地址配置

在 `vite.config.ts` 中配置代理：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Django 后端地址
      changeOrigin: true,
      secure: false
    }
  }
}
```

### 主要接口

- **认证**: `/api/auth/`
- **用户管理**: `/api/users/`
- **聊天**: `/api/conversations/`
- **知识库**: `/api/knowledge/`
- **模型管理**: `/api/models/`
- **平台管理**: `/api/platforms/`
- **分析统计**: `/api/analytics/`

## 开发指南

### 添加新页面

1. 在 `src/views/` 中创建页面组件
2. 在 `src/router/index.ts` 中添加路由配置
3. 在主布局的侧边栏中添加菜单项

### 状态管理

使用 Pinia 进行状态管理，在 `src/stores/` 目录下创建对应的 store。

### 样式规范

- 使用 SCSS 预处理器
- 遵循 BEM 命名规范
- 使用全局样式变量

### 组件开发

- 使用 Composition API
- TypeScript 类型声明
- 响应式设计原则

## 部署说明

### 环境变量

根据不同环境配置相应的环境变量：

```bash
# 开发环境
VITE_API_BASE_URL=http://localhost:8000

# 生产环境  
VITE_API_BASE_URL=https://api.yourdomain.com
```

### Docker 部署

```dockerfile
FROM node:16-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系我们

如有问题或建议，请联系：

- 邮箱: support@shoptalk-ai.com
- 官网: https://www.shoptalk-ai.com
- 文档: https://docs.shoptalk-ai.com 