<div align="center">

# 🔧 OpenClaw-Harness

**企业级智能体基础设施 — 安全沙箱 · 工具调度 · 代码执行**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Apache--2.0-green)
![GitHub Stars](https://img.shields.io/github/stars/weksbwrx62862/OCH?style=social)
![Last Commit](https://img.shields.io/github/last-commit/weksbwrx62862/OCH)

</div>

OpenClaw-Harness（OCH）是一个多智能体协作平台，基于 OpenHarness 核心框架构建，提供完整的后端 API 和现代化前端界面。平台支持智能体管理、实时会话聊天、DAG 任务调度、技能编排、RBAC 权限控制、MCP 服务器管理、多渠道集成等能力，旨在为企业和开发者提供一站式的 AI 智能体编排与协作解决方案。

---

## 目录

- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [功能详解](#功能详解)
- [API 概览](#api-概览)
- [环境变量](#环境变量)
- [开发指南](#开发指南)
- [Docker 部署](#docker-部署)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 核心特性

### 智能体管理
- 创建、配置、启停 AI 智能体（Agent）
- 支持系统提示词（System Prompt）、模型参数、工具绑定
- 智能体状态实时监控与生命周期管理

### 实时会话系统
- 基于 SSE（Server-Sent Events）的流式聊天体验
- 支持思考过程展示（thinking）、文本增量输出（text_delta）
- 工具调用可视化（tool_start / tool_end）
- 消息持久化存储与历史会话回溯

### DAG 任务调度
- 有向无环图（DAG）任务依赖管理
- 任务状态机：pending → running → completed / failed / cancelled
- 支持任务重试、超时控制、优先级调度
- 子任务并行执行与结果汇聚

### 技能与工具生态
- **43+ 内置工具**，涵盖 7 大类别：
  - 文件 I/O（读写、搜索、目录操作）
  - 网络（HTTP 请求、网页抓取）
  - 智能体（子智能体调用、模式切换）
  - 任务（任务创建、状态查询）
  - MCP（MCP 工具调用）
  - 记忆（记忆存储、检索）
- 技能（Skill）注册、发现、组合与版本管理
- 工具权限粒度控制

### 权限与安全
- RBAC（基于角色的访问控制）权限模型
- 路径规则引擎（Path Rules）实现细粒度 API 授权
- JWT Token 认证 + bcrypt 密码哈希
- 操作审计日志完整记录

### 多渠道集成
- 内置 12 种即时通讯渠道适配器：
  - 飞书（Feishu/Lark）
  - Slack
  - Telegram
  - Discord
  - 钉钉（DingTalk）
  - 企业微信
  - 以及更多...
- 统一消息收发接口，渠道无关的业务逻辑

### MCP 支持
- Model Context Protocol 服务器管理
- MCP 工具动态发现与调用
- 支持 stdio 与 SSE 两种传输模式

### 记忆系统
- 智能体记忆事实库（Memory Fact）
- 支持结构化记忆存储与语义检索
- 会话级与全局级记忆隔离

### 沙箱与插件
- 安全的代码执行沙箱环境
- 插件（Plugin）热插拔机制
- Hook 系统支持自定义扩展点

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Dashboard│ │  Chat   │ │ Agents  │ │ Tasks   │  ...      │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └─────────────┴─────────┴─────────────┘                │
│                         Next.js 15 + React 19                │
│                         Zustand + Tailwind CSS               │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP / WebSocket
┌─────────────────────────────┴───────────────────────────────┐
│                      API 网关层 (Backend API)                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ /agents │ │/sessions│ │ /tasks  │ │ /tools  │ │/skills │ │
│  │ /auth   │ │/channels│ │ /mcp    │ │/permissions│/audit │ │
│  │ /config │ │/plugins │ │ /sandbox│ │ /websocket │       │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬───┘ │
│       └─────────────┴─────────┴─────────────┴────────────┘   │
│                         Flask 3.0 + SocketIO                 │
│                         JWT Auth + CORS + Swagger            │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    业务服务层 (Services)                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │SessionService│ │Coordinator   │ │Permission    │         │
│  │              │ │Service       │ │Service       │         │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤         │
│  │ToolService   │ │SkillService  │ │PluginService │         │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤         │
│  │CacheService  │ │Subagent      │ │HookService   │         │
│  │              │ │Executor      │ │              │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                   OpenHarness 核心引擎                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ engine  │ │  tools  │ │channels │ │coordinator│ memory│ │
│  │permissions│ swarm  │ │sandbox  │ │  hooks   │ skills │ │
│  │  bridge │ │   mcp   │ │ services│ │  models  │  ...   │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│                                                              │
│  • 25+ 子包，100% 保留核心引擎能力                            │
│  • 双线程池调度（Scheduler + Executor）                       │
│  • CompactCache 工具输出压缩缓存                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                      数据持久层                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ PostgreSQL  │    │    Redis    │    │   SQLite    │     │
│  │  (主数据库)  │    │  (缓存/消息) │    │  (开发环境)  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│  SQLAlchemy Async ORM + Alembic 迁移                         │
└─────────────────────────────────────────────────────────────┘
```

更详细的架构说明请参阅 [docs/architecture.md](docs/architecture.md)。

---

## 技术栈

### 后端

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | Flask | 3.0+ | RESTful API 基础框架 |
| 实时通信 | Flask-SocketIO | 5.3+ | WebSocket 实时事件推送 |
| 数据库 ORM | SQLAlchemy | 2.0+ | 异步 ORM，支持 PostgreSQL / SQLite |
| 数据库迁移 | Alembic | 1.13+ | 自动化 schema 迁移 |
| 认证 | PyJWT + bcrypt | - | JWT Token + 密码哈希 |
| 缓存 | Redis + CompactCache | - | 分布式缓存与工具输出压缩 |
| 配置管理 | Pydantic-Settings | 2.0+ | 环境变量校验与类型安全 |
| API 文档 | Flask-RESTX / Swagger UI | - | 自动生成 API 文档 |
| 测试 | pytest + pytest-asyncio | - | 异步测试支持 |
| 代码检查 | ruff | - | PEP 8 规范与自动修复 |

### 前端

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Next.js | 15+ | App Router 模式 |
| UI 库 | React | 19+ | 函数组件 + Hooks |
| 样式 | Tailwind CSS | 3.4+ | 原子化 CSS + CSS 变量主题 |
| 状态管理 | Zustand | - | 轻量级全局状态 |
| 字体 | Inter + JetBrains Mono | - | 界面字体与等宽代码字体 |
| 图标 | Lucide React | - | 统一图标系统 |
| 构建 | Turbopack | - | 快速开发构建 |
| 测试 | Jest + React Testing Library | - | 组件与单元测试 |

---

## 项目结构

```
openclaw-harness/
├── backend/                          # Python 后端服务
│   ├── app/
│   │   ├── api/                      # REST API 路由（15 个蓝图）
│   │   │   ├── agents.py             # 智能体 CRUD 与运行控制
│   │   │   ├── sessions.py           # 会话管理与 SSE 流式聊天
│   │   │   ├── tasks.py              # DAG 任务调度与状态管理
│   │   │   ├── tools.py              # 工具注册、发现与调用
│   │   │   ├── skills.py             # 技能管理与组合
│   │   │   ├── permissions.py        # RBAC 权限与路径规则
│   │   │   ├── channels.py           # IM 渠道适配器管理
│   │   │   ├── mcp.py                # MCP 服务器管理
│   │   │   ├── memory.py             # 记忆事实库操作
│   │   │   ├── plugins.py            # 插件生命周期管理
│   │   │   ├── sandbox.py            # 沙箱执行环境
│   │   │   ├── config.py             # 动态配置管理
│   │   │   ├── audit.py              # 审计日志查询
│   │   │   ├── auth.py               # 认证与授权
│   │   │   └── websocket.py          # SocketIO 事件处理
│   │   ├── core/                     # 核心基础设施
│   │   │   ├── database.py           # 异步 SQLAlchemy 引擎
│   │   │   ├── security.py           # JWT 签发与验证
│   │   │   ├── exceptions.py         # 自定义异常体系
│   │   │   └── config.py             # Pydantic 配置类
│   │   ├── models/                   # 数据模型（10 个核心模型）
│   │   │   ├── agent.py              # Agent + ToolPermission
│   │   │   ├── session.py            # Session
│   │   │   ├── message.py            # Message + ToolResult
│   │   │   ├── task.py               # Task + TaskDependency
│   │   │   ├── team.py               # Team + TeamMember
│   │   │   ├── skill.py              # Skill
│   │   │   ├── memory_fact.py        # MemoryFact
│   │   │   ├── mcp_server.py         # MCPServer
│   │   │   ├── permission.py         # PermissionRule + AuditLog
│   │   │   └── plugin.py             # Plugin
│   │   └── services/                 # 业务服务层（9 个核心服务）
│   │       ├── session_service.py    # 会话业务逻辑
│   │       ├── coordinator_service.py # 协调器服务
│   │       ├── tool_service.py       # 工具执行与缓存
│   │       ├── skill_service.py      # 技能编排
│   │       ├── permission_service.py # 权限校验
│   │       ├── plugin_service.py     # 插件管理
│   │       ├── cache_service.py      # 压缩缓存
│   │       ├── subagent_executor.py  # 子智能体执行器
│   │       └── hook_service.py       # Hook 扩展点
│   ├── openharness/                  # OpenHarness CLI 集成
│   ├── tests/                        # 测试用例
│   ├── alembic/                      # 数据库迁移脚本
│   ├── requirements.txt              # Python 依赖
│   ├── Dockerfile                    # 后端容器镜像
│   └── .env.example                  # 环境变量模板
│
├── frontend/                         # Next.js 前端应用
│   ├── app/                          # App Router 页面
│   │   ├── page.tsx                  # Dashboard 仪表盘
│   │   ├── layout.tsx                # 根布局（AuthProvider + AppLayout）
│   │   ├── chat/                     # 实时聊天页
│   │   ├── agents/                   # 智能体管理页
│   │   ├── sessions/                 # 会话历史页
│   │   ├── tasks/                    # 任务调度页
│   │   ├── tools/                    # 工具浏览页
│   │   ├── skills/                   # 技能管理页
│   │   ├── swarm/                    # 群体智能页
│   │   ├── audit/                    # 审计日志页
│   │   ├── settings/                 # 系统设置页
│   │   └── login/                    # 登录页
│   ├── components/                   # React 组件
│   │   ├── layout/                   # 布局组件（Sidebar、Header）
│   │   ├── ui/                       # 基础 UI 组件
│   │   └── chat/                     # 聊天相关组件
│   ├── lib/                          # 工具库
│   │   └── api.ts                    # API 客户端封装
│   ├── stores/                       # Zustand 状态管理
│   │   └── appStore.ts               # 全局应用状态
│   ├── public/                       # 静态资源
│   ├── package.json                  # Node.js 依赖
│   ├── next.config.js                # Next.js 配置（API 代理）
│   ├── tailwind.config.ts            # Tailwind 主题配置
│   └── Dockerfile                    # 前端容器镜像
│
├── docs/                             # 项目文档
│   ├── architecture.md               # 架构设计文档
│   └── debugging-guide.md            # 调试指南
│
├── docker-compose.yml                # Docker Compose 编排
├── start.sh                          # 一键启动脚本
├── .env.example                      # 全局环境变量模板
└── README.md                         # 本文件
```

---

## 快速开始

### 方式一：一键启动脚本（推荐）

```bash
./start.sh
```

脚本将自动完成以下步骤：
1. 创建 Python 虚拟环境（`backend/.venv`）
2. 安装后端 Python 依赖
3. 初始化数据库（`alembic upgrade head`）
4. 安装前端 Node.js 依赖
5. 并行启动后端服务（端口 `8008`）和前端开发服务器（端口 `3000`）

### 方式二：手动启动

**1. 克隆仓库并进入目录**

```bash
cd openclaw-harness
```

**2. 启动后端**

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate
# 激活虚拟环境（Linux/macOS）
# source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，至少设置 SECRET_KEY 和 ADMIN_PASSWORD

# 初始化数据库
alembic upgrade head

# 启动服务
python -m app.main
```

后端服务默认监听 `http://localhost:8008`，API 文档地址 `http://localhost:8008/docs`。

**3. 启动前端**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器默认监听 `http://localhost:3000`。

### 方式三：Docker Compose 部署

```bash
# 启动所有服务（PostgreSQL + Redis + Backend + Frontend）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务映射：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Next.js 应用 |
| 后端 API | http://localhost:8008 | Flask REST API |
| API 文档 | http://localhost:8008/docs | Swagger UI |
| PostgreSQL | localhost:5433 | 主数据库 |
| Redis | localhost:6380 | 缓存与消息队列 |

---

## 功能详解

### 1. 智能体管理

智能体（Agent）是平台的核心执行单元。每个智能体包含：

- **基础配置**：名称、描述、图标、状态（active / inactive）
- **模型参数**：系统提示词（System Prompt）、温度系数、最大 Token 数
- **工具绑定**：可使用的工具列表与权限控制
- **记忆关联**：绑定的记忆事实库

通过前端 **Agents** 页面或 `/api/agents` 接口进行 CRUD 操作。

### 2. 会话与聊天

会话（Session）是用户与智能体的交互上下文：

- **创建会话**：选择智能体，初始化对话上下文
- **流式响应**：基于 SSE 的实时流式输出，支持：
  - `thinking`：展示智能体思考过程
  - `text_delta`：文本增量输出
  - `tool_start` / `tool_end`：工具调用开始与结束
  - `turn_complete`：本轮对话完成
  - `error`：错误信息
- **消息持久化**：所有消息存储于数据库，支持历史回溯
- **工具结果展示**：工具执行结果以结构化卡片形式呈现

### 3. DAG 任务调度

任务系统支持复杂的工作流编排：

- **任务定义**：名称、描述、执行命令、优先级、超时时间
- **依赖管理**：通过 `TaskDependency` 建立 DAG 依赖关系
- **状态流转**：
  ```
  pending → running → completed
                    → failed
                    → cancelled
  ```
- **调度策略**：支持并行执行无依赖任务，按拓扑顺序调度
- **子任务**：任务可拆分为多个子任务，独立调度执行

### 4. 工具与技能

**工具（Tool）** 是智能体可调用的原子能力：

| 类别 | 工具示例 |
|------|----------|
| 文件 I/O | `read_file`, `write_file`, `search_files`, `list_directory` |
| 网络 | `http_request`, `web_search`, `fetch_url` |
| 智能体 | `call_subagent`, `switch_mode` |
| 任务 | `create_task`, `get_task_status` |
| MCP | `mcp_tool_call` |
| 记忆 | `store_memory`, `retrieve_memory` |

**技能（Skill）** 是工具的组合与编排：

- 技能可包含多个工具调用步骤
- 支持参数传递与结果链式引用
- 版本管理与启用/禁用控制

### 5. 权限控制

- **RBAC 模型**：基于角色的访问控制，支持用户-角色-权限多级关联
- **路径规则引擎（Path Rules）**：通过 URL 路径模式匹配实现细粒度 API 授权
- **工具权限**：控制智能体可访问的工具范围
- **审计日志**：记录所有敏感操作，支持查询与导出

### 6. 多渠道集成

统一渠道抽象层，内置适配器支持：

- 飞书（Feishu / Lark）
- Slack
- Telegram
- Discord
- 钉钉（DingTalk）
- 企业微信
- 以及更多...

通过 **Channels** 页面配置渠道参数，即可实现智能体与 IM 平台的双向通信。

### 7. MCP 服务器管理

- 注册 MCP 服务器（支持 stdio 与 SSE 传输模式）
- 自动发现服务器提供的工具列表
- 动态调用 MCP 工具，与内置工具无缝集成

---

## API 概览

后端提供 15 个 REST API 蓝图模块：

| 蓝图 | 前缀 | 核心功能 |
|------|------|----------|
| agents | `/api/agents` | 智能体 CRUD、运行控制 |
| sessions | `/api/sessions` | 会话管理、SSE 流式聊天 |
| tasks | `/api/tasks` | 任务 CRUD、DAG 依赖、状态查询 |
| tools | `/api/tools` | 工具列表、调用、注册 |
| skills | `/api/skills` | 技能 CRUD、启用禁用 |
| permissions | `/api/permissions` | 权限规则、角色管理 |
| channels | `/api/channels` | 渠道配置、消息收发 |
| mcp | `/api/mcp` | MCP 服务器管理、工具调用 |
| memory | `/api/memory` | 记忆存储、检索 |
| plugins | `/api/plugins` | 插件上传、启用、配置 |
| sandbox | `/api/sandbox` | 沙箱执行、环境管理 |
| config | `/api/config` | 动态配置项管理 |
| audit | `/api/audit` | 审计日志查询 |
| auth | `/api/auth` | 登录、注册、Token 刷新 |
| websocket | `/socket.io` | 实时事件推送 |

完整的 API 文档可通过启动后端后访问 `http://localhost:8008/docs` 查看 Swagger UI。

---

## 环境变量

复制 `.env.example` 为 `.env` 并根据环境配置：

### 核心配置

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `SECRET_KEY` | JWT 签名密钥 | - | 是 |
| `ADMIN_PASSWORD` | 管理员初始密码 | - | 是 |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite+aiosqlite:///./openharness.db` | 否 |
| `REDIS_URL` | Redis 连接字符串 | - | 否 |

### 数据库配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_USER` | PostgreSQL 用户名 | `openharness` |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | - |
| `POSTGRES_DB` | PostgreSQL 数据库名 | `openharness` |
| `POSTGRES_HOST` | PostgreSQL 主机 | `localhost` |
| `POSTGRES_PORT` | PostgreSQL 端口 | `5432` |

### 安全与 CORS

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CORS_ORIGINS` | 允许的跨域来源 | `["http://localhost:3000"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT 访问令牌过期时间 | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT 刷新令牌过期时间 | `7` |

### 服务配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BACKEND_HOST` | 后端监听地址 | `0.0.0.0` |
| `BACKEND_PORT` | 后端监听端口 | `8008` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `ENV` | 运行环境 | `development` |

> 完整环境变量列表请参阅 `backend/.env.example` 与 `frontend/.env.example`。

---

## 开发指南

### 代码规范

- **后端**：遵循 PEP 8，使用 `ruff` 进行代码检查与自动修复
- **前端**：使用 ESLint + Prettier，遵循 Next.js 最佳实践

### 常用命令

```bash
# ── 后端开发 ──
cd backend

# 运行测试
pytest

# 代码检查
ruff check .
ruff check . --fix

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1

# ── 前端开发 ──
cd frontend

# 运行测试
npm test

# 代码检查
npm run lint
npm run lint -- --fix

# 类型检查
npx tsc --noEmit
```

### 提交规范

```
<type>: <subject>

<body>
```

**类型**：

- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式（不影响代码运行的变动）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

### 分支策略

- `main`: 主分支，保持稳定可发布状态
- `feature/*`: 功能分支，用于新功能开发
- `fix/*`: 修复分支，用于 Bug 修复

---

## Docker 部署

### 生产环境部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，设置生产环境配置

# 2. 构建并启动
docker-compose -f docker-compose.yml up -d --build

# 3. 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 4. 查看服务状态
docker-compose ps
```

### 服务说明

`docker-compose.yml` 定义了 4 个服务：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| postgres | postgres:16-alpine | 5433 → 5432 | 主数据库 |
| redis | redis:7-alpine | 6380 → 6379 | 缓存与消息队列 |
| backend | 本地构建 | 8008 | Flask API 服务 |
| frontend | 本地构建 | 3000 | Next.js 前端 |

---

## 常见问题

### Q: 前端无法连接后端 API？

检查 `frontend/next.config.js` 中的 `rewrites` 配置，确保 API 代理路径正确。默认配置已将 `/api/*` 代理到 `http://localhost:8008`。

### Q: 数据库迁移失败？

确保 `DATABASE_URL` 配置正确，且数据库服务已启动。对于 SQLite，确保应用有目录写入权限。

### Q: SSE 流式聊天无响应？

检查浏览器控制台网络面板，确认 EventSource 连接已建立。若使用代理或 CDN，请确保支持 SSE 长连接。

### Q: 如何添加自定义工具？

在 `openharness/tools/` 目录下创建新的工具模块，继承工具基类并注册到工具注册表。详细步骤请参阅开发文档。

---

## FAQ

<details>
<summary><b>Q: Can I use OpenClaw without the Agent module?</b></summary>

Yes! OpenClaw is modular by design. The Filesystem module works standalone:
```python
from workbuddy.fs import FileSystem
fs = FileSystem()
```
The Agent module adds orchestration capabilities but is not required.
</details>

<details>
<summary><b>Q: What's the difference between Work Buddy and Code Buddy?</b></summary>

**Work Buddy** focuses on file management and content operations (create, edit, organize files).
**Code Buddy** extends Work Buddy with code quality tools (linting, testing, type checking).
**OpenClaw Agent** orchestrates both with LLM-based reasoning.
</details>

<details>
<summary><b>Q: How do I configure custom tools?</b></summary>

Create a Python file with tool functions and register them:
```python
from openclaw.tools import Tool
def my_custom_tool(param: str) -> str:
    return f"Result: {param}"
custom = Tool("my_tool", my_custom_tool, description="My custom tool")
agent = Agent(tools=[custom])
```
</details>

<details>
<summary><b>Q: Which LLM providers are supported?</b></summary>

OpenClaw supports multiple LLM providers through a unified interface. Current support includes OpenAI, Anthropic, and any OpenAI-compatible API (local models, Azure, etc.).
</details>

<details>
<summary><b>Q: How do I contribute a new skill?</b></summary>

See the [Contributing](#contributing) section. The recommended approach is:
1. Fork the repository
2. Create a branch `feat/my-skill`
3. Add your skill under the appropriate module
4. Submit a Pull Request
</details>

---

## 许可证

[MIT License](LICENSE)

---

## 安全

OpenClaw-Harness 采用安全沙箱架构，所有工具执行均在隔离环境中进行。

如发现安全漏洞，请通过以下方式报告（**不要**创建公开 Issue）：

- **邮箱**: security@openclaw.dev
- **响应时间**: 72 小时内确认，30 天内修复

---

## 致谢

- [OpenAI](https://openai.com) — GPT 系列模型
- [Anthropic](https://anthropic.com) — Claude 系列模型
- [LangChain](https://langchain.com) — Agent 编排框架
- [Playwright](https://playwright.dev) — 浏览器自动化
- [qoder](https://www.qoder.fun) — 社区生态

---

## 开发指南

### 本地开发环境

```bash
# 克隆仓库
git clone https://github.com/weksbwrx62862/OCH.git
cd OCH

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 运行 lint
ruff check src/
mypy src/
```

### 代码规范

- **类型注解**: 所有公共函数必须有完整的类型注解
- **Docstring**: 使用 Google 风格的 docstring
- **测试**: 新功能必须包含单元测试
- **提交**: 使用 Conventional Commits 规范（`feat:`、`fix:`、`docs:` 等）

---

## 路线图

| 阶段 | 目标 | 状态 |
|------|------|------|
| **Phase 1** | Filesystem + Terminal 沙箱 | ✅ 已完成 |
| **Phase 2** | Browser 自动化 + 代码执行 | ✅ 已完成 |
| **Phase 3** | Agent 编排 + 工具链 | 🔄 开发中 |
| **Phase 4** | 多模态支持 + RAG 集成 | 📋 计划中 |
| **Phase 5** | 企业级部署 + 监控 | 📋 计划中 |

---

## 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -m 'feat: add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 创建 Pull Request

欢迎提交 Issue 和 Pull Request，共同完善 OpenClaw-Harness！

---

<div align="center">

**OpenClaw-Harness** — 让智能体安全、高效地使用工具

[⬆ 回到顶部](#-openclaw-harness)

</div>
