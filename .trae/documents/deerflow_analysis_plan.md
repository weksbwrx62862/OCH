# DeerFlow 2.0 项目分析报告

## 项目概述

**DeerFlow (Deep Exploration and Efficient Research Flow)** 是一个由字节跳动开源的 **Super Agent Harness** 框架，它将 **Sub-Agents（子代理）**、**Memory（记忆）** 和 **Sandbox（沙箱）** 有机组织在一起，配合可扩展的 **Skills（技能）**，使 Agent 能够完成几乎任何任务。

**主要特性：**
- 🚀 基于 LangGraph 和 LangChain 构建的完整全栈架构
- 🔒 隔离的沙箱执行环境，支持本地、Docker 和 Kubernetes 模式
- 🧠 跨会话的长期记忆系统
- 🔧 可扩展的技能和 MCP 工具系统
- 💬 支持多 IM 渠道（飞书、Slack、Telegram、企业微信）
- 📊 完整的 Web UI 界面

---

## 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx (端口 2026)                         │
│                    统一反向代理入口                                │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             ▼                                ▼
    ┌──────────────────┐             ┌──────────────────┐
    │  LangGraph Server│             │   Gateway API     │
    │   (端口 2024)    │             │   (端口 8001)     │
    │  Agent 运行时     │             │  REST API 服务    │
    └────────┬─────────┘             └────────┬─────────┘
             │                                  │
             └──────────┬───────────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   Frontend      │
               │  (Next.js/3000) │
               │   Web UI         │
               └─────────────────┘
```

### 核心服务组件

| 组件 | 端口 | 职责 |
|------|------|------|
| **Nginx** | 2026 | 统一入口，反向代理 |
| **LangGraph Server** | 2024 | Agent 运行时和工作流执行 |
| **Gateway API** | 8001 | REST API（模型、MCP、技能、记忆、文件上传等） |
| **Frontend** | 3000 | Next.js Web 界面 |
| **Provisioner** | 8002 | 可选，Kubernetes 沙箱模式 |

---

## 后端技术栈

### 核心依赖

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12+ | 后端开发语言 |
| **LangChain** | - | LLM 交互框架 |
| **LangGraph** | - | 多 Agent 编排 |
| **FastAPI** | 0.115.0+ | Gateway API 框架 |
| **uv** | - | 包管理工具 |

### 后端目录结构

```
backend/
├── packages/harness/deerflow/       # 核心框架包（可独立发布）
│   ├── agents/                       # LangGraph Agent 系统
│   │   ├── lead_agent/              # 主 Agent（工厂 + 系统提示词）
│   │   ├── middlewares/             # 12 个中间件组件
│   │   ├── memory/                  # 记忆提取、队列、提示词
│   │   └── thread_state.py          # ThreadState 数据结构
│   ├── sandbox/                      # 沙箱执行系统
│   │   ├── local/                   # 本地文件系统提供者
│   │   ├── sandbox.py               # 抽象沙箱接口
│   │   ├── tools.py                 # bash、ls、文件读写工具
│   │   └── middleware.py            # 沙箱生命周期管理
│   ├── subagents/                    # 子代理委托系统
│   │   ├── builtins/                # 通用、bash 代理
│   │   ├── executor.py              # 后台执行引擎
│   │   └── registry.py              # 代理注册表
│   ├── tools/builtins/              # 内置工具
│   ├── mcp/                          # MCP 集成（工具、缓存、客户端）
│   ├── models/                       # 模型工厂（支持思考、视觉）
│   ├── skills/                       # 技能发现、加载、解析
│   ├── config/                       # 配置系统
│   ├── community/                    # 社区工具（Tavily、Jina AI 等）
│   ├── reflection/                   # 动态模块加载
│   ├── utils/                        # 工具函数
│   └── client.py                     # 内嵌 Python 客户端
├── app/                              # 应用层
│   ├── gateway/                      # FastAPI Gateway API
│   │   ├── app.py                   # FastAPI 应用
│   │   └── routers/                 # 路由模块
│   └── channels/                     # IM 平台集成
├── tests/                            # 测试套件
└── docs/                             # 文档
```

### 核心模块详解

#### 1. Agent 系统

**Lead Agent** (`agents/lead_agent/agent.py`)：
- 入口点：`make_lead_agent(config)` 注册在 `langgraph.json`
- 动态模型选择，支持思考和视觉功能
- 工具加载：沙箱、内置、MCP、社区、子代理工具组合
- 系统提示词生成，包含技能、记忆和子代理指令

**ThreadState** (`agents/thread_state.py`)：
- 扩展 `AgentState`，包含：`sandbox`、`thread_data`、`title`、`artifacts`、`todos`、`uploaded_files`、`viewed_images`
- 自定义 reducer：`merge_artifacts`（去重）、`merge_viewed_images`（合并/清除）

#### 2. 中间件链（12 个中间件，严格顺序执行）

1. **ThreadDataMiddleware** - 创建每线程目录
2. **UploadsMiddleware** - 跟踪和注入新上传文件
3. **SandboxMiddleware** - 获取沙箱，存储 sandbox_id
4. **DanglingToolCallMiddleware** - 为缺少响应的工具调用注入占位符
5. **GuardrailMiddleware** - 工具调用前授权（可选）
6. **SummarizationMiddleware** - 接近 token 限制时进行上下文压缩（可选）
7. **TodoListMiddleware** - 任务跟踪（计划模式下）
8. **TitleMiddleware** - 自动生成对话标题
9. **MemoryMiddleware** - 异步记忆更新队列
10. **ViewImageMiddleware** - 在 LLM 调用前注入 base64 图像数据
11. **SubagentLimitMiddleware** - 限制并发子代理数量（可选）
12. **ClarificationMiddleware** - 拦截澄清请求（必须最后）

#### 3. 沙箱系统

**接口**：抽象 `Sandbox` 类，包含 `execute_command`、`read_file`、`write_file`、`list_dir`

**实现**：
- `LocalSandboxProvider` - 单例本地文件系统执行
- `AioSandboxProvider` - 基于 Docker 的隔离执行

**虚拟路径系统**：
- Agent 看到：`/mnt/user-data/{workspace,uploads,outputs}`、`/mnt/skills`
- 物理路径：`backend/.deer-flow/threads/{thread_id}/user-data/...`、`deer-flow/skills/`

**沙箱工具**：
- `bash` - 执行命令，带路径转换和错误处理
- `ls` - 目录列表（树状格式，最多 2 层）
- `read_file` - 读取文件内容，支持行范围
- `write_file` - 写入/追加文件，自动创建目录
- `str_replace` - 子串替换

#### 4. 子代理系统

**内置代理**：`general-purpose`（所有工具除了 `task`）和 `bash`（命令专家）

**执行**：双线程池 - `_scheduler_pool`（3 个工作线程）+ `_execution_pool`（3 个工作线程）

**并发限制**：`MAX_CONCURRENT_SUBAGENTS = 3`，由 `SubagentLimitMiddleware` 强制实施，15 分钟超时

**流程**：`task()` 工具 → `SubagentExecutor` → 后台线程 → 5 秒轮询 → SSE 事件 → 结果

#### 5. 记忆系统

**组件**：
- `updater.py` - 基于 LLM 的记忆更新，事实提取，去重
- `queue.py` - 防抖更新队列
- `prompt.py` - 记忆更新提示词模板

**数据结构**（存储在 `backend/.deer-flow/memory.json`）：
- **用户上下文**：`workContext`、`personalContext`、`topOfMind`
- **历史**：`recentMonths`、`earlierContext`、`longTermBackground`
- **事实**：离散事实，包含 `id`、`content`、`category`、`confidence`、`createdAt`、`source`

---

## 前端技术栈

### 核心依赖

| 技术 | 版本 | 用途 |
|------|------|------|
| **Next.js** | 16.1.7 | React 框架 |
| **React** | 19.0.0 | UI 库 |
| **TypeScript** | 5.8.2 | 类型安全 |
| **Tailwind CSS** | 4.0.15 | 样式框架 |
| **shadcn/ui** | - | UI 组件库 |
| **@tanstack/react-query** | 5.90.17 | 数据获取和缓存 |
| **@langchain/langgraph-sdk** | 1.5.3 | LangGraph 客户端 |
| **CodeMirror** | 6.0.2 | 代码编辑器 |

### 前端目录结构

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   ├── components/       # React 组件
│   ├── lib/              # 工具函数
│   └── hooks/            # 自定义 Hooks
├── public/               # 静态资源
└── scripts/              # 构建脚本
```

---

## 技能系统

### 内置技能（22 个）

| 技能 | 描述 |
|------|------|
| `deep-research` | 深度研究 |
| `academic-paper-review` | 学术论文评审 |
| `bootstrap` | 项目启动引导 |
| `chart-visualization` | 图表可视化 |
| `claude-to-deerflow` | Claude Code 集成 |
| `code-documentation` | 代码文档生成 |
| `consulting-analysis` | 咨询分析 |
| `data-analysis` | 数据分析 |
| `find-skills` | 技能发现 |
| `frontend-design` | 前端设计 |
| `github-deep-research` | GitHub 深度研究 |
| `image-generation` | 图像生成 |
| `newsletter-generation` | 新闻通讯生成 |
| `podcast-generation` | 播客生成 |
| `ppt-generation` | PPT 生成 |
| `skill-creator` | 技能创建器 |
| `surprise-me` | 惊喜技能 |
| `vercel-deploy-claimable` | Vercel 部署 |
| `video-generation` | 视频生成 |
| `web-design-guidelines` | 网页设计指南 |

### 技能格式

- 位置：`deer-flow/skills/{public,custom}/`
- 格式：目录 + `SKILL.md`（YAML frontmatter：name、description、license、allowed-tools）
- 按需渐进加载，不会一次性全部塞入上下文

---

## 配置系统

### 主配置 (`config.yaml`)

主要配置节：
- `models[]` - LLM 配置
- `tools[]` - 工具配置
- `tool_groups[]` - 工具逻辑分组
- `sandbox.use` - 沙箱提供者类路径
- `skills.path` / `skills.container_path` - 技能目录路径
- `title` - 自动标题生成配置
- `summarization` - 上下文摘要配置
- `subagents.enabled` - 子代理主开关
- `memory` - 记忆系统配置
- `channels` - IM 渠道配置

### 扩展配置 (`extensions_config.json`)

- `mcpServers` - MCP 服务器配置
- `skills` - 技能启用状态

---

## IM 渠道集成

支持的平台：

| 平台 | 传输方式 | 上手难度 |
|------|----------|----------|
| Telegram | Bot API（long-polling） | 简单 |
| Slack | Socket Mode | 中等 |
| 飞书 / Lark | WebSocket | 中等 |
| 企业微信智能机器人 | WebSocket | 中等 |

---

## 开发命令

### 根目录命令

```bash
make check       # 检查系统要求
make install     # 安装所有依赖（前端 + 后端）
make dev         # 启动所有服务
make stop        # 停止所有服务
make docker-init # 拉取 sandbox 镜像
make docker-start # Docker 开发模式
```

### 后端目录命令

```bash
make install     # 安装后端依赖
make dev         # 仅运行 LangGraph 服务器
make gateway     # 仅运行 Gateway API
make test        # 运行所有后端测试
make lint        # 使用 ruff 进行 lint
make format      # 使用 ruff 格式化代码
```

---

## 安全注意事项

⚠️ **重要安全警告**：

DeerFlow 具备系统指令执行、资源操作等高权限能力，默认设计为部署在本地可信环境（仅本机 127.0.0.1 回环访问）。

**安全建议**：
1. 将 DeerFlow 部署在本地可信网络环境
2. 设置访问 IP 白名单
3. 前置高强度身份验证
4. 网络隔离（专用 VLAN）
5. 持续关注项目安全更新

---

## 总结

DeerFlow 2.0 是一个功能完整、架构清晰的 Super Agent Harness 框架，具有以下突出优势：

1. **完整的全栈架构** - 从前端 Web UI 到后端 Agent 运行时一应俱全
2. **强大的隔离沙箱** - 支持本地、Docker、Kubernetes 多种执行模式
3. **灵活的扩展机制** - 技能、MCP 工具、自定义代理三重扩展
4. **成熟的生产特性** - 记忆系统、IM 集成、链路追踪等
5. **优秀的开发体验** - 清晰的文档、完善的测试、便捷的命令

项目代码质量高，架构设计合理，非常适合作为 Agent 应用开发的基础框架学习和使用。
