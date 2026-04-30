# OpenClaw-Harness 开发指南

## 项目概述

OpenClaw-Harness 是一个多智能体协作平台，采用前后端分离架构。

## 开发规范

### 代码风格
- **后端**: 遵循 PEP 8，使用 `ruff` 进行代码检查
- **前端**: 使用 ESLint + Prettier，遵循 Next.js 最佳实践

### 提交规范
```
<type>: <subject>

<body>
```

类型：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

### 分支策略
- `main`: 主分支，保持稳定
- `feature/*`: 功能分支
- `fix/*`: 修复分支

## 模块说明

### Backend (`backend/`)
- `app/api/`: RESTful API 端点（agents, sessions, tasks, skills 等）
- `app/models/`: SQLAlchemy ORM 模型
- `app/services/`: 业务逻辑服务
- `app/core/`: 核心基础设施（数据库、安全、异步工具）
- `openharness/`: OpenHarness CLI 集成

### Frontend (`frontend/`)
- `app/`: Next.js App Router 页面
- `components/`: 可复用 React 组件
- `lib/`: 工具函数和 API 客户端
- `stores/`: Zustand 状态管理

## 环境配置

1. 复制 `.env.example` 为 `.env`
2. 配置数据库和密钥
3. 运行 `alembic upgrade head` 初始化数据库

## 常用命令

```bash
# 启动开发环境
./start.sh

# 仅启动后端
cd backend && python -m app.main

# 仅启动前端
cd frontend && npm run dev

# 运行测试
pytest                    # 后端
npm test                  # 前端

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## 贡献指南

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'feat: add xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 创建 Pull Request
