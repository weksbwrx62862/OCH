---
name: deploy-test-and-fix-och
overview: 部署 OpenClaw-Harness 项目，按模块排查并修复所有 bug，确保前后端接口参数一致、数据格式正确，实现无缝对接与正常通信。
todos:
  - id: fix-backend-startup
    content: 修复后端启动方式：Dockerfile/docker-compose CMD 改为 python -m app.main，main.py 添加 init_db() 自动建表
    status: completed
  - id: fix-async-utils-getdb
    content: 修复 async_utils.get_db() 为异步上下文管理器，添加 rollback/close 保护
    status: completed
  - id: fix-user-field-mismatch
    content: 统一修复后端所有 g.user.get('user_id') 为 g.user.get('sub')，前端 User 接口和登录存储匹配后端格式
    status: completed
  - id: fix-frontend-types
    content: 扩展 lib/types.ts 为完整类型定义（Agent/Session/Message/Task/Skill/User/LoginResponse），各页面组件引用集中类型
    status: completed
  - id: fix-api-proxy-rewrites
    content: 修复 next.config.js 排除 /api/proxy/* 的 rewrite，验证 SSE 聊天流端到端正常
    status: completed
  - id: fix-agent-permission
    content: 前端 Agent 创建改用 quick-create 端点，修复权限对接问题
    status: completed
  - id: deploy-and-e2e-test
    content: 部署启动前后端，端到端测试核心流程：登录->会话->聊天->Agent管理
    status: completed
    dependencies:
      - fix-backend-startup
      - fix-async-utils-getdb
      - fix-user-field-mismatch
      - fix-frontend-types
      - fix-api-proxy-rewrites
      - fix-agent-permission
---

## 产品概述

OpenClaw-Harness (OCH) 是一个基于 OpenHarness 核心架构的多智能体驾驭平台，包含 Flask 后端和 Next.js 前端。用户要求部署并测试该项目，按模块排查并修复所有 bug，确保前后端接口参数一致、数据格式正确，实现无缝对接与正常通信。

## 核心功能

- 部署后端（Flask + SQLite）和前端（Next.js），确保服务可正常启动
- 修复后端启动方式不兼容（Flask vs uvicorn）的致命 bug
- 修复前端 API 代理路由与 Next.js rewrites 冲突导致 SSE 聊天流失效的问题
- 修复前后端用户数据模型不一致（username vs name/email）的问题
- 修复 get_db() 会话管理缺少 rollback 保护的问题
- 修复前端 Agent 创建因权限问题失败的对接问题
- 补全前端类型定义，集中管理后端响应数据类型
- 逐模块验证所有 API 端点与前端请求的参数和响应格式一致性
- 端到端测试核心流程：登录 -> 创建会话 -> SSE 聊天 -> 管理智能体

## 技术栈

- 后端: Python 3.11+ / Flask 3.0 / SQLAlchemy 2.0 (async) / SQLite (开发模式) / Flask-SocketIO / PyJWT
- 前端: Next.js 15 / React 19 / TypeScript / Tailwind CSS / Zustand
- 数据库: SQLite (aiosqlite) / PostgreSQL (asyncpg, 生产)
- 部署: Docker Compose / 本地开发 (start.sh)

## 实现方案

### 1. 修复后端启动方式 (致命 Bug)

**问题**: Dockerfile 和 docker-compose.yml 使用 `uvicorn`（ASGI 服务器），但 `main.py` 创建的是 Flask WSGI 应用 + SocketIO，两者不兼容。`__main__` 入口使用 `socketio.run()` 启动 WSGI 服务器。
**方案**: 将 Dockerfile CMD 和 docker-compose.yml command 改为 `python -m app.main`，使用 Flask+SocketIO 内置服务器启动。同时在 `main.py` 的 `__main__` 中增加 `init_db()` 调用确保数据库表自动创建。

### 2. 修复前端 SSE 代理路由冲突

**问题**: `next.config.js` 的 rewrites 将 `/api/:path*` 全部代理到后端，但前端有 `app/api/proxy/chat/route.ts` 处理 SSE 流。Next.js API Routes 优先于 rewrites，因此 `/api/proxy/chat` 请求会先匹配到 route handler，**但**前端 `api.ts` 中 `streamChat()` 请求的 URL 是 `/api/proxy/chat?sessionId=...`，而 Next.js 的 rewrite 规则不包含 WebSocket/SSE 特殊处理。需验证实际行为并确保路由优先级正确。
**方案**: 确认 Next.js API Routes 优先级，如需调整则在 `next.config.js` 中排除 `/api/proxy/:path*` 的 rewrite 规则。

### 3. 修复前后端用户数据模型不一致

**问题**: 后端 `auth.py` 返回 `{ user: { id, username, role } }`，前端 `appStore.ts` 定义 `User = { id, email, name, role }`，且前端登录页将 `data.user` 存入 `localStorage.och_user`。
**方案**: 修改前端 `appStore.ts` 的 `User` 接口匹配后端响应 `{ id, username, role }`，并在 AuthProvider 中正确解析用户信息。

### 4. 修复 get_db() 会话管理安全

**问题**: `async_utils.get_db()` 返回裸 `AsyncSession`，缺少 `try/yield/commit/except/rollback/finally/close` 保护。如果 API 代码中途异常，session 不会自动 rollback，可能导致连接泄漏。
**方案**: 将 `async_utils.get_db()` 改为异步上下文管理器，添加 rollback/close 保护，与 `database.get_db()` 行为一致。

### 5. 修复前端 Agent 创建权限对接

**问题**: 前端 `agents/page.tsx` 调用 `POST /agents`（需要 admin 角色），但开发环境登录默认是 admin，一般用户创建 Agent 会 403。`quick-create` 端点不需要 admin 但前端没有使用它。
**方案**: 前端 Agent 创建改为调用 `/agents/quick-create` 端点（普通用户可用），或保留当前方式但在错误提示中明确权限要求。

### 6. 修复前端类型定义并集中管理

**问题**: `lib/types.ts` 仅导出 `AuditLog`，其他类型散落在各组件中，与后端模型不统一。
**方案**: 扩展 `lib/types.ts`，添加 `Agent`、`Session`、`Message`、`Task`、`Skill`、`ToolInfo`、`User`、`LoginResponse` 等接口，与后端 `to_dict()` 输出格式对齐。各页面组件引用集中类型。

### 7. 修复 Agent 创建时 created_by 字段取值不一致

**问题**: `agents.py` 中 `create_agent` 使用 `g.user.get('user_id')`，但 JWT payload 中存的是 `sub` 字段而非 `user_id`。同样问题出现在 `duplicate_agent` 中。`quick_create_agent` 则使用 `g.user.get('sub')`（正确）。
**方案**: 统一所有 `g.user.get('user_id')` 为 `g.user.get('sub')`，与 JWT payload 一致。同样检查 `coordinator.py` 中的相同问题。

## 关键修改文件

```
backend/
├── app/main.py              # [MODIFY] 添加 init_db() 调用，修复启动逻辑
├── app/core/async_utils.py  # [MODIFY] get_db() 改为异步上下文管理器
├── app/api/agents.py        # [MODIFY] 修复 g.user.get('user_id') → 'sub'
├── app/api/coordinator.py   # [MODIFY] 修复 g.user.get('user_id') → 'sub'
├── app/api/skills.py        # [MODIFY] 修复 g.user.get('user_id') → 'sub'
├── Dockerfile               # [MODIFY] CMD 改为 python -m app.main
docker-compose.yml           # [MODIFY] backend command 改为 python -m app.main

frontend/
├── lib/types.ts             # [MODIFY] 扩展为完整类型定义，与后端对齐
├── lib/api.ts               # [MODIFY] 验证 SSE 代理 URL 逻辑
├── stores/appStore.ts       # [MODIFY] User 接口匹配后端 { id, username, role }
├── app/login/page.tsx       # [MODIFY] 存储用户信息时匹配后端格式
├── app/AuthProvider.tsx     # [MODIFY] 解析 localStorage 用户信息
├── app/agents/page.tsx      # [MODIFY] 使用 quick-create 或集中类型
├── app/chat/types.ts        # [MODIFY] 引用集中类型
├── app/sessions/page.tsx    # [MODIFY] 引用集中类型
├── next.config.js           # [MODIFY] 排除 /api/proxy/* 的 rewrite
```

## 实现注意事项

- **数据库初始化**: SQLite 模式下 `alembic upgrade head` 可能失败，需确保 `init_db()` 在启动时自动创建表
- **asyncio.run() 嵌套问题**: Flask before_request 中调用 `asyncio.run()` 在已有事件循环时会 RuntimeError，当前有 fallback 但需测试
- **SSE 流式响应**: 修复后必须端到端验证 chat 流的 SSE 事件解析
- **SQLite 布尔兼容性**: `Skill.enabled.is_(True)` 在 SQLite 中需确认 SQLAlchemy 正确处理
- **前端 API_BASE_URL**: 默认 `/api/v1` 配合 Next.js rewrites 工作，修改 rewrites 时需确保不破坏此路径
- **g.user 字段名**: JWT payload 中存的是 `sub`（用户ID）、`username`、`role`，所有 `g.user.get('user_id')` 引用都需改为 `g.user.get('sub')`

## SubAgent

- **code-explorer**
- Purpose: 在修复过程中搜索代码中所有 `g.user.get('user_id')` 的引用，确保统一修复
- Expected outcome: 找到所有需要修改的 user_id 引用位置，避免遗漏