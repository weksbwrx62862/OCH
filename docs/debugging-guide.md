# OpenClaw-Harness 各模块单独调试指南

> 生成时间：2026-04-12
> 基于架构文档 `architecture.md` 对照实际代码的诊断结果

---

## 目录

1. [全局性问题](#一全局性问题)
2. [后端模块调试](#二后端模块调试)
3. [前端模块调试](#三前端模块调试)
4. [基础设施调试](#四基础设施调试)
5. [模块间集成调试](#五模块间集成调试)

---

## 一、全局性问题

### 1.1 技术栈版本不一致

| 组件 | 架构文档描述 | 实际代码 | 问题 |
|------|------------|---------|------|
| Next.js | 14 (App Router) | **15.5.14** | `package.json` 实际使用 Next.js 15，文档需更新 |
| React | — | **19.2.4** | Next.js 15 配套 React 19，与 Next.js 14 + React 18 的文档不匹配 |
| SocketIO async_mode | — | `threading` | 生产环境应使用 `gevent` 或 `eventlet` 以获得更好并发性能 |

**调整建议**：更新架构文档中技术栈版本号为实际值，或降级前端依赖至 Next.js 14。

### 1.2 `.env` 配置问题

| 问题 | 位置 | 说明 |
|------|------|------|
| `ADMIN_PASSWORD` 为空 | `.env` 第 47 行（缺失） | 架构文档说"生产环境必须配置"，但 `.env` 未定义此字段 |
| `ANTHROPIC_API_KEY` 为空 | `.env` 第 36 行 | 聊天功能依赖此 Key，缺失将导致 AI 调用失败 |
| `OPENAI_API_KEY` 为空 | `.env` 第 38 行 | 同上，GPT 模型不可用 |
| Redis 端口不匹配 | `.env` 第 22 行 `6379` vs `docker-compose.yml` 第 23 行 `6380` | Docker 环境下 Redis 映射为 6380，但 `.env` 写的是 6379 |
| PostgreSQL 端口不匹配 | `.env` 第 16 行注释 `5432` vs `docker-compose.yml` 第 10 行 `5433` | 同上，Docker 环境映射为 5433 |

**调整建议**：
- 在 `.env` 中添加 `ADMIN_PASSWORD` 字段
- 填入至少一个 LLM API Key
- Docker 环境下将 `REDIS_URL` 改为 `redis://localhost:6380/0`
- Docker 环境下将 `DATABASE_URL` 改为 `postgresql+asyncpg://och:och123@localhost:5433/openclaw_harness`

---

## 二、后端模块调试

### 2.1 应用入口 `main.py`

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/backend
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=/home/xxh/openclaw-harness/backend
python -m app.main
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `static_folder` 和 `template_folder` 指向 `../frontend/public` | `main.py:82-83` | Flask 不应直接引用前端目录，前后端已分离部署，应删除这两行或改为 None |
| 2 | `before_request` 中 `asyncio.run()` 在已有事件循环时会抛 `RuntimeError` | `main.py:178` | 当前靠 `except RuntimeError` 回退到 `_run_middleware_sync()`，但这意味着中间件管道的 `async` 逻辑被绕过，`after_request` 阶段不会执行 |
| 3 | `socketio` 在模块顶层创建，早于 `create_app()` | `main.py:27` | `cors_allowed_origins=get_settings().CORS_ORIGINS` 在导入时即调用 `get_settings()`，如果 `.env` 不存在会使用默认值，可能不符合预期 |
| 4 | `auth_bp` 单独注册但其他 Blueprint 通过循环注册 | `main.py:210` | `auth_bp` 已自带 `/api/v1/auth` 前缀，而其他 bp 使用 `url_prefix=f'{api_prefix}{url_prefix}'`，这是正确的但需注意不要重复加前缀 |
| 5 | 错误处理中 401 返回而非 403 时的状态码判断有误 | `main.py:185` | `status_code = 404 if 'not found' in result.block_reason.lower() else 401` — 缺少 403 (Forbidden) 的判断，权限被拒时应返回 403 |
| 6 | `init_security(app)` 是空函数 | `security.py:20-22` | `init_security` 只做了 `pass`，未注册任何 `before_request` 处理器。认证逻辑实际由中间件管道处理，此函数应移除或明确标注已弃用 |

### 2.2 配置管理 `config.py`

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "from app.config import get_settings; s = get_settings(); print(f'DB={s.DATABASE_URL}'); print(f'Redis={s.REDIS_URL}'); print(f'Env={s.APP_ENV}')"
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `@lru_cache()` 使用了过期语法 | `config.py:94` | Python 3.8+ 推荐 `@lru_cache` 无括号形式，当前 `@lru_cache()` 不影响功能但不够规范 |
| 2 | `.env` 文件路径硬编码为相对路径 | `config.py:88` | `env_file=".env"` 相对于工作目录，Docker 中工作目录为 `/app`，但 `docker-compose.yml` 通过 `env_file: - .env` 注入，所以 Pydantic 的 `.env` 读取在 Docker 中可能不生效 |
| 3 | CORS_ORIGINS 默认值不包含 Docker frontend 域名 | `config.py:39` | Docker 环境下前端访问后端为 `http://backend:8008` 或 `http://localhost:3000`，默认值只有 localhost:3000，缺少 `http://frontend:3000` |

### 2.3 数据库层 `core/database.py` + `core/async_utils.py`

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "
import asyncio
from app.core.database import init_db, engine
asyncio.run(init_db())
print('DB init OK')
print(f'Engine: {engine.url}')
"
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `database.py` 中 `settings = get_settings()` 在模块级别调用 | `database.py:15` | 这会在 import 时立即创建引擎，如果 `.env` 配置有误则直接报错。应改为延迟初始化 |
| 2 | `get_db()` 在 `database.py` 和 `async_utils.py` 中都有定义 | 两个文件 | `database.py:44` 的 `get_db()` 是 AsyncGenerator，`async_utils.py:69` 的 `get_db()` 返回 `_DbContextManager`。API 层应统一使用 `async_utils.py` 的版本，但 `database.py` 的版本仍存在，可能造成混淆 |
| 3 | SQLite 不支持并发写入 | — | 开发模式用 SQLite，但 `async_handler` 中多线程调用 `asyncio.run()` 可能导致 "database is locked" 错误 |
| 4 | `_DbContextManager.__aenter__` 中 `self._session = self._session_factory()` | `async_utils.py:46` | `self._session_factory()` 返回的是 `AsyncSession` 上下文管理器，需调用 `await self._session_factory().__aenter__()` 或 `async with self._session_factory() as session`，当前写法 `await self._session.__aenter__()` 是正确的但不够直观 |

### 2.4 安全层 `core/security.py`

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "
from app.core.security import create_jwt, verify_token, hash_password, verify_password
token = create_jwt({'sub': 'test', 'username': 'test', 'role': 'admin'})
print(f'Token: {token[:50]}...')
payload = verify_token(token)
print(f'Verified: {payload}')
hashed = hash_password('test123')
print(f'Verify: {verify_password(\"test123\", hashed)}')
"
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `init_security(app)` 是空函数 (pass) | `security.py:20-22` | 架构文档说 "Initialize security (JWT auth before_request handler)"，但实际什么都没做。认证由中间件管道处理，应删除此函数调用或实现预期逻辑 |
| 2 | `require_auth` 装饰器检查 `g.user` 但不检查 token 过期 | `security.py:75-82` | 如果 token 已过期但 `g.user` 仍被中间件设置（不太可能），则仍可通过。当前依赖中间件在 before_request 中验证 token，所以问题不大 |

### 2.5 中间件 `middleware/__init__.py`

**调试步骤**：

```bash
# 启动后端后访问中间件信息端点
curl http://localhost:8008/api/v1/middleware
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `AuthMiddleware` 和 `_run_middleware_sync` 逻辑重复 | `main.py:33-58` vs `middleware/__init__.py:212-246` | 两处都做了相同的 JWT 验证逻辑，当 `asyncio.run()` 失败回退时调用 `_run_middleware_sync()`，但其逻辑与 `AuthMiddleware.before_request()` 不同步 |
| 2 | `AuditMiddleware` 只实现了 `after_request` | `middleware/__init__.py:255` | 但 Flask 的 `before_request` 钩子中执行的是 `BEFORE_REQUEST` 阶段，`after_request` 阶段从未被调用（因为 `after_request` 钩子未注册） |
| 3 | `RateLimitMiddleware` 使用内存存储 | `middleware/__init__.py:298` | 多 worker 部署时限流不共享，生产环境应使用 Redis |
| 4 | `/api/v1/auth/login` 是 public_path | `middleware/__init__.py:229` | 但 `/api/v1/auth/verify` 和 `/api/v1/auth/refresh` 不在白名单中，会导致这两个端点也需要认证才能访问（这是正确行为，但需确认是否预期） |

### 2.6 认证 API `api/auth.py`

**调试步骤**：

```bash
# 登录
curl -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": ""}'

# 验证
curl http://localhost:8008/api/v1/auth/verify \
  -H "Authorization: Bearer <token>"
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 开发环境无需密码即可登录 | `auth.py:46` | 任何用户名都能获得 admin 权限，这是开发便利设计，但需确保生产环境 `APP_ENV != 'development'` |
| 2 | `ADMIN_PASSWORD` 为空时生产环境无法登录 | `auth.py:49-50` | `.env` 中 `ADMIN_PASSWORD` 未设置，生产环境启动后会返回 "Login disabled"，需要配置 |
| 3 | 密码比较使用 `verify_password(plain, hashed)` | `auth.py:51` | 但 `.env` 中 `ADMIN_PASSWORD` 存储的是明文，不是 bcrypt 哈希。如果直接传明文给 `verify_password()` 会失败，因为第二个参数应为哈希值。**这是一个 BUG** |

**BUG 详情**：`auth.py:51` 调用 `verify_password(password, settings.ADMIN_PASSWORD)`，`settings.ADMIN_PASSWORD` 是从环境变量读取的明文密码，但 `verify_password` 期望第二个参数是 bcrypt 哈希值。

**调整建议**：应该在启动时对 `ADMIN_PASSWORD` 进行哈希处理并缓存，或改用明文比较。

### 2.7 会话与聊天 API `api/sessions.py`

**调试步骤**：

```bash
# 先获取 token
TOKEN=$(curl -s -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 创建会话
curl -X POST http://localhost:8008/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "测试会话"}'

# 列出会话
curl http://localhost:8008/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN"
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 内存缓存 `_active_sessions` 无持久化 | `sessions.py:33` | 进程重启后缓存丢失，生产环境应使用 Redis |
| 2 | SSE 流式架构中 `asyncio.run()` 与 Flask 线程冲突 | 架构文档描述 | Flask 是同步框架，`sessions.py` 中的 SSE 流式实现需要在新线程中运行异步代码，通过 `queue.Queue` 桥接，这是正确的设计但容易出错 |
| 3 | 会话创建未要求 `agent_id` | 架构文档 vs 实际 | 架构文档说 Session 有 `agent_id` FK，但实际创建端点可能允许 null agent_id，需确认 |

### 2.8 WebSocket `api/websocket.py`

**调试步骤**：

```javascript
// 浏览器控制台
const socket = io('http://localhost:8008', {
  auth: { token: 'your-jwt-token' }
});
socket.on('connected', (data) => console.log('Connected:', data));
socket.emit('join_session', { session_id: 'your-session-id' });
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 前端未使用 SocketIO 客户端 | `frontend/` 全局 | 架构文档描述了完整的 WebSocket 事件流，但前端代码中未找到 `socket.io-client` 依赖。`package.json` 中没有此依赖。WebSocket 功能在前端未实现 |
| 2 | WebSocket 代理路径 | `next.config.js:17-19` | `/ws/:path*` 代理到后端，但 SocketIO 默认使用 `/socket.io/` 路径，rewrite 规则可能不匹配 |

### 2.9 OpenHarness 核心引擎

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "
from openharness.engine.query_engine import QueryEngine
from openharness.tools import get_tool_registry
print('QueryEngine imported OK')
tools = get_tool_registry()
print(f'Tools: {len(tools)} registered')
"
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `openharness/config/settings.py` 有自己的配置体系 | `openharness/config/settings.py` (7.55KB) | OCH 的 `app/config.py` 和 OpenHarness 的 `config/settings.py` 两套配置可能冲突，需确认优先级 |
| 2 | MSA (语义检索) 子包是新增的 | `openharness/msa/` | 架构文档中未提及 MSA 模块，这是新增的语义检索功能，文档需补充 |
| 3 | `auth/` 子包存在但 OCH 有自己的认证 | `openharness/auth/` | OpenHarness 自带认证（Copilot Auth、OAuth），与 OCH 的 JWT 认证体系独立，需确认是否需要集成 |

### 2.10 空目录问题

| 目录 | 状态 | 说明 |
|------|------|------|
| `backend/app/schemas/` | 空目录 | 架构文档未提及 schemas，API 直接用 `request.get_json()` 解析，缺少请求/响应验证 |
| `backend/app/utils/` | 空目录 | 未使用，可删除或补充工具函数 |

**调整建议**：
- `schemas/` 应添加 Pydantic schema 或 marshmallow schema 进行请求验证
- `utils/` 要么删除，要么添加通用工具函数（如分页计算、脱敏等）

---

## 三、前端模块调试

### 3.1 依赖安装与启动

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `next.config.js` 中 WebSocket rewrite 可能不正确 | `next.config.js:17-19` | `/ws/:path*` → `${BACKEND_URL}/ws/:path*`，但 SocketIO 使用 `/socket.io/*` 路径，应改为 `/socket.io/:path*` |
| 2 | Docker 环境下前端使用 `npm run dev` | `docker-compose.yml:70` | 生产镜像用多阶段构建了 standalone 模式，但 `command: npm run dev` 会覆盖 Dockerfile 的 CMD，导致总是以开发模式运行 |
| 3 | `BACKEND_URL` 在 Docker 中为 `http://backend:8008` | `docker-compose.yml:64` | 但 `next.config.js` 的 rewrite 在服务端执行，`http://backend:8008` 可达。SSE 代理 `route.ts` 也读取 `BACKEND_URL`，这是正确的 |

### 3.2 API 客户端 `lib/api.ts`

**调试步骤**：

```bash
# 检查 API 连通性
cd /home/xxh/openclaw-harness/frontend
curl http://localhost:3000/api/v1/health  # 应代理到后端
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | SSE 流式聊天不经过 rewrite 代理 | `api.ts:114` | `streamChat()` 直接请求 `/api/proxy/chat`，这是正确的（Next.js rewrite 不支持 SSE），但需确保 Route Handler 正常工作 |
| 2 | `getHeaders()` 在 SSR 时 `localStorage` 不可用 | `api.ts:26-31` | 已用 `typeof window !== 'undefined'` 守护，OK |
| 3 | 超时 30 秒对于长对话可能不够 | `api.ts:37` | AI 生成+工具执行可能超过 30 秒，建议聊天请求使用更长的超时 |

### 3.3 认证流程 `AuthProvider.tsx`

**调试步骤**：

1. 访问 `http://localhost:3000` — 应重定向到 `/login`
2. 输入任意用户名（开发模式）登录
3. 检查 `localStorage` 中 `och_token` 是否存在

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `AuthProvider` 只检查 token 存在性 | `AuthProvider.tsx:13` | `!!token` 只检查 token 非空，不验证有效性。如果 token 已过期，用户不会被重定向到登录页，直到 API 调用返回 401 |
| 2 | 没有全局 401 拦截 | `api.ts` 全局 | 当 API 返回 401 时，应自动清除 token 并重定向到登录页。当前 `api.ts` 只抛出错误，未处理 401 |
| 3 | 登录页未处理 token 已存在的情况 | `login/page.tsx` | 如果用户已登录再访问 `/login`，应重定向到首页 |

**调整建议**：在 `api.ts` 的 `request()` 方法中添加 401 响应拦截，自动清除 `localStorage.och_token` 并跳转 `/login`。

### 3.4 页面组件

**各页面调试检查清单**：

| 页面 | 路由 | 检查要点 |
|------|------|---------|
| Dashboard | `/` | API 调用 `/sessions`, `/agents`, `/audit` 是否返回正确格式 |
| Login | `/login` | 开发模式无密码登录是否正常 |
| Chat | `/chat` | SSE 流式是否工作，quick-create Agent + Session 是否成功 |
| Agents | `/agents` | CRUD 操作是否正常，权限配置是否保存 |
| Sessions | `/sessions` | 列表分页、状态筛选是否正常 |
| Tasks | `/tasks` | 任务创建、状态更新是否正常 |
| Skills | `/skills` | 技能列表是否加载 |
| Tools | `/tools` | 工具列表是否显示 |
| Audit | `/audit` | 审计日志是否有数据 |
| Settings | `/settings` | 配置读取和更新是否正常 |
| Swarm | `/swarm` | 团队管理是否正常 |

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `components/chat/` 等目录为空 | `components/chat/`, `coordinator/`, `dashboard/`, `skills/`, `tools/` | 架构文档描述了 `MemorySidebar`, `ToolCallCard` 等组件，实际它们位于 `app/chat/` 中。组件目录结构应整理 |
| 2 | `(dashboard)/` 路由组下所有目录为空 | `app/(dashboard)/` | 子路由如 `agents/[agentId]/edit/`、`chat/[sessionId]/` 等目录存在但无页面文件，这些详情页未实现 |
| 3 | `(auth)/` 路由组为空 | `app/(auth)/` | 未使用，可删除 |
| 4 | `hooks/` 根目录为空 | `hooks/` | 自定义 hooks 在 `lib/hooks/` 中，根 `hooks/` 目录多余 |
| 5 | `styles/themes/` 为空 | `styles/themes/` | 主题通过 CSS 变量实现，此目录多余 |

### 3.5 类型定义 `lib/types.ts`

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/frontend
npx tsc --noEmit
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `ToolPermission.path_rules` 类型为 `string[]` | `types.ts:43` | 后端模型中 `path_rules` 是 JSON 类型，实际可能为对象数组而非字符串数组 |
| 2 | `Task` 类型字段与后端不完全对齐 | `types.ts:86-102` | 前端有 `title`, `description`, `priority`, `progress`, `parent_task_id` 等字段，但后端 Task 模型字段为 `task_type`, `command`, `exit_code`, `pid` 等，差异较大 |
| 3 | 缺少 `Team`, `TeamMember`, `MCPServer`, `Plugin` 类型 | `types.ts` | 后端有这些模型但前端未定义对应类型 |

---

## 四、基础设施调试

### 4.1 Docker Compose

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness
docker compose up -d postgres redis  # 先启动数据库
docker compose up backend            # 再启动后端
docker compose up frontend           # 最后启动前端
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `frontend` 用 dev 模式运行 | `docker-compose.yml:70` | `command: npm run dev -- -H 0.0.0.0` 覆盖了 Dockerfile 的生产构建，应该用 `npm run start` 启动 standalone 产物 |
| 2 | `backend` volumes 挂载了源码 | `docker-compose.yml:52` | `./backend:/app` 方便开发但不符合生产部署，生产应去掉此挂载 |
| 3 | 缺少 `.env.example` 文件 | 项目根目录 | `start.sh:79` 引用了 `.env.example`，但项目中不存在此文件 |
| 4 | `ADMIN_PASSWORD` 不在 `.env` 中 | `.env` | Docker Compose 通过 `env_file: - .env` 注入环境变量，但 `.env` 中没有 `ADMIN_PASSWORD` |

### 4.2 Infrastructure 目录

| 目录 | 状态 | 调整建议 |
|------|------|---------|
| `infrastructure/nginx/` | 空 | 应添加 nginx.conf 反向代理配置 |
| `infrastructure/postgres/` | 空 | 应添加 init.sql 或迁移脚本 |
| `infrastructure/redis/` | 空 | 应添加 redis.conf 配置 |

### 4.3 Backend Dockerfile

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 使用 `python:3.11-slim` | `backend/Dockerfile:1` | `requirements.txt` 中部分依赖（如 `asyncpg`）需要编译，`slim` 镜像可能缺少编译工具。当前有 `build-essential` 但增加了镜像体积 |
| 2 | 未安装 Node.js | — | 部分前端相关工具可能需要 Node.js，但当前后端 Dockerfile 不包含 |

---

## 五、模块间集成调试

### 5.1 前后端认证联调

**调试步骤**：

```bash
# 1. 启动后端
cd /home/xxh/openclaw-harness/backend && python -m app.main

# 2. 启动前端
cd /home/xxh/openclaw-harness/frontend && npm run dev

# 3. 访问 http://localhost:3000/login 登录
# 4. 打开浏览器 DevTools Network 查看 API 请求
```

**问题与调整**：

| # | 问题 | 说明 |
|---|------|------|
| 1 | CORS 配置需包含前端地址 | 后端 `CORS_ORIGINS` 默认包含 `http://localhost:3000`，本地开发OK，但 Docker 环境需额外配置 |
| 2 | 前端 API 代理链路 | `/api/v1/*` → Next.js rewrite → Backend:8008，SSE 走 `/api/proxy/chat` Route Handler |
| 3 | Token 格式 | 后端 JWT payload: `{sub, username, role, exp, iat}`，前端 `AuthProvider` 只检查存在性 |

### 5.2 聊天流程联调

**调试步骤**：

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Quick-create Agent
AGENT_ID=$(curl -s -X POST http://localhost:8008/api/v1/agents/quick-create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-agent"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent',d).get('id',''))")

# 3. 创建 Session
SESSION_ID=$(curl -s -X POST http://localhost:8008/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"test\", \"agent_id\": \"$AGENT_ID\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

# 4. 发送聊天 (SSE)
curl -N -X POST "http://localhost:8008/api/v1/sessions/$SESSION_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": true}'
```

**问题与调整**：

| # | 问题 | 说明 |
|---|------|------|
| 1 | AI 调用需要 API Key | `ANTHROPIC_API_KEY` 和 `OPENAI_API_KEY` 都为空，聊天会返回 LLM 调用失败 |
| 2 | OpenHarness QueryEngine 集成 | 需要确认 `sessions.py` 中的 `_generate_ai_response()` 是否正确调用 OpenHarness 的 `QueryEngine` |
| 3 | 工具执行权限 | 架构文档描述了三层权限检查（DenialTracker → PermissionChecker → DB PermissionRule），需要确认实际实现 |

### 5.3 WebSocket 联调

**问题**：前端未实现 WebSocket 客户端，`package.json` 中没有 `socket.io-client` 依赖。

**调整建议**：

```bash
cd /home/xxh/openclaw-harness/frontend
npm install socket.io-client
```

然后在前端创建 WebSocket 连接管理模块。

---

## 附：各模块独立调试命令速查

### 后端模块

| 模块 | 调试命令 |
|------|---------|
| 配置 | `python3 -c "from app.config import get_settings; print(get_settings().dict())"` |
| 数据库 | `python3 -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"` |
| 安全 | `python3 -c "from app.core.security import create_jwt, verify_token; t=create_jwt({'sub':'test','username':'test','role':'admin'}); print(verify_token(t))"` |
| 异步工具 | `python3 -c "from app.core.async_utils import run_async; print(run_async(asyncio.sleep(0.1)))"` |
| 认证 API | `curl -X POST http://localhost:8008/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"admin"}'` |
| 健康检查 | `curl http://localhost:8008/health` |
| 中间件 | `curl http://localhost:8008/api/v1/middleware` |
| Swagger | `curl http://localhost:8008/apispec.json` |

### 前端模块

| 模块 | 调试命令 |
|------|---------|
| 类型检查 | `npx tsc --noEmit` |
| 构建 | `npm run build` |
| 测试 | `npm test` |
| Lint | `npm run lint` |

### Docker 环境

| 操作 | 命令 |
|------|------|
| 启动全部 | `docker compose up -d` |
| 查看日志 | `docker compose logs -f backend` |
| 重启后端 | `docker compose restart backend` |
| 进入容器 | `docker compose exec backend bash` |
| 清理重建 | `docker compose down -v && docker compose up --build -d` |

---

## 六、深度审查 — 第二轮问题（模型层 + 服务层）

### 6.1 模型层数据完整性问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `MemoryFact` 使用旧式 `Column()` 而非 `Mapped[]` + `mapped_column()` | `memory_fact.py:29-56` | 所有其他模型都使用了 Mapped 风格，MemoryFact 是唯一的旧式写法，风格不一致，且缺少类型提示 |
| 2 | `ToolPermission` 缺少 `(agent_id, tool_name)` 联合唯一约束 | `agent.py:77-78` | 同一 Agent 对同一工具可以创建多条权限记录，导致数据冗余和歧义，应添加 `UniqueConstraint('agent_id', 'tool_name')` |
| 3 | `TaskDependency` 缺少 `(task_id, dep_task_id)` 联合唯一约束 | `task.py:89-94` | 同一任务可以重复添加相同的依赖关系，应添加唯一约束防止循环和重复依赖 |
| 4 | `Task.status` 无 CHECK 约束 | `task.py:32` | `status` 字段是 String(16)，任意值都可写入。应添加 CHECK 约束或使用 Enum 限制为 `pending/running/completed/failed/stopped` |
| 5 | `Session.status` 无 CHECK 约束 | `session.py:29` | 同上，应限制为 `active/paused/completed` |
| 6 | `TeamMember.assigned_task_id` 不是 FK | `team.py:78` | 引用了任务 ID 但没有 ForeignKey 约束，数据完整性无法保证 |
| 7 | `Agent.to_dict()` 缺少 `created_by` 字段 | `agent.py:52-66` | 模型有 `created_by` 列但 `to_dict()` 未输出此字段 |
| 8 | `Session.to_dict()` 的 `metadata` 字段名与模型列名不一致 | `session.py:71` | 模型中 `metadata_` 映射到 `metadata` 列，`to_dict()` 输出 `metadata` 键，与前端交互正确但容易混淆 |
| 9 | `Message.tool_results` 使用 `lazy='selectin'` | `message.py:43-44` | 每次加载 Message 都会自动加载所有 ToolResult，在批量获取消息列表时导致 N+1 预加载，应改为 `lazy='noload'` + 按需加载 |
| 10 | `Team.members` 使用 `lazy='selectin'` | `team.py:38-42` | 同上，列表查询时不必要地加载所有成员，应用 `selectinload` 按需控制 |

### 6.2 服务层问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `SessionService.stream_chat()` 是 Mock | `session_service.py:232-295` | `_simulate_stream()` 返回硬编码文本，`QueryEngine(config=config)` 创建后未赋值也未使用。注释中的 TODO 表明实际对接尚未实现 |
| 2 | `SessionService` 构造函数需要 `db: AsyncSession` | `session_service.py:25` | 但 API 层 (sessions.py) 并未使用 SessionService，而是直接操作数据库，导致 SessionService 未被实际调用 |
| 3 | `PermissionService` 状态仅存内存 | `permission_service.py:35-37` | `_path_rules`、`_denial_log`、`_current_mode` 都在内存中，进程重启后丢失。而 API 层 (permissions.py) 使用 DB 持久化 `PermissionRule`，两者数据不同步 |
| 4 | `PermissionService` 和 `permissions.py` API 逻辑重复 | 两个文件 | API 层直接操作 DB 的 `PermissionRule`，服务层使用内存 `_path_rules`，两套独立的权限规则系统 |
| 5 | `PluginService` 状态仅存内存 | `plugin_service.py:22` | `_plugins` 字典在内存中，进程重启后所有插件信息丢失。而 `plugins.py` API 使用 DB `Plugin` 模型持久化，两者不互通 |
| 6 | `PluginService.install_plugin()` 使用同步 `subprocess.run` | `plugin_service.py:172-178, 184-189` | 在 `async` 方法中使用 `subprocess.run` 会阻塞事件循环，应使用 `asyncio.create_subprocess_exec` |
| 7 | `SkillService` 的 `enable_skill()` 和 `disable_skill()` 是空实现 | `skill_service.py:145-153` | 两个方法都只返回 `True`，注释说"TODO: 实现"，功能未实现 |
| 8 | `CoordinatorService.spawn_subagent()` 返回的字典未持久化 | `coordinator_service.py:152-180` | 创建的 `sub_task` 只是内存字典，不存入 DB，进程重启后丢失 |
| 9 | `CoordinatorService.get_task_dependencies()` 返回空数据 | `coordinator_service.py:182-187` | 总是返回 `{'nodes': [], 'edges': []}`，功能未实现 |
| 10 | `DualPoolSubagentExecutor._execute_task()` 使用 Mock | `subagent_executor.py:148-180` | 调用 `_mock_agent_stream()` 而非真正的 Agent Loop，未连接 LLM |
| 11 | `DualPoolSubagentExecutor.get_stats()` 访问私有属性 | `subagent_executor.py:235-236` | `self._scheduler_pool._work_queue.qsize()` 访问 ThreadPoolExecutor 的私有属性 `_work_queue`，Python 版本升级后可能不可用 |
| 12 | `ToolService.execute_tool()` 调用 `registry.execute()` | `tool_service.py:111` | 但 `FallbackToolRegistry.execute()` 只返回字符串，而 API 层 (sessions.py 的 `_execute_tool()`) 完全绕过了 ToolService，使用自己的 mock 逻辑 |

---

## 七、深度审查 — 第三轮问题（API + 配置 + 基础设施）

### 7.1 额外 API 模块问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `permissions.py` 中 `_current_permission_mode` 是模块级全局变量 | `permissions.py:69` | 只在当前进程生效，多 worker 部署时各 worker 模式不一致。应持久化到 DB 或 Redis |
| 2 | `permissions.py` 的 `check_tool_permission()` 中嵌套 `async def _check_db_rules()` | `permissions.py:582-593` | 在同步函数中定义异步函数并通过 `run_async()` 调用，如果外层已在 `run_async()` 上下文中会死锁 |
| 3 | `channels.py` 所有渠道数据在内存中 | `channels.py:28` | `_registered_channels` 是内存字典，重启丢失。应持久化到 DB |
| 4 | `channels.py` 渠道淘汰策略不合理 | `channels.py:158-161` | `while len >= MAX: del oldest` 使用 FIFO 淘汰，但在 Python 3.7+ 中 dict 是有序的，新注册的渠道在尾部，淘汰头部的最旧渠道 — 但如果频繁注册和注销，可能导致意外淘汰 |
| 5 | `channels.py` `send_message()` 是 Mock | `channels.py:242-249` | 注释说"实际实现中调用 openharness.channels.impl.{type}.send()"，但未实现 |
| 6 | `sandbox.py` 的 `_execute_locally()` 无任何安全检查 | `sandbox.py:208-224` | 当 `use_sandbox=False` 或沙箱不可用时，直接执行用户输入的命令，存在命令注入风险。应至少进行基本危险命令过滤 |
| 7 | `sandbox.py` 的安全检查使用简单 `in` 匹配 | `sandbox.py:338` | `if pattern.lower() in command.lower()` 会导致误报，例如 `format` 匹配到 `information`。应使用正则或更精确的模式匹配 |
| 8 | `config.py` 的 `update_config()` 直接 setattr 到 Pydantic Settings 对象 | `config_api.py:112` | `setattr(settings, key, data[key])` 绕过了 Pydantic 的验证逻辑，可能导致无效值。且这些更改不会持久化（`.env` 文件未修改） |
| 9 | `config.py` 的 `reset_config()` 是空实现 | `config_api.py:119-123` | 只返回消息但不实际重置任何配置 |
| 10 | `config.py` 的 `test_provider()` 测试延迟为 0ms | `config_api.py:201-206` | `start = time.time()` 后立即计算 `latency_ms`，没有实际测试连接，只是一个占位 |
| 11 | `mcp.py` 的 `test_mcp_connection()` 不是真正测试 | `mcp.py:254-276` | 只测量了数据库查询时间，没有实际连接 MCP 服务器。无论服务器是否可达都返回 `status: 'ok'` |
| 12 | `mcp.py` 的 `add_mcp_server()` 未验证 `type` 字段 | `mcp.py:113` | `server_type=data.get('type', 'stdio')` 接受任意字符串，应限制为 `stdio` 或 `streamable-http` |
| 13 | `plugins.py` 的 `enable_plugin()` 不限制角色 | `plugins.py:113-124` | `enable/disable` 只需 `@require_auth`（任何认证用户），而 `install/uninstall` 需要 `@require_role('admin')`。启用/禁用插件应有更严格的权限控制 |

### 7.2 配置一致性问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `requirements.txt` 中 `httpx` 重复声明 | `requirements.txt:38,62` | 第 38 行 `httpx>=0.25.0` 和第 62 行 `httpx>=0.25.0` 重复，应去重 |
| 2 | `alembic.ini` 缺少 `sqlalchemy.url` 配置 | `backend/alembic.ini` | 标准的 alembic.ini 应包含 `sqlalchemy.url`，当前依赖 `env.py` 动态设置，但缺少 fallback 时迁移命令可能失败 |
| 3 | 迁移脚本 001 中 `sessions.agent_id` 是 `nullable=False` | `alembic/versions/001_initial_schema.py:37` | 但模型定义 `session.py:28` 是 `nullable=True`。迁移脚本与模型定义不一致，Alembic autogenerate 会检测到差异并尝试修改 |
| 4 | `ToolResult.completed_at` 在迁移中 `server_default=sa.func.now()` | `alembic/versions/001_initial_schema.py:78` | 但模型定义 `message.py:82` 是 `nullable=True` 无默认值，迁移自动设置了创建时间，不一致 |
| 5 | `mcp_servers` 表缺少 `name` 唯一约束 | `alembic/versions/002_add_skills_teams_mcp_memory.py:68` | 模型中 `MCPServer.name` 没有设置 `unique=True`，但实际业务场景中 MCP 服务器名称应该唯一，否则会创建重复配置 |

### 7.3 前端依赖与配置问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `package.json` 缺少 `socket.io-client` | `frontend/package.json` | 后端有完整的 WebSocket/SockerIO 实现，但前端未安装 `socket.io-client` 依赖 |
| 2 | `package.json` 缺少 `aiofiles` 的前端等价物 | — | 后端 `skill_service.py` 使用 `aiofiles`，前端技能管理页面可能需要异步文件操作支持 |
| 3 | `next.config.js` 缺少 MCP API 路由代理 | `next.config.js` | 后端有 `/api/v1/mcp/*` 端点，但前端 `next.config.js` 的 rewrite 规则未覆盖 MCP 路由 |

---

## 八、深度审查 — 第四轮问题（安全 + 边界条件 + 数据一致性）

### 8.1 安全漏洞

| # | 严重度 | 问题 | 位置 | 调整建议 |
|---|--------|------|------|---------|
| 1 | **高** | 沙箱本地模式无命令过滤 | `sandbox.py:208-224` | `_execute_locally()` 直接 `subprocess.run(shlex.split(command))`，任何认证用户都可以通过 API 执行任意系统命令 |
| 2 | **高** | `ADMIN_PASSWORD` 明文 vs bcrypt 不匹配 | `auth.py:51` | `verify_password(password, settings.ADMIN_PASSWORD)` 将明文密码当作哈希使用，导致生产环境登录永远失败 |
| 3 | **高** | 开发模式无密码即 admin | `auth.py:46` | 任何用户名都能获得 `role='admin'` 的 JWT token，如果误在生产环境设置 `APP_ENV=development`，将导致严重安全问题 |
| 4 | **中** | 配置 API 直接 setattr 绕过验证 | `config_api.py:112` | `setattr(settings, key, data[key])` 不经过 Pydantic 验证，可以设置无效值（如 `OPENHARNESS_MAX_TOKENS=-1`） |
| 5 | **中** | `SECRET_KEY` 默认值为 `change-me-in-production` | `config.py` | 如果生产环境未修改，JWT 签名可被伪造 |
| 6 | **中** | 安全检测模式使用简单 `in` 匹配 | `sandbox.py:338` | `format` 会匹配 `information`，导致误报；同时也容易被绕过（如 `rm  -rf  /` 双空格） |
| 7 | **低** | CORS 默认允许 localhost | `config.py:39` | 本地开发正常，但生产部署时需要配置实际域名 |

### 8.2 SSE 流式边界条件

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | SSE 流中 `asyncio.run()` 与 Flask 线程冲突 | `sessions.py` | Flask 的 SSE 在独立线程中运行，内部调用 `asyncio.run()` 创建新事件循环。如果该线程中已有其他异步操作，会抛出 `RuntimeError` |
| 2 | SSE 客户端断开时服务端无感知 | `sessions.py` | `stream_with_context` 在客户端断开后可能继续生成数据，浪费资源。应添加 `request.environ.get('werkzeug.socket')` 检测或使用 `generate()` 中的 `should_abort` 信号 |
| 3 | 长时间流式响应可能超时 | `api.ts:37` | 前端 30 秒超时对于需要工具执行的长对话不够。AI 回复可能涉及多轮工具调用，单次响应可能超过 5 分钟 |
| 4 | SSE 流中 `queue.Queue` 无大小限制 | `sessions.py` | 如果消费端（Flask 响应线程）慢于生产端（异步生成器），队列会无限增长，可能导致内存溢出 |

### 8.3 竞态条件与资源泄漏

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_compact_cache` 全局单例无锁保护 | `cache_service.py:9` | 多线程并发调用 `get_compact_cache()` 可能创建多个实例 |
| 2 | `_hook_executor` 全局单例无锁保护 | `hook_service.py:10` | 同上，但更危险，因为 `HookExecutor` 可能涉及状态变更 |
| 3 | `DualPoolSubagentExecutor._running_count` 用 `Lock()` 但调度循环用 `time.sleep(0.5)` 忙等待 | `subagent_executor.py:125` | 当并发已满时，调度线程持续占用 CPU 等待槽位释放，应使用 `threading.Condition` 或 `threading.Semaphore` |
| 4 | `DualPoolSubagentExecutor._tasks` 字典无大小限制 | `subagent_executor.py:80` | 如果不断提交任务但从不清理，已完成的任务会永远留在内存中，应添加 LRU 淘汰或定期清理 |
| 5 | `PermissionService._denial_log` 截断时重新创建列表 | `permission_service.py:192` | `self._denial_log = self._denial_log[-5000:]` 创建新列表，如果在并发写入时可能丢失记录。应使用 `collections.deque(maxlen=10000)` |

### 8.4 数据库迁移与索引

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 迁移脚本 001 与模型定义不一致：`sessions.agent_id` | `001_initial_schema.py:37` vs `session.py:28` | 迁移中 `nullable=False`，模型中 `nullable=True`。执行 `alembic upgrade head` 后再 `alembic revision --autogenerate` 会检测到差异 |
| 2 | `ToolResult.completed_at` 迁移有 `server_default` 但模型没有 | `001_initial_schema.py:78` vs `message.py:82` | 同上，迁移自动设置 `sa.func.now()` 作为默认值，但模型中 `nullable=True` 无默认值 |
| 3 | 缺少 `sessions.created_at` 索引 | — | Session 列表按 `updated_at` 排序但经常按 `agent_id` 过滤，已有 `agent_id` 索引但无 `created_at` 索引 |
| 4 | `messages` 表缺少 `(session_id, created_at)` 复合索引 | — | 获取会话消息时按 `session_id` 过滤 + `created_at` 排序，复合索引可大幅提升性能 |
| 5 | `audit_logs` 缺少 `(user_id, created_at)` 复合索引 | — | 按用户筛选审计日志 + 按时间排序是常见查询模式 |
| 6 | `task_dependencies` 缺少 `(dep_task_id)` 索引 | — | 反向查找"哪些任务依赖于我"时需要此索引 |

### 8.5 错误处理边界

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `alembic/env.py` 中 `from app.models import *` 在 venv 外可能失败 | `alembic/env.py:13` | 如果在非 venv 环境执行 `alembic upgrade`，`app.models` 可能找不到（依赖未安装），应添加 `try/except` 和清晰的错误提示 |
| 2 | `permissions.py` 中 `from openharness.permissions.denial_tracking import get_denial_tracker` 在顶层导入 | `permissions.py:15` | 如果 `openharness` 不完整安装，整个 Blueprint 无法加载，应延迟导入或在 `except` 中提供降级 |
| 3 | `memory.py` 中 `MemoryFact.tags.contains([tag])` SQLite 不支持 | `memory.py:99` | SQLite 不支持 JSON `contains` 操作，开发模式下使用 SQLite 会报错 |
| 4 | `session_service.py` 中 `func.json_array_length(Message.tool_uses)` SQLite 不支持 | `session_service.py:318-321` | `json_array_length` 是 PostgreSQL 函数，SQLite 中不存在 |
| 5 | `memory.py` 中 `func.lower(MemoryFact.content)` 搜索在大量数据时性能差 | `memory.py:201` | `ilike` 搜索无法使用索引，大量记忆事实时查询会很慢。应考虑全文搜索或 MSA 向量检索 |

### 8.6 前后端类型对齐

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 前端 `Task` 类型完全偏离后端模型 | `types.ts:86-102` | 前端有 `title/description/priority/progress`，后端有 `task_type/command/exit_code/pid`。前端代码无法正确渲染任务列表 |
| 2 | 前端缺少 `Team`/`TeamMember`/`MCPServer`/`Plugin` 类型 | `types.ts` | 后端有完整的 CRUD API，但前端未定义这些类型，导致 `/swarm`、`/tools` (MCP)、`/settings` (Plugins) 页面无法正确交互 |
| 3 | 前端 `ToolPermission.path_rules` 类型可能不匹配 | `types.ts:43` | 前端定义为 `string[]`，后端 `agent.py:80` 定义为 `Optional[List[Dict]]`（对象数组），实际是路径规则对象数组而非字符串数组 |
| 4 | `MCPServer.to_dict()` 输出 `type` 而非 `server_type` | `mcp_server.py:57` | `to_dict()` 中键名是 `'type': self.server_type`，但模型字段名是 `server_type`，前端如果按 `server_type` 取值会取不到 |

---

## 9. Round 3: OpenHarness 核心集成 + 配置一致性 + 边缘案例

本轮深入审查 OCH 服务层与 OpenHarness 核心引擎的集成接口，发现大量 API 签名不匹配、不存在类/函数的导入、以及配置系统冲突问题。这些问题意味着当前代码在运行时会直接抛出 `ImportError`、`TypeError` 或 `AttributeError`，核心功能完全无法工作。

### 9.1 OpenHarness 核心集成 API 不匹配（严重 - 运行时崩溃）

#### 9.1.1 `OpenHarnessConfig` 类不存在

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `from openharness.config import OpenHarnessConfig` — 该类不存在 | `session_service.py:199` | `openharness/config/__init__.py` 只导出 `Settings`, `get_config_dir`, `get_config_file_path`, `get_data_dir`, `get_logs_dir`, `load_settings`。应改为 `from openharness.config import Settings` 并使用 `Settings` |
| 2 | `OpenHarnessConfig()` 无参构造 — 即使改为 `Settings()` 也需注意 | `session_service.py:218` | `openharness.config.Settings` 是 `pydantic.BaseModel`（非 BaseSettings），构造时需要 `api_key` 等必要字段或通过 `_apply_env_overrides()` 读取环境变量。应使用 `load_settings()` 函数加载，它内部会调用 `_apply_env_overrides()` |

#### 9.1.2 `QueryEngine` 构造函数签名完全错误

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `QueryEngine(config=config)` — 不接受 `config` 参数 | `session_service.py:219` | 实际签名为 `QueryEngine(*, api_client: SupportsStreamingMessages, tool_registry: ToolRegistry, permission_checker: PermissionChecker, cwd: str | Path, model: str, system_prompt: str, max_tokens: int = 4096, max_turns: int = 8, ...)`。必须逐个传入 6 个必选关键字参数 |
| 2 | `QueryEngine` 创建后未赋值也未使用 | `session_service.py:219` | 即使修正构造函数，`QueryEngine(...)` 返回值被丢弃，代码继续执行到 `self._simulate_stream()` mock。应将 QueryEngine 赋值给变量并调用 `submit_message()` |
| 3 | 缺少 `api_client` 实现 — OCH 没有 `SupportsStreamingMessages` 适配器 | `session_service.py` 全文 | QueryEngine 需要 `api_client: SupportsStreamingMessages`（具有 `stream_messages()` 方法的对象），OCH 没有实现此接口。需要创建适配器类，包装 `httpx` 或 `anthropic` SDK 客户端 |

#### 9.1.3 `ToolRegistry` API 全面不匹配

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `from openharness.tools import get_default_tool_registry` — 函数名错误 | `tool_service.py:25` | 实际导出名是 `create_default_tool_registry`，应改为 `from openharness.tools import create_default_tool_registry` |
| 2 | `self.registry.list_tools()` 返回值类型错误处理 | `tool_service.py:41` | `ToolRegistry.list_tools()` 返回 `list[BaseTool]`（工具对象列表），但代码将其当作字符串名称列表处理。应改为 `[t.name for t in self.registry.list_tools()]` |
| 3 | `self.registry.get_tool_info(tool_name)` — 方法不存在 | `tool_service.py:42` | `ToolRegistry` 只有 `get(name: str) -> BaseTool | None`，无 `get_tool_info()`。应改为 `tool = self.registry.get(tool_name)`，然后从 `BaseTool` 对象获取信息 |
| 4 | `self.registry.get_schema(tool_name)` — 方法不存在 | `tool_service.py:65` | `ToolRegistry` 没有 `get_schema()` 方法。应改为 `tool = self.registry.get(tool_name)`，然后使用 `tool.input_schema` 或 `tool.get_schema()` 获取 schema |
| 5 | `await self.registry.execute(tool_name, input_data)` — 签名错误 | `tool_service.py:111` | 实际 `BaseTool.execute()` 签名为 `execute(arguments: BaseModel, context: ToolExecutionContext)`。不是在 registry 上调用，而是 `tool = self.registry.get(tool_name)` 然后 `await tool.execute(parsed_args, context)` |
| 6 | 缺少 `ToolExecutionContext` 构建 | `tool_service.py` 全文 | 调用 `tool.execute()` 需要传入 `ToolExecutionContext`，该上下文需要 `cwd`、`permission_checker` 等依赖，当前代码完全没有构建 |

#### 9.1.4 `SandboxAvailability` 属性缺失 + 适配器函数不存在

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `availability.provider` — 属性不存在 | `sandbox.py:46` | `SandboxAvailability` dataclass 只有 `enabled: bool`, `available: bool`, `reason: str | None`, `command: str | None`，没有 `provider`。应删除此访问或改用 `availability.command` 推断 provider |
| 2 | `availability.runtime_path` — 属性不存在 | `sandbox.py:47` | 同上，应删除此访问。`SandboxAvailability` 不包含路径信息 |
| 3 | `availability.version` — 属性不存在 | `sandbox.py:48` | 同上，应删除此访问。如需版本信息，应在 `SandboxAvailability` 中添加 `version` 字段 |
| 4 | `get_sandbox_config()` — 函数不存在 | `sandbox.py:36` | `openharness.sandbox.adapter` 没有 `get_sandbox_config()` 函数。只有 `get_sandbox_availability()` 和 `wrap_command_for_sandbox()`。应删除此导入，自行从 OCH Settings 获取配置 |
| 5 | `is_host_bash_allowed()` — 函数不存在 | `sandbox.py:37` | `openharness.sandbox.adapter` 没有此函数。应自行实现此逻辑或从 OCH 配置读取 |

#### 9.1.5 `wrap_command_for_sandbox` 签名不匹配

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 传入 `str` 但期望 `list[str]` | `sandbox.py:190` | 实际签名 `wrap_command_for_sandbox(command: list[str], *, settings=None) -> tuple[list[str], Path | None]`。OCH 传入的是字符串，应改为 `wrap_command_for_sandbox(command.split())` 或将命令构建为列表 |
| 2 | 返回值类型不匹配 — 返回 `tuple[list[str], Path | None]` | `sandbox.py:190` | 代码忽略返回值，但实际返回的是包装后的命令列表和可选的临时脚本路径。应使用返回值替换原始命令 |

#### 9.1.6 `PermissionMode` 枚举值不匹配

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `PERMISSION_MODES['auto']` 键不存在于 `PermissionMode` 枚举 | `permission_service.py` | `PermissionMode` 枚举只有 `DEFAULT="default"`, `PLAN="plan"`, `FULL_AUTO="full_auto"`，没有 `AUTO="auto"`。应将 `auto` 改为 `full_auto`，或在枚举中添加 `AUTO` 值 |
| 2 | OCH 自定义的 `SimpleSettings` 不完全实现 `PermissionSettings` 接口 | `permissions.py:435-451` | `SimpleSettings` 的 `denied_tools`/`allowed_tools` 使用 `set` 类型，但 `PermissionSettings` 可能期望 `list[str]`。此外缺少 `permission_mode` 字段映射 |

### 9.2 配置系统一致性问题

#### 9.2.1 双 Settings 系统耦合冲突

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | OCH `app/config.py` 和 OpenHarness `openharness/config/settings.py` 共享环境变量 | `config.py` / `settings.py` | 两套 Settings 都读取 `OPENHARNESS_MAX_TOKENS`、`OPENHARNESS_MAX_TURNS`、`ANTHROPIC_API_KEY`，形成隐式耦合。应明确单一配置源，OCH 应将 OpenHarness 的配置项透传而非重复定义 |
| 2 | OCH 默认值覆盖 OpenHarness 更优默认值 | `config.py:OPENHARNESS_MAX_TOKENS=4096` vs `settings.py:max_tokens=16384` | OCH 设置 `OPENHARNESS_MAX_TOKENS=4096`，OpenHarness 默认 `max_tokens=16384`。由于 OpenHarness 的 `_apply_env_overrides()` 读取同一环境变量，OCH 的较低值会覆盖 OpenHarness 的较高默认值。应将 OCH 默认值提升到 16384 或删除重复定义 |
| 3 | OCH 默认 `max_turns=8` vs OpenHarness 默认 `max_turns=200` | `config.py:OPENHARNESS_MAX_TURNS=8` | 同上，OCH 的 8 轮对话上限极低（对比 OpenHarness 的 200），会严重限制 Agent 能力。应至少提升到 50 或直接使用 OpenHarness 默认值 |
| 4 | `ANTHROPIC_API_KEY` 环境变量冲突 | `.env:ANTHROPIC_API_KEY=` (空) | `.env` 中 `ANTHROPIC_API_KEY` 为空字符串，OpenHarness `_apply_env_overrides()` 会将空字符串设为 API key，导致认证失败而非缺少 key 的清晰错误。应在 OpenHarness Settings 中对空字符串做 falsy 检查 |

#### 9.2.2 `.env` 配置缺失与错误

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `ADMIN_PASSWORD` 未设置 | `.env` 缺失 | `auth.py:49-51` 使用 `os.getenv('ADMIN_PASSWORD', '')`，空密码意味着生产环境登录完全失效。应在 `.env` 中设置强密码，并添加非空校验 |
| 2 | `JWT_ALGORITHM` 未设置 | `.env` 缺失 | `auth.py` 默认 `'HS256'`，但如果环境变量拼写错误或缺失，可能导致 token 验证失败。建议在 `.env` 中显式设置 |
| 3 | `DATABASE_URL=sqlite+aiosqlite:///./och.db` — Docker 中无效 | `.env:6` | Docker 容器中使用 SQLite 相对路径 `./och.db` 会写入容器内部，容器重启后丢失。应改为 PostgreSQL URL `postgresql+asyncpg://och:och@db:5432/och` |
| 4 | `REDIS_URL=redis://localhost:6379/0` — Docker 中无效 | `.env:7` | Docker 中 Redis 容器名是 `redis`，不是 `localhost`。应改为 `redis://redis:6379/0` |
| 5 | `ANTHROPIC_API_KEY=` / `OPENAI_API_KEY=` 空值 | `.env:1-2` | 空字符串不同于未设置，某些库会将空字符串视为有效 key 导致认证失败。应删除等号或添加占位说明 |

#### 9.2.3 Redis 配置但未使用

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `requirements.txt` 包含 `redis>=5.0.0`，`.env` 定义 `REDIS_URL` | `requirements.txt:54`, `.env:7` | 整个后端代码中没有实际使用 Redis 的地方（无 `import redis` 或 `aioredis`）。要么移除依赖和配置，要么实现 Redis 缓存/发布订阅功能 |
| 2 | `docker-compose.yml` 启动 Redis 容器 | `docker-compose.yml:redis` | Redis 容器占用资源但无用途。如不需要，应移除以节省资源 |
| 3 | SocketIO 未配置 Redis 消息队列 | `main.py:socketio` | 多 worker 部署时，SocketIO 需要 Redis 或其他消息队列来跨进程广播事件。当前使用默认内存队列，多 worker 下事件会丢失 |

### 9.3 基础设施与部署边缘案例

#### 9.3.1 Docker 部署配置问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `.env` 与 `docker-compose.yml` 的服务发现不一致 | `.env` / `docker-compose.yml` | `.env` 中 `DATABASE_URL` 和 `REDIS_URL` 使用 `localhost`，但 Docker Compose 网络中服务名是 `db` 和 `redis`。需要创建 `.env.docker` 或在 compose 文件中覆盖环境变量 |
| 2 | `docker-compose.yml` 只使用 `env_file: .env` | `docker-compose.yml:14` | 无法区分开发/生产环境配置。应在 compose 的 `environment` 块中覆盖 Docker 专用变量，或使用多个 env 文件 |
| 3 | PostgreSQL 容器启动但未被使用 | `docker-compose.yml:db` | `.env` 指向 SQLite，PostgreSQL 容器白白运行。应修正 `DATABASE_URL` 指向 PostgreSQL |
| 4 | 健康检查依赖 `/health` 但未验证数据库连接 | `docker-compose.yml:healthcheck` | `/health` 只返回静态 `{"status": "ok"}`，不检查数据库或 OpenHarness 连接。容器可能"健康"但实际无法工作 |

#### 9.3.2 SQLite 兼容性问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `MemoryFact.tags.contains([tag])` — SQLite 不支持 JSON contains | `memory.py:99` | PostgreSQL 的 `jsonb` 支持 `contains`，但 SQLite 的 `json` 类型不支持。开发环境用 SQLite 会报错。应使用 `func.json_each()` 或手动过滤 |
| 2 | `func.json_array_length(Message.tool_uses)` — SQLite 无此函数 | `session_service.py:318-321` | `json_array_length` 是 PostgreSQL 内置函数。应改用 SQLAlchemy 的 `func.json_array_length` 并在 SQLite 下降级为 Python 端计算 |
| 3 | 并发写入 — SQLite 单写锁 | 全局 | SQLAlchemy Async + SQLite 在并发写入时会遇到 `database is locked`。应确保开发环境使用 WAL 模式或切换到 PostgreSQL |

#### 9.3.3 `start.sh` 问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 未检查依赖是否安装 | `start.sh` | 直接运行 `flask`/`next` 而不检查 Python/Node 是否安装或 venv 是否存在。应添加前置检查 |
| 2 | 未运行数据库迁移 | `start.sh` | 启动后端前应执行 `alembic upgrade head`，否则新部署的数据库表不存在 |
| 3 | 未设置 `FLASK_APP` 环境变量 | `start.sh` | Flask 需要 `FLASK_APP` 才能正确找到应用工厂。应添加 `export FLASK_APP=app.main:create_app()` |

#### 9.3.4 Alembic 迁移不一致

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `sessions.agent_id` — 迁移 `nullable=False`，模型 `nullable=True` | `001_initial_schema.py:37` vs `models.py` | 迁移脚本定义 `agent_id` 为 NOT NULL，但模型定义允许 NULL。后续迁移或 ORM 操作会冲突。应统一为 `nullable=True` 并创建修正迁移 |
| 2 | `ToolResult.completed_at` — 迁移有 `server_default=sa.func.now()`，模型无默认 | `001_initial_schema.py:78` vs `models.py` | 迁移定义了数据库级别的默认值，但 ORM 模型不知道这个默认值，可能导致 ORM 插入时传 `None` 而触发默认值。应在模型中添加 `server_default` 或在 Python 层设置默认值 |
| 3 | `mcp_servers` 表缺少 `name` 唯一约束 | `002_add_skills_teams_mcp_memory.py` | 模型定义 `name` 有 `unique=True`，但迁移脚本未创建唯一索引。应添加修正迁移 |

#### 9.3.5 前端代理与 API 边缘案例

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `NEXT_PUBLIC_API_URL` 默认相对路径 `/api/v1` — SSR 时无法解析 | `lib/api.ts:3` | Next.js SSR（服务端渲染）时，相对路径 `/api/v1` 无法解析为后端地址（SSR 运行在 Node.js 进程，不是浏览器）。SSR 请求会 404。应在 SSR 环境使用完整 URL |
| 2 | WebSocket 代理 — `next.config.js` 只代理 HTTP | `next.config.js:rewrites` | SocketIO WebSocket 连接不会被 Next.js rewrites 处理。需要配置 `ws` 协议代理或客户端直连后端 |
| 3 | 前端 `fetchApi` 无重试逻辑 | `lib/api.ts:fetchApi` | 网络抖动或后端重启时，API 调用直接失败。应添加指数退避重试 |

#### 9.3.6 安全边缘案例

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_execute_locally()` 无命令过滤 | `sandbox.py:208-224` | 通过沙箱逃逸检查后，命令直接执行无任何过滤。恶意 Agent 理论上可构造破坏性命令（如 `rm -rf`）。应添加命令黑名单或白名单过滤 |
| 2 | `ADMIN_PASSWORD` 空密码 | `auth.py:49` | 空字符串通过 `if not password` 检查，但 `secrets.compare_digest('', '')` 返回 True，意味着空密码可登录。必须在启动时检查 ADMIN_PASSWORD 非空 |
| 3 | JWT Secret 默认 `dev-secret-key` | `config.py:JWT_SECRET_KEY` | 生产环境如果不设置 `JWT_SECRET_KEY`，将使用硬编码的 dev key，任何人可伪造 token。应在启动时对生产环境强制检查 |
| 4 | 插件安装无安全校验 | `plugin_service.py:172-189` | `subprocess.run(["pip", "install", ...])` 直接安装任意 pip 包，存在供应链攻击风险。应限制为只允许白名单仓库或添加 hash 校验 |

### 9.4 Round 3 问题严重度总结

| 严重度 | 数量 | 关键问题 |
|--------|------|---------|
| **P0 - 运行时崩溃** | 6 | OpenHarnessConfig 不存在、QueryEngine 构造函数错误、ToolRegistry API 不匹配、SandboxAvailability 属性缺失、沙箱函数不存在、wrap_command 签名错误 |
| **P1 - 功能失效** | 5 | QueryEngine 创建后未使用、Redis 配置但未用、Docker 网络配置错误、SQLite 不兼容函数、WebSocket 代理缺失 |
| **P2 - 安全/数据风险** | 5 | ADMIN_PASSWORD 空密码、JWT 硬编码密钥、插件安装无校验、命令注入、SSE 类型不匹配 |
| **P3 - 配置/一致性** | 7 | 双 Settings 冲突、环境变量覆盖默认值、.env 缺失项、Alembic 不一致、前端 SSR 代理问题 |

**核心结论**：OCH 后端服务层（session_service、tool_service、sandbox、permissions）与 OpenHarness 核心引擎的集成接口存在系统性 API 不匹配问题。这不是个别 bug，而是 OCH 在开发时未参考 OpenHarness 实际 API 文档/源码，基于臆测编写的集成代码。建议全面审查并逐个服务重写集成层，优先修复 P0 级别的导入和构造函数问题。

---

## 十、Round 4：再验证与补充发现

> 对 Round 1-3 中所有问题进行逐条源码验证，并补充新发现的问题。

### 10.1 Round 1-3 问题验证结果

#### 10.1.1 已确认的问题（无需修正）

以下问题经源码重新验证后确认准确：

1. **`OpenHarnessConfig` 不存在** ✅ — `openharness/config/__init__.py` 只导出 `Settings`、`get_config_dir` 等，无 `OpenHarnessConfig`。`session_service.py:199` 的 `from openharness.config import OpenHarnessConfig` 会 `ImportError`
2. **`QueryEngine(config=config)` 构造函数错误** ✅ — `query_engine.py:27-44` 签名要求 `api_client`, `tool_registry`, `permission_checker`, `cwd`, `model`, `system_prompt` 关键字参数，不接受 `config`
3. **`QueryEngine` 创建后未赋值** ✅ — `session_service.py:219` 创建后无赋值，落入 `_simulate_stream()` mock
4. **`get_default_tool_registry` 函数名错误** ✅ — `openharness/tools/__init__.py:46` 导出的是 `create_default_tool_registry`
5. **`ToolRegistry.list_tools()` 返回 `list[BaseTool]` 非 `list[str]`** ✅ — `base.py:69` 确认返回 tool 对象列表
6. **`ToolRegistry.get_tool_info()` 不存在** ✅ — `base.py` 只有 `get(name) -> BaseTool | None`
7. **`ToolRegistry.get_schema()` 不存在** ✅ — `base.py` 中无此方法
8. **`BaseTool.execute()` 签名不匹配** ✅ — `base.py:38` 签名为 `execute(self, arguments: BaseModel, context: ToolExecutionContext) -> ToolResult`，OCH 传入 `(tool_name, input_data)` 字典
9. **`SandboxAvailability` 无 `provider`/`runtime_path`/`version` 属性** ✅ — `adapter.py:22-28` 只有 `enabled`, `available`, `reason`, `command`
10. **`get_sandbox_config()`/`is_host_bash_allowed()` 不存在** ✅ — `adapter.py` 只有 `get_sandbox_availability()` 和 `wrap_command_for_sandbox()`
11. **`wrap_command_for_sandbox()` 期望 `list[str]` 不是 `str`** ✅ — `adapter.py:105-106` 签名为 `(command: list[str], ...)`
12. **`PermissionMode` 无 `AUTO` 值** ✅ — `modes.py` 只有 `DEFAULT`, `PLAN`, `FULL_AUTO`
13. **`SimpleSettings` 的 `denied_tools`/`allowed_tools` 类型为 `set` 而非 `list[str]`** ✅ — `permissions.py:437-438` 使用 `set`，但 `PermissionSettings` 定义为 `list[str]`（`settings.py:36-37`）
14. **双 Settings 系统共享环境变量** ✅ — `app/config.py` 和 `openharness/config/settings.py` 都读取 `OPENHARNESS_MAX_TOKENS` 等
15. **OCH `max_tokens=4096` 覆盖 OpenHarness `16384` 默认值** ✅ — `config.py:46` vs `settings.py:84`
16. **OCH `max_turns=8` 覆盖 OpenHarness `200` 默认值** ✅ — `config.py:45` vs `settings.py:87`
17. **`_work_queue` 为私有属性访问** ✅ — `subagent_executor.py:235-236` 访问 `ThreadPoolExecutor._work_queue`
18. **`_mock_agent_stream()` 代替真实 LLM** ✅ — `subagent_executor.py:252-257` 和 `session_service.py:243-295`
19. **`HookExecutionContext.api_client=None` 会导致 prompt/agent hook 失败** ✅ — `executor.py:41` 字段类型为 `SupportsStreamingMessages`，传 None 对 prompt/agent hook 不安全
20. **Alembic 迁移 `sessions.agent_id` nullable 不一致** ✅ — 已在文档中记录
21. **Redis 配置但未使用** ✅ — 搜索整个 `app/` 目录无 `import redis` 或 `import aioredis`
22. **`.env` 中 `ANTHROPIC_API_KEY=` 空字符串** ✅ — 空字符串对 `_apply_env_overrides()` 为 truthy 会覆盖默认值

#### 10.1.2 需要修正或补充的问题

| # | 原始描述 | 修正说明 |
|---|---------|---------|
| 1 | auth.py "ADMIN_PASSWORD 空密码意味着生产环境登录完全失效" | **需补充细节**：`auth.py:46-52` 在非 `development` 环境下，空 `ADMIN_PASSWORD` 会返回 "Login disabled"，**不是**允许空密码登录。但在 `development` 模式下，`auth.py:46` 跳过密码检查，任何人可以 admin 身份登录。这是开发模式的预期行为，但应在文档中区分说明 |
| 2 | `SSE StreamEvent` 类型不匹配 | **需精确化**：OCH `_simulate_stream()` 输出 `{'type': 'text_delta', 'content': ...}`（dict），但 OpenHarness `StreamEvent` 是 dataclass（`AssistantTextDelta(text=...)`, `ToolExecutionStarted(tool_name=..., tool_input=...)` 等），字段名和结构完全不同 |
| 3 | `wrap_command_for_sandbox` 返回值被忽略 | **需补充**：`sandbox.py:190` 传入字符串会导致 `TypeError`（期望 `list[str]`），根本到不了忽略返回值的步骤。即使修复了类型问题，`sandbox.py:194` 还对返回值 `shlex.split(wrapped)`，但返回值是 `tuple[list[str], Path | None]`，不是字符串，也会报错 |
| 4 | `sandbox.py:252` 的 `wrap_command_for_sandbox(command)` 同样有类型错误 | **遗漏**：`/wrap` 端点也传字符串给 `wrap_command_for_sandbox`，且返回值 `wrapped` 被直接序列化为 JSON，但实际返回 `tuple[list[str], Path | None]` |

### 10.2 新发现的问题

#### 10.2.1 `Settings.load()` 方法不存在

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `Settings.load()` 调用不存在的方法 | `memory.py:593` | OpenHarness `Settings` 是 Pydantic `BaseModel`，没有 `load` 类方法。应使用 `load_settings()` 函数：`from openharness.config import load_settings; settings = load_settings()` |
| 2 | `load_settings()` 也不是 `Settings` 的方法 | `memory.py:591-593` | `from openharness.config.settings import Settings; settings = Settings.load()` — `Settings.load` 不存在。应改为 `from openharness.config import load_settings; settings = load_settings()` |

#### 10.2.2 `CompactCache` 的 `_entries` 字段声明有数据类问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `CompactCache._entries` 使用 `field(default_factory=collections.OrderedDict)` 但与类变量声明冲突 | `cached_compact.py:63` | `_entries` 以下划线开头表示私有，但作为 dataclass field 会有序列化问题。此外 OCH 的 `cache_service.py` 在模块级创建全局单例，多线程访问 `_entries` 无锁保护，可能导致 `RuntimeError: OrderedDict mutated during iteration` |

#### 10.2.3 `get_sandbox_availability()` 需要 `Settings` 参数

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `get_sandbox_availability()` 接受 `Settings` 参数，OCH 未传递 | `sandbox.py:41` | `adapter.py:52` 签名为 `get_sandbox_availability(settings: Settings | None = None)`。OCH 调用时未传参，会使用 `load_settings()` 默认加载，但 OCH 的 `app/config.py` 不会自动同步到 OpenHarness 的 Settings。应显式传递或确保配置一致 |

#### 10.2.4 `_NullHookExecutor` 内部导入可能失败

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_NullHookExecutor.execute()` 内部导入 `AggregatedHookResult` | `hook_service.py:39` | 当 OpenHarness 整体不可用时（`get_hook_executor()` 失败），`_NullHookExecutor` 作为降级实现被使用。但其 `execute()` 方法内部 `from openharness.hooks.types import AggregatedHookResult` 也可能失败，导致降级方案也崩溃。应在模块顶层导入或使用简单的数据类替代 |

#### 10.2.5 `permissions.py` 的 `_current_permission_mode` 是模块级全局变量

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_current_permission_mode = 'default'` 是进程内全局状态 | `permissions.py:69` | 多 worker 部署时（如 Gunicorn 多进程），每个 worker 有独立的 `_current_permission_mode`，修改模式只影响当前 worker。应持久化到数据库或使用 Redis 共享状态 |

#### 10.2.6 前端 `next.config.js` 的 WebSocket 代理不完整

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `rewrites` 只处理 `/ws/:path*` 的 HTTP 请求，不处理 WebSocket 升级 | `next.config.js:17-19` | Next.js `rewrites` 不支持 WebSocket 协议代理。Socket.IO 客户端连接 `ws://localhost:3000/ws` 不会被代理到后端 `ws://localhost:8008/ws`。需要在 `next.config.js` 中配置 `httpAgentOptions` 或在客户端直连后端的 WebSocket 端口 |

#### 10.2.7 前端 `streamChat()` 通过 `/api/proxy/chat` 代理，但 SSE 事件格式未校验

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 代理层透传后端 SSE，但 `StreamEvent` 类型定义与后端不匹配 | `lib/api.ts:174-184` vs `session_service.py:278` | 前端定义 `StreamEvent.type` 包括 `thinking`, `text_delta`, `tool_start`, `tool_end`, `turn_complete`, `error`。但后端 `_simulate_stream()` 输出 `text_delta`（有 `content` 字段）和 `turn_complete`（有 `stop_reason`, `usage`, `hooks_triggered` 字段），与 OpenHarness 真实 `StreamEvent` 的 `AssistantTextDelta(text=...)` 格式完全不同。若未来切换到真实引擎，前端解析会全面崩溃 |

#### 10.2.8 `plugin_service.py` 在 async 方法中使用阻塞 `subprocess.run`

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_install_from_github()` 使用 `subprocess.run` 阻塞事件循环 | `plugin_service.py:172-178` | `async` 方法内调用同步 `subprocess.run`（git clone）会阻塞整个 asyncio 事件循环。应使用 `asyncio.create_subprocess_exec()` |
| 2 | `_install_from_npm()` 同上 | `plugin_service.py:184-191` | 同上，npx 命令也可能耗时较长，应使用异步子进程 |

#### 10.2.9 `sandbox.py` 安全检测使用简单字符串匹配

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `security_check()` 使用 `pattern.lower() in command.lower()` 而非正则 | `sandbox.py:338` | 简单的子串匹配容易绕过。例如 `rrm -rf /`（含空格变异）、`/bin/rm -rf /`（带路径前缀）可绕过 `'rm -rf /'` 匹配。且部分模式如 `wget.* | sh` 含正则语法但被当作字面量处理，`.*` 不会匹配任意字符。应使用正则表达式 `re.search()` |

#### 10.2.10 `coordinator_service.py` 的 `spawn_subagent()` 不持久化

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `spawn_subagent()` 返回内存中的 dict，不写入数据库 | `coordinator_service.py:152-180` | 子代理任务仅存在于返回值中，进程重启后丢失。应创建 `SubagentTask` 数据库模型并持久化，或在 `Task` 模型中存储子代理信息 |

#### 10.2.11 `HookExecutionContext` 字段 `api_client` 为必填，不可传 None

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `HookExecutionContext.api_client` 类型为 `SupportsStreamingMessages`（非 Optional） | `hook_service.py:24` vs `executor.py:41` | `executor.py:41` 定义 `api_client: SupportsStreamingMessages`（无默认值、无 Optional），OCH 传入 `api_client=None`。这在类型层面不合法，且 prompt hook 和 agent hook 内部会调用 `api_client` 的方法导致 `AttributeError`。应传入真实的 API client 实例或将字段改为 `Optional` 并添加 None 检查 |

#### 10.2.12 `permissions.py` 内嵌 `SimpleSettings` 不实现 `PermissionSettings` 接口

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `SimpleSettings` 缺少 `path_rules` 和 `denied_commands` 字段的正确类型 | `permissions.py:435-451` | `PermissionSettings`（`settings.py:32-39`）定义 `path_rules: list[PathRuleConfig]` 和 `denied_commands: list[str]`，但 `SimpleSettings.path_rules: list = []` 不包含 `PathRuleConfig` 对象。`PermissionChecker.__init__`（`checker.py:41-56`）遍历 `path_rules` 并访问 `.pattern` 属性，`SimpleSettings` 传入空列表不会报错，但无法通过 DB 动态添加路径规则 |

### 10.3 Round 4 严重度总结

| 严重度 | 数量 | 关键问题 |
|--------|------|---------|
| **P0 - 运行时崩溃** | 4 | `Settings.load()` 不存在、`wrap_command_for_sandbox` 返回值类型错误（tuple 非 str）、`_NullHookExecutor` 降级也崩溃、`api_client=None` 传给必填参数 |
| **P1 - 功能失效** | 4 | WebSocket 代理不工作、安全检测绕过、plugin async 阻塞事件循环、spawn_subagent 不持久化 |
| **P2 - 安全/数据风险** | 2 | 多 worker 权限模式不同步、CompactCache 线程安全 |
| **P3 - 配置/一致性** | 2 | SSE 事件格式前后端契约不对齐、get_sandbox_availability 未传 Settings |

### 10.4 累计问题统计（Round 1-4）

| 严重度 | Round 1 | Round 2 | Round 3 | Round 4 | **总计** |
|--------|---------|---------|---------|---------|---------|
| **P0 - 运行时崩溃** | 3 | 8 | 6 | 4 | **21** |
| **P1 - 功能失效** | 2 | 12 | 5 | 4 | **23** |
| **P2 - 安全/数据风险** | 1 | 5 | 5 | 2 | **13** |
| **P3 - 配置/一致性** | 2 | 6 | 7 | 2 | **17** |
| **合计** | 8 | 31 | 23 | 12 | **74** |

**最终结论**：经过四轮验证，共发现 74 个问题。核心矛盾集中在三个方面：
1. **OCH-OpenHarness 集成层系统性 API 不匹配**（P0）：`OpenHarnessConfig` 不存在、`QueryEngine` 构造签名错误、`ToolRegistry` API 错误、SandboxAvailability 属性缺失、`Settings.load()` 方法不存在——这些意味着 OCH 的核心功能（AI 对话、工具执行、沙箱、权限）在运行时全部会崩溃
2. **Mock/Stub 占位而非真实实现**（P1）：`_simulate_stream()`、`_mock_agent_stream()`、`spawn_subagent()` 返回内存 dict——整个 AI Agent Loop 是模拟的
3. **配置系统双重体系冲突**（P3）：OCH `app/config.py` 和 OpenHarness `openharness/config/settings.py` 各自独立，通过环境变量隐式耦合，默认值冲突导致 OCH 的低值覆盖 OpenHarness 的高值

建议优先级：先修复 P0 的 21 个运行时崩溃问题 → 再替换 Mock 实现真实集成 → 最后统一配置体系
