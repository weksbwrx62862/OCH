# OpenClaw-Harness 架构分析文档

> 最后更新：2026-04-12

---

## 目录

1. [系统总览](#一系统总览)
2. [后端模块架构](#二后端模块架构)
3. [OpenHarness 核心框架](#三openharness-核心框架)
4. [前端模块架构](#四前端模块架构)
5. [关键业务流程](#五关键业务逻辑流程)
6. [模块依赖关系图](#六模块依赖关系图)
7. [数据库交互层](#七数据库交互层)
8. [配置管理层](#八配置管理层)

---

## 一、系统总览

OpenClaw-Harness (OCH) 是一个基于 **OpenHarness 核心框架** 的多智能体驾驭平台，采用前后端分离架构。

### 1.1 技术栈

| 层级 | 技术栈 | 端口 |
|------|--------|------|
| 前端 | Next.js 14 (App Router) + Zustand + TailwindCSS | 3000 |
| 后端 | Flask 3.0 + SocketIO + SQLAlchemy Async | 8008 |
| 数据库 | PostgreSQL 16 (SQLite 开发模式) | 5433 |
| 缓存 | Redis 7 | 6380 |
| 核心引擎 | OpenHarness (100% preserved) | — |

### 1.2 核心数据流

```
用户 → Next.js 页面 → API Client → Next.js Rewrite/Proxy → Flask API → Service/Model → DB
                   ↘ SSE Proxy Route Handler → Backend Chat SSE → Agent Loop → Tool Execution
                   ↘ SocketIO WebSocket → Real-time Events
```

### 1.3 容器编排 (docker-compose.yml)

| 服务 | 镜像 | 端口映射 | 依赖 |
|------|------|---------|------|
| `backend` | 自建 (Dockerfile.backend) | 8008:8008 | db, redis |
| `frontend` | 自建 (Dockerfile.frontend) | 3000:3000 | backend |
| `db` | postgres:16-alpine | 5433:5432 | — |
| `redis` | redis:7-alpine | 6380:6379 | — |

---

## 二、后端模块架构 (`backend/app/`)

### 2.1 应用入口 — `main.py`

**职责**：Flask Application Factory，全局初始化

**关键功能**：

- `create_app()` — 工厂函数：注册 CORS、Swagger、Blueprint、Security、SocketIO、Error Handlers
- `async_handler()` — 将 async 函数包装为 Flask 同步处理
- `_run_middleware_sync()` — 中间件管道同步执行回退
- `before_request` — 执行中间件管道（认证/限流/验证）
- `__main__` — 启动入口：`init_db()` + `socketio.run()`

**注册的 Blueprint**（15 个，统一前缀 `/api/v1`）：

| Blueprint | URL 前缀 | 模块文件 | 说明 |
|-----------|----------|---------|------|
| `auth_bp` | `/api/v1/auth` | `auth.py` | 认证 |
| `agents_bp` | `/api/v1/agents` | `agents.py` | 智能体管理 |
| `sessions_bp` | `/api/v1/sessions` | `sessions.py` | 会话 & 聊天 |
| `tasks_bp` | `/api/v1/tasks` | `tasks.py` | 后台任务 |
| `tools_bp` | `/api/v1/tools` | `tools.py` | 工具注册表 |
| `skills_bp` | `/api/v1/skills` | `skills.py` | 技能库 |
| `coordinator_bp` | `/api/v1/coordinator` | `coordinator.py` | 多智能体协调 |
| `permissions_bp` | `/api/v1/permissions` | `permissions.py` | 权限规则 |
| `memory_bp` | `/api/v1/memory` | `memory.py` | 记忆管理 |
| `mcp_bp` | `/api/v1/mcp` | `mcp.py` | MCP 服务器 |
| `audit_bp` | `/api/v1/audit` | `audit.py` | 审计日志 |
| `channels_bp` | `/api/v1/channels` | `channels.py` | 消息渠道 |
| `sandbox_bp` | `/api/v1/sandbox` | `sandbox.py` | 沙箱环境 |
| `config_bp` | `/api/v1/config` | `config_api.py` | 系统配置 |
| `plugins_bp` | `/api/v1/plugins` | `plugins.py` | 插件管理 |

### 2.2 配置管理 — `config.py`

**职责**：统一管理所有应用配置

**类 `Settings(BaseSettings)`**，基于 `pydantic-settings`，从环境变量/`.env` 文件加载：

| 配置组 | 关键字段 | 默认值 |
|--------|---------|--------|
| Application | `APP_NAME`, `APP_ENV`, `DEBUG`, `SECRET_KEY` | development |
| JWT | `JWT_SECRET_KEY`, `JWT_ALGORITHM` (HS256), `JWT_EXPIRATION_HOURS` (24) | — |
| Database | `DATABASE_URL`, `DATABASE_POOL_SIZE` (20) | `sqlite+aiosqlite:///./och.db` |
| Redis | `REDIS_URL`, `REDIS_CACHE_TTL` (300) | `redis://localhost:6379/0` |
| CORS | `CORS_ORIGINS` | `["http://localhost:3000"]` |
| OpenHarness | `OPENHARNESS_DEFAULT_MODEL` (claude-sonnet-4), `MAX_TURNS` (8), `MAX_TOKENS` (4096) | — |
| LLM | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | None |
| Security | `ADMIN_PASSWORD`, `RATE_LIMIT_REQUESTS` (100) | — |

- **输入**：环境变量 + `.env` 文件
- **输出**：`get_settings()` 单例，所有模块通过此函数获取配置
- **安全特性**：`_check_default_secrets()` — 非开发环境禁止使用默认密钥

### 2.3 核心层 — `core/`

#### 2.3.1 数据库 — `database.py`

**职责**：SQLAlchemy 异步引擎和会话管理

| 组件 | 说明 |
|------|------|
| `engine` | `create_async_engine()`，支持 SQLite/PostgreSQL 自适应参数 |
| `async_session_factory` | `async_sessionmaker(expire_on_commit=False)` |
| `Base` | `DeclarativeBase`，所有模型的基类 |
| `init_db()` | `Base.metadata.create_all()`，自动建表 |
| `close_db()` | `engine.dispose()`，关闭连接 |
| `get_db()` | AsyncGenerator 上下文管理器，提供事务性会话（commit/rollback/close） |

- **输入**：`Settings.DATABASE_URL`
- **输出**：`AsyncSession` 实例
- **依赖**：`app.config.get_settings()`

#### 2.3.2 异步工具 — `async_utils.py`

**职责**：解决 Flask 同步视图调用 async 代码的桥接问题

| 组件 | 说明 |
|------|------|
| `run_async(coro)` | `asyncio.run()` 包装，同步函数调用异步协程 |
| `get_db()` | 返回 `_DbContextManager`，支持 `async with await get_db() as db` 和 `async with get_db() as db` 两种用法 |
| `_DbContextManager` | 自定义上下文管理器：`__aenter__` 创建会话，`__aexit__` 自动 commit/rollback/close，`__await__` 支持 await 模式 |
| `dispose_engine()` | 关闭数据库引擎（atexit 注册） |

- **输入**：异步协程
- **输出**：同步执行结果
- **依赖**：`app.core.database.async_session_factory`

#### 2.3.3 安全 — `security.py`

**职责**：JWT 认证 + 密码哈希 + 权限装饰器

| 组件 | 说明 |
|------|------|
| `hash_password(password)` | bcrypt 哈希 (rounds=12) |
| `verify_password(plain, hashed)` | bcrypt 验证 |
| `create_jwt(payload, expires_hours)` | 创建 JWT Token (sub, username, role) |
| `decode_jwt(token)` | 解码 JWT |
| `verify_token(token)` | 解码 + 异常处理，返回 payload 或 None |
| `require_auth` | 装饰器：检查 `g.user` 是否存在 |
| `require_role(*roles)` | 装饰器：检查 `g.user.role` 是否在指定角色中 |
| `generate_api_key()` | 生成 `och-` 前缀的 API Key |

- **输入**：HTTP 请求 (Authorization header)
- **输出**：`g.user` payload dict (`{sub, username, role}`)
- **依赖**：`app.config.get_settings()` (JWT_SECRET_KEY, JWT_ALGORITHM)

#### 2.3.4 异常 — `exceptions.py`

**职责**：统一异常层级

```
OCHError (base, code=500)
  ├── NotFoundError (404)
  ├── AuthenticationError (401)
  ├── AuthorizationError (403)
  ├── ValidationError (422, field)
  ├── SessionError (400, session_id)
  ├── ToolExecutionError (500, tool_name)
  └── PermissionDeniedError (403, tool_name)
```

所有异常被 `main.py` 的 `_register_custom_exception_handlers` 统一捕获，返回 JSON 格式错误响应。

### 2.4 中间件管道 — `middleware/__init__.py`

**职责**：有序请求/响应处理管道

**5 个生命周期阶段**：

| 阶段 | 说明 |
|------|------|
| `BEFORE_REQUEST` | 请求前处理 |
| `AFTER_REQUEST` | 请求后处理 |
| `BEFORE_TOOL_CALL` | 工具调用前 |
| `AFTER_TOOL_CALL` | 工具调用后 |
| `ON_ERROR` | 错误处理 |

**4 个内置中间件**（按 order 排序执行）：

| 中间件 | Order | 职责 |
|--------|-------|------|
| `AuthMiddleware` | 10 | JWT Token 验证，设置 `g.user` |
| `RateLimitMiddleware` | 15 | 内存级限流（100 请求/60 秒） |
| `ValidationMiddleware` | 20 | 请求体大小检查（10MB 上限） |
| `AuditMiddleware` | 90 | API 调用日志记录 |

- **输入**：`MiddlewareContext(request, response, metadata)`
- **输出**：`MiddlewareResult(modified, blocked, block_reason, skip_remaining)`
- **依赖**：`app.core.security.verify_token`

### 2.5 数据模型 — `models/`

**10 个模型，关系图**：

```
Agent 1──N Session 1──N Message
  │                └──N Task N──N TaskDependency (DAG)
  └──N ToolPermission

Team 1──N TeamMember ──→ Agent (FK)

PermissionRule (全局)    AuditLog (全局)
MCPServer (独立)         MemoryFact (独立)
Plugin (独立)            Skill (独立)
```

#### Agent (`agent.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String (UUID) | 主键 |
| name | String (unique) | Agent 名称 |
| description | Text | 描述 |
| system_prompt | Text | 系统提示词 |
| model | String | 默认 LLM 模型 |
| max_turns | Integer | 最大对话轮数 |
| max_tokens | Integer | 最大输出 token |
| workspace | String | 工作目录 |
| config | JSON | 扩展配置 |
| is_active | Boolean | 启用状态 |
| created_by | String | 创建者 |

关系：`sessions` (1:N), `permissions` (1:N ToolPermission)

#### ToolPermission (`agent.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String (UUID) | 主键 |
| agent_id | String (FK→agents) | 所属 Agent |
| tool_name | String | 工具名称 |
| permission | Enum | allow/deny/ask |
| path_rules | JSON | 路径限制规则 |
| approved_commands | JSON | 批准的命令列表 |
| denied_commands | JSON | 拒绝的命令列表 |

#### Session (`session.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String (UUID) | 主键 |
| agent_id | String (FK→agents) | 所属 Agent |
| status | Enum | active/paused/completed |
| title | String | 会话标题 |
| total_messages | Integer | 消息计数 |
| total_turns | Integer | 对话轮数 |
| total_tokens_input/output | Integer | Token 统计 |
| total_cost_usd | Float | 费用统计 |
| metadata | JSON | 扩展元数据 |

关系：`agent`, `messages` (1:N), `tasks` (1:N)

#### Message (`message.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String (UUID) | 主键 |
| session_id | String (FK) | 所属会话 |
| role | Enum | user/assistant/system/tool |
| content | Text | 消息内容 |
| tool_uses | JSON | 工具调用记录 |
| stop_reason | String | 停止原因 |
| tokens_input/output | Integer | Token 统计 |
| model | String | 使用的模型 |

#### Task (`task.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String (UUID) | 主键 |
| session_id | String (FK) | 所属会话 |
| task_type | String | 任务类型 |
| command | String | 执行命令 |
| status | Enum | pending/running/completed/failed/stopped |
| result | Text | 执行结果 |
| error | Text | 错误信息 |
| exit_code | Integer | 退出码 |
| pid | Integer | 进程 ID |
| output_path | String | 输出路径 |
| cwd | String | 工作目录 |
| metadata | JSON | 扩展元数据 |

关系：`dependencies` (N:N TaskDependency DAG)

#### Team / TeamMember (`team.py`)

**Team**：id, name, description, status (active/paused/dissolved), config (JSON), metadata (JSON), created_by

**TeamMember**：id, team_id (FK), agent_id (FK→agents), role (leader/reviewer/worker), capabilities (JSON), status (idle/busy/offline), assigned_task_id, task_count, completed_tasks

#### PermissionRule / AuditLog (`permission.py`)

**PermissionRule**：id, name, pattern (glob), allow (bool), description, priority, created_by

**AuditLog**：id, user_id, action, resource_type, resource_id, details (JSON), ip_address, user_agent, status_code, error_message

### 2.6 API 路由层 — `api/`

#### 2.6.1 认证 API — `auth.py`

| 端点 | 方法 | 说明 | 输入 | 输出 |
|------|------|------|------|------|
| `/api/v1/auth/login` | POST | 登录 | `{username, password}` | `{access_token, token_type, expires_in, user}` |
| `/api/v1/auth/verify` | GET | 验证 Token | Authorization header | `{valid, user}` |
| `/api/v1/auth/refresh` | POST | 刷新 Token | Authorization header | `{access_token, token_type, expires_in}` |

**特殊逻辑**：开发环境不需要密码即可登录；生产环境必须配置 `ADMIN_PASSWORD`

#### 2.6.2 智能体 API — `agents.py`

| 端点 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/agents` | GET | auth | 列出 Agent（分页+搜索+状态筛选） |
| `/agents` | POST | admin | 创建 Agent（含工具权限配置） |
| `/agents/quick-create` | POST | auth | 快速创建聊天用 Agent（普通用户可用） |
| `/agents/{id}` | GET | auth | 获取详情（含权限配置） |
| `/agents/{id}` | PUT | admin | 更新配置 |
| `/agents/{id}` | DELETE | admin | 删除（级联删除权限和会话） |
| `/agents/{id}/duplicate` | POST | auth | 复制（含配置和权限） |
| `/agents/{id}/stats` | GET | auth | 统计数据 |
| `/agents/{id}/permissions` | GET | auth | 获取权限配置 |
| `/agents/{id}/permissions` | PUT | admin | 更新权限配置 |

#### 2.6.3 会话 & 聊天 API — `sessions.py`（核心）

**会话管理**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/sessions` | GET | 列出会话（分页+状态/Agent 筛选） |
| `/sessions` | POST | 创建会话 |
| `/sessions/{id}` | GET | 获取详情（含最近 5 条消息） |
| `/sessions/{id}` | DELETE | 删除会话 |
| `/sessions/{id}/pause` | PUT | 暂停 |
| `/sessions/{id}/resume` | PUT | 恢复 |
| `/sessions/{id}/messages` | GET | 消息列表（分页） |
| `/sessions/{id}/stats` | GET | 统计数据 |

**聊天核心流程** (`/sessions/{id}/chat POST`)：

```
用户消息 → 保存到 DB → Agent Loop (最多 max_turns 轮)
  → 每轮: thinking → _generate_ai_response → [text_delta / tool_start → _execute_tool → tool_end]
  → 结束: turn_complete → 保存 assistant 消息 → 更新 Session 统计
```

**SSE 事件类型**：

| 事件 | 说明 |
|------|------|
| `message_saved` | 用户消息已保存 |
| `thinking` | AI 思考中 |
| `text_delta` | 文本增量 |
| `tool_start` | 工具调用开始 |
| `tool_end` | 工具调用完成 |
| `turn_complete` | 一轮完成 |
| `error` | 错误 |

**SSE 流式架构**：异步生成器 → 线程队列 → Flask `stream_with_context` → SSE Response

**CompactCache API**：

| 端点 | 说明 |
|------|------|
| `/sessions/compact-cache` | 缓存统计 |
| `/sessions/compact-cache/{tool_id}` | 查找缓存工具输出 |
| `/sessions/compact-cache/clear-expired` | 清除过期缓存 |

#### 2.6.4 任务 API — `tasks.py`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/tasks` | GET | 任务列表（分页+状态/类型筛选） |
| `/tasks` | POST | 创建任务 |
| `/tasks/{id}` | GET | 获取详情 |
| `/tasks/{id}` | PUT | 更新状态 |
| `/tasks/{id}` | DELETE | 删除 |
| `/tasks/{id}/cancel` | POST | 取消任务 |
| `/tasks/{id}/dependencies` | GET | 查看依赖 |
| `/tasks/{id}/dependencies` | POST | 添加依赖 |
| `/tasks/stats` | GET | 统计 |

#### 2.6.5 工具 API — `tools.py`

43+ 工具按 7 个分类组织：

| 分类 | 工具 | 危险级别 |
|------|------|---------|
| file_io | Bash(⚠), Read, Write, Edit, Glob, Grep, NotebookEdit, Lsp | Bash 危险 |
| web | WebFetch, WebSearch | 安全 |
| agent | Agent(⚠), SendMessage, TeamCreate(⚠), TeamDelete(⚠) | 危险 |
| task | TaskCreate/Get/List/Stop/Output/Update | 安全 |
| mcp | MCPTool(⚠), ListMcpResources, ReadMcpResource | MCPTool 危险 |
| mode | EnterPlanMode, ExitPlanMode, Compact | 安全 |
| memory | MemoryCreate, MemoryRead, MemorySearch | 安全 |

端点：列表、分类、详情、Schema、安全检查

#### 2.6.6 技能 API — `skills.py`

双源管理（DB + 文件系统）：
- 列出/搜索/分类/详情
- 安装/卸载
- 启用/禁用
- 扫描新技能

#### 2.6.7 协调器 API — `coordinator.py`

**三套并行机制**：

1. **团队管理**：teams CRUD + 成员管理
2. **AutonomousWorker**（来自 `openharness/coordinator/`）：
   - `/coordinator/workers` — Worker 列表/启动/停止/统计
   - 空闲轮询 + 超时自动关机 + 身份注入
3. **SubagentExecutor**（双线程池）：
   - `/coordinator/subagents` — 任务提交/查询/取消/统计
   - 调度池 + 执行池分离，并发上限控制，超时保护

3 个内置 Agent 定义：Code Reviewer, Debugger, Planner

#### 2.6.8 其他 API

| API | 模块文件 | 核心端点 |
|-----|---------|---------|
| 权限 | `permissions.py` | PermissionRule CRUD + 权限检查 |
| 记忆 | `memory.py` | MemoryFact CRUD + 去重 + 置信度管理 |
| MCP | `mcp.py` | MCPServer CRUD + 连接测试 + 工具/资源发现 |
| 审计 | `audit.py` | AuditLog 列表 + CSV/JSON 导出 + 清除 |
| 渠道 | `channels.py` | 11 种 IM 渠道 + 注册 + 发送测试 |
| 沙箱 | `sandbox.py` | 状态查询 + 命令执行 + 安全检查 |
| 配置 | `config_api.py` | 读取/更新 + Provider 管理 |
| 插件 | `plugins.py` | 安装/卸载/启用/禁用 |

#### 2.6.9 WebSocket — `websocket.py`

SocketIO 事件处理：

| 事件 | 方向 | 说明 |
|------|------|------|
| `connect` | C→S | JWT 认证，返回 sid |
| `disconnect` | C→S | 断开连接 |
| `join_session` | C→S | 加入会话房间 |
| `leave_session` | C→S | 离开会话房间 |
| `ping` | C→S | 心跳 |

服务端 emit 函数：

| 函数 | 说明 |
|------|------|
| `emit_session_event(session_id, event_type, data)` | 会话级事件 |
| `emit_tool_progress(session_id, tool_name, status)` | 工具进度 |
| `emit_system_notification(level, title, message)` | 全局广播 |
| `emit_agent_status(agent_id, status)` | Agent 状态变更 |

### 2.7 服务层 — `services/`

| 服务 | 职责 | 依赖 |
|------|------|------|
| `SessionService` | 会话生命周期管理 | models.Session |
| `ToolService` | 工具注册、发现、安全验证 | openharness.tools |
| `SkillService` | Markdown 技能库管理 | openharness.skills |
| `CoordinatorService` | 多智能体协调和任务分派 | models.Team |
| `PermissionService` | RBAC + 路径规则引擎 | models.PermissionRule |
| `PluginService` | 插件安装/卸载/启用/禁用 | models.Plugin |
| `HookService` | 钩子执行引擎 | openharness.hooks |
| `CacheService` | CompactCache（微压缩缓存） | 内存 |
| `SubagentExecutor` | 双线程池子代理执行器 | 线程池 |

---

## 三、OpenHarness 核心框架 (`backend/openharness/`)

100% 保留的核心引擎，25+ 子包：

| 子包 | 职责 | 关键类 |
|------|------|--------|
| `engine/` | 查询引擎核心 | `QueryEngine`, `CostTracker`, `StreamEvents` |
| `tools/` | 43+ 工具实现 | `BaseTool`, `ToolExecutionContext`, `ToolResult` |
| `channels/` | 12 个 IM 适配器 | `BaseChannel`, `ChannelBridge`, `MessageBus` |
| `coordinator/` | 多智能体协调 | `AutonomousWorker`, `CoordinationProtocolHandler` |
| `permissions/` | 权限系统 | `PermissionChecker`, `PermissionMode`, `PathRule` |
| `memory/` | Agent 记忆 | `AgentMemory`, `AgentMemoryConfig` |
| `services/` | 基础服务 | `CompactService`, `CronScheduler`, `TokenEstimation` |
| `swarm/` | Swarm 模式 | `InProcessBackend`, Git Worktree 隔离 |
| `sandbox/` | 沙箱执行 | `srt` 适配器 |
| `hooks/` | 钩子系统 | `HookExecutor`, `CompactWarningHook` |
| `skills/` | 内置技能 | `.md` 知识库技能 |
| `bridge/` | 消息桥接 | `ChannelBridge` (MessageBus → QueryEngine) |
| `mcp/` | MCP 协议 | `McpClientManager` |

### 核心抽象 (God Nodes)

基于 graphify 代码图谱分析，最核心的 5 个抽象：

| 排名 | 抽象 | 边数 | 说明 |
|------|------|------|------|
| 1 | `ToolExecutionContext` | 212 | 工具执行上下文，贯穿所有工具调用 |
| 2 | `BaseTool` | 209 | 工具基类，所有工具的抽象父类 |
| 3 | `ToolResult` | 206 | 工具执行结果，标准化输出 |
| 4 | `OutboundMessage` | 183 | 出站消息，渠道通信核心 |
| 5 | `BaseChannel` | 174 | 渠道基类，IM 适配器抽象 |

---

## 四、前端模块架构 (`frontend/`)

### 4.1 技术栈

- **框架**：Next.js 14 (App Router, standalone output)
- **UI**：TailwindCSS + Lucide Icons
- **状态管理**：Zustand
- **API 通信**：自定义 ApiClient (REST + SSE)
- **字体**：Inter + JetBrains Mono

### 4.2 请求代理架构

```
浏览器 → /api/v1/*  → next.config.js rewrite → Backend:8008/api/v1/*
浏览器 → /ws/*      → next.config.js rewrite → Backend:8008/ws/*
浏览器 → /api/proxy/chat → Route Handler (SSE) → Backend:8008/api/v1/sessions/{id}/chat
```

**关键设计**：
- `next.config.js` 的 `rewrites` 只代理 `/api/v1/*`，避免与 Next.js 自身 `/api/proxy/*` 冲突
- SSE 聊天使用独立的 Route Handler (`app/api/proxy/chat/route.ts`)，因为 Next.js rewrite 不支持 SSE 流式

### 4.3 认证流程

```
LoginPage → POST /api/v1/auth/login → JWT Token → localStorage('och_token')
AuthCheck → AuthProvider → 检查 localStorage → 无 token 重定向 /login
API请求   → ApiClient.getHeaders() → Authorization: Bearer {token}
```

### 4.4 页面模块

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | Dashboard | 审计日志概览 + 统计卡片 |
| `/login` | Login | 用户登录 |
| `/chat` | Chat | **核心**：SSE 流式聊天 + 工具调用 + 记忆侧边栏 |
| `/agents` | Agents | Agent CRUD 管理 |
| `/sessions` | Sessions | 会话列表 |
| `/tasks` | Tasks | 任务管理 |
| `/skills` | Skills | 技能浏览 |
| `/tools` | Tools | 工具浏览器 |
| `/audit` | Audit | 审计日志 |
| `/settings` | Settings | 系统配置 |
| `/swarm` | Swarm | 多智能体协作 |

### 4.5 聊天页面核心流程 (`chat/page.tsx`)

```
1. 初始化：检查 URL sid → 恢复会话 / 自动 quick-create Agent + 创建 Session
2. 发送消息：apiClient.streamChat(sessionId, message, onEvent)
3. SSE 事件处理：
   - thinking → 更新 turn 计数
   - text_delta → 追加流式内容
   - tool_start → 添加活跃工具调用
   - tool_end → 更新工具调用结果
   - turn_complete → 结束加载
   - error → 显示错误
4. 流式结束后：将完整 assistant 消息追加到 messages 列表
```

### 4.6 状态管理 — `stores/appStore.ts`

Zustand store 管理全局 UI 状态：

| 状态 | 类型 | 说明 |
|------|------|------|
| `user` | `{id, username, role}` | 当前用户 |
| `sidebarOpen` | boolean | 侧边栏开关 |
| `theme` | `'dark' \| 'light'` | 主题 |
| `commandPaletteOpen` | boolean | 命令面板 |
| `isLoading` | boolean | 全局加载 |
| `notifications` | Notification[] | 通知队列 |

### 4.7 类型系统 — `lib/types.ts`

与后端 `to_dict()` 输出对齐的完整类型定义：

| 类型 | 对应后端模型 |
|------|-------------|
| `User`, `LoginResponse` | JWT payload |
| `Agent`, `ToolPermission` | Agent, ToolPermission |
| `Session` | Session |
| `Message`, `ToolUse` | Message |
| `Task` | Task |
| `Skill` | Skill |
| `ToolInfo` | 工具注册表 |
| `AuditLog` | AuditLog |
| `MemoryFact` | MemoryFact |
| `PaginatedResponse<T>` | 分页响应泛型 |

### 4.8 组件层级

```
RootLayout
  └── AuthProvider
        └── AppLayout
              ├── Sidebar (导航)
              ├── TopBar (用户信息/主题/命令面板)
              ├── {children} (页面内容)
              └── ToastContainer (通知)

ChatPage
  ├── MessageBubble (消息气泡)
  │     └── ToolCallCard (工具调用卡片)
  ├── MarkdownRenderer (动态加载, SSR=false)
  ├── MemorySidebar (记忆侧边栏)
  └── ChatInput (输入框 + 快捷提示)
```

### 4.9 API 客户端 — `lib/api.ts`

`ApiClient` 类封装所有后端通信：

| 方法 | 说明 |
|------|------|
| `getHeaders()` | 构建带 JWT 的请求头 |
| `get/post/put/delete(url, ...)` | REST 请求封装 |
| `streamChat(sessionId, message, onEvent)` | SSE 流式聊天 |
| `getPaginated(url, params)` | 分页请求封装 |

SSE 流式聊天通过 `EventSource` 连接 Next.js Route Handler (`/api/proxy/chat`)，Route Handler 再作为代理转发到后端 SSE 端点。

---

## 五、关键业务逻辑流程

### 5.1 聊天流程（最核心）

```
用户输入 → ChatInput.sendMessage()
  → apiClient.streamChat(sessionId, message, onEvent)
    → POST /api/proxy/chat?sessionId=X  (Next.js Route Handler)
      → POST http://backend:8008/api/v1/sessions/X/chat  (SSE proxy)
        → sessions.chat() → _chat_stream_impl()
          → 新线程: _run_async_generator()
            → stream_chat_sse() 异步生成器:
              1. 保存用户消息 → emit message_saved
              2. Agent Loop (max_turns):
                 a. emit thinking
                 b. _generate_ai_response() → [text | tool_use]
                 c. text → emit text_delta
                 d. tool_use → emit tool_start
                    → _execute_tool() → emit tool_end
                 e. 有更多工具 → 继续循环
              3. 保存 assistant 消息 → 更新 Session 统计
              4. emit turn_complete
              5. emit [DONE]
          → queue.Queue 桥接 → Flask stream_with_context → SSE Response
  ← SSE 事件流 → onEvent 回调 → UI 状态更新
```

### 5.2 认证流程

```
LoginPage: POST /api/v1/auth/login {username, password}
  → auth.login() → create_jwt({sub, username, role})
  → 响应: {access_token, user: {id, username, role}}
  → localStorage.setItem('och_token', token)

每次请求: ApiClient.getHeaders() → Authorization: Bearer {token}
  → AuthMiddleware.before_request() → verify_token() → g.user = payload

WebSocket: connect?token={token} → handle_connect() → verify_token()
```

### 5.3 多智能体协调流程

```
1. 创建团队: POST /coordinator/teams {name, members}
2. 生成子 Agent: POST /coordinator/spawn {agent_definition, task, team_id}
3. 提交子代理任务: POST /coordinator/subagents {prompt, agent_id, timeout}
   → SubagentExecutor (调度池+执行池) → 执行 → 结果
4. 启动自治 Worker: POST /coordinator/workers {agent_id, team}
   → AutonomousWorker → 空闲轮询认领任务 → 超时自动关机
```

### 5.4 权限检查流程

```
工具调用 → _execute_tool()
  → PermissionService.check_tool_permission(agent_id, tool_name, input)
    → 三重校验:
      1. DenialTracker 内存缓存（快速拒绝）
      2. PermissionChecker (openharness/permissions/)
      3. DB PermissionRule + Agent.ToolPermission
    → 返回 {allowed, decision, reason}
```

---

## 六、模块依赖关系图

```
                    ┌─────────────┐
                    │  config.py  │ ← .env / 环境变量
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐     ┌──────▼──────┐   ┌──────▼──────┐
    │database │     │  security   │   │ middleware  │
    │  .py    │     │    .py      │   │  __init__   │
    └────┬────┘     └──────┬──────┘   └──────┬──────┘
         │                 │                 │
    ┌────▼────┐           │                 │
    │async_   │           │                 │
    │utils.py │           │                 │
    └────┬────┘           │                 │
         │                 │                 │
    ┌────▼─────────────────▼─────────────────▼────┐
    │              models/ (10个模型)               │
    │  Agent Session Message Task Team Permission  │
    │  ToolPermission TaskDependency MCPServer     │
    │  MemoryFact Plugin Skill AuditLog            │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │              services/ (9个服务)              │
    │  Session Tool Skill Coordinator Permission   │
    │  Plugin Hook Cache SubagentExecutor          │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │            api/ (15个 Blueprint)             │
    │  auth agents sessions tasks tools skills     │
    │  coordinator permissions memory mcp audit    │
    │  channels sandbox config plugins websocket   │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │             main.py (Flask App)              │
    │  Blueprint注册 + 中间件 + SocketIO + 错误处理  │
    └──────────────────────────────────────────────┘
                       ↕
    ┌──────────────────────────────────────────────┐
    │         openharness/ (核心引擎, 25+子包)       │
    │  engine tools channels coordinator           │
    │  permissions memory swarm sandbox hooks      │
    └──────────────────────────────────────────────┘

前端依赖链:
    types.ts ← api.ts ← 页面组件 ← AuthProvider ← RootLayout
              ↖ stores/appStore.ts ↗
```

---

## 七、数据库交互层

### 7.1 连接池配置

| 参数 | PostgreSQL | SQLite |
|------|-----------|--------|
| pool_size | 20 | — |
| max_overflow | 30 | — |
| pool_pre_ping | True | — |
| echo | debug 模式开启 | debug 模式开启 |

### 7.2 会话管理

- 所有 API 通过 `get_db()` 获取事务性会话
- `_DbContextManager` 自动 commit/rollback/close
- Flask 同步视图通过 `run_async()` 桥接 async 代码

### 7.3 数据库迁移

- 使用 Alembic (`backend/alembic/`)
- 初始迁移: `001_initial`

---

## 八、配置管理层

### 8.1 配置源优先级

| 配置源 | 优先级 | 示例 |
|--------|--------|------|
| 环境变量 | 最高 | `DATABASE_URL`, `JWT_SECRET_KEY` |
| `.env` 文件 | 中 | `backend/.env` |
| `Settings` 默认值 | 最低 | `APP_ENV='development'` |
| Docker Compose `env_file` | 容器级 | `.env` |

### 8.2 安全约束

- 非开发环境禁止使用默认密钥（`_check_default_secrets()`）
- 配置 API 输出自动脱敏（密码/密钥替换为 `***`）

### 8.3 关键环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `DATABASE_URL` | 数据库连接串 | 生产环境 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 生产环境 |
| `ADMIN_PASSWORD` | 管理员密码 | 生产环境 |
| `ANTHROPIC_API_KEY` | Anthropic API Key | 使用 Claude 时 |
| `OPENAI_API_KEY` | OpenAI API Key | 使用 GPT 时 |
| `REDIS_URL` | Redis 连接串 | 生产环境 |
| `APP_ENV` | 运行环境 (development/production) | 否 |
