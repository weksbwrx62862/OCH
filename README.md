# OpenClaw-Harness

OpenClaw-Harness 是一个多智能体协作平台，提供完整的后端 API 和前端界面，支持智能体管理、会话聊天、任务调度、技能管理、权限控制等功能。

## 项目结构

```
openclaw-harness/
├── backend/              # Python Flask 后端
│   ├── app/              # 主应用代码
│   │   ├── api/          # REST API 端点
│   │   ├── core/         # 核心工具（数据库、安全、异步）
│   │   ├── models/       # SQLAlchemy 数据模型
│   │   └── services/     # 业务服务层
│   ├── openharness/      # OpenHarness 集成模块
│   ├── tests/            # 测试用例
│   ├── requirements.txt  # Python 依赖
│   └── Dockerfile        # 后端容器镜像
├── frontend/             # Next.js 前端
│   ├── app/              # 页面路由
│   ├── components/       # React 组件
│   ├── lib/              # 工具库
│   └── package.json      # Node.js 依赖
├── docs/                 # 项目文档
├── docker-compose.yml    # Docker 编排配置
└── start.sh              # 快速启动脚本
```

## 技术栈

### 后端
- **框架**: Flask + Flask-SocketIO
- **数据库**: SQLAlchemy (SQLite/PostgreSQL)
- **迁移**: Alembic
- **认证**: JWT + bcrypt
- **缓存**: Redis
- **测试**: pytest

### 前端
- **框架**: Next.js 15 + React 19
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **测试**: Jest + React Testing Library

## 快速开始

### 使用启动脚本（推荐）

```bash
./start.sh
```

脚本会自动完成：
1. 创建 Python 虚拟环境
2. 安装后端依赖
3. 初始化数据库
4. 安装前端依赖
5. 启动后端（端口 8008）和前端（端口 3000）

### 手动启动

**后端:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.main
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

## Docker 部署

```bash
docker-compose up -d
```

服务启动后：
- 前端: http://localhost:3000
- 后端 API: http://localhost:8008
- API 文档: http://localhost:8008/docs

## 主要功能

- **智能体管理**: 创建、配置、管理 AI 智能体
- **会话系统**: 支持流式/非流式聊天，消息持久化
- **任务调度**: DAG 任务依赖管理，状态流转
- **技能系统**: 技能注册、发现、启用/禁用
- **权限控制**: RBAC 角色权限管理
- **渠道集成**: 支持多种消息渠道（钉钉、飞书、Slack 等）
- **MCP 支持**: Model Context Protocol 服务器管理
- **记忆系统**: 智能体记忆事实库

## 开发

```bash
# 运行后端测试
cd backend
pytest

# 运行前端测试
cd frontend
npm test

# 代码格式化
cd backend
ruff check .
cd frontend
npm run lint
```

## 环境变量

复制 `.env.example` 为 `.env` 并配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 | SQLite |
| `REDIS_URL` | Redis 连接 | - |
| `SECRET_KEY` | JWT 密钥 | 必填 |
| `ADMIN_PASSWORD` | 管理员密码 | 必填 |
| `CORS_ORIGINS` | 跨域白名单 | `["http://localhost:3000"]` |

## 许可证

MIT License
