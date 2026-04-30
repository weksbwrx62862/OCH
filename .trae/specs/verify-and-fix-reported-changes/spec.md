# 报告整合与修改验证 Spec

## Why

项目存在三份技术报告（技术提升方案、前后端一致性修复报告、技术债修复报告），其中技术债修复报告声称所有 16 项修复"✅ 全部完成"，前后端一致性修复报告也描述了 5 项修复的具体代码变更。但经过对代码库的实际验证，**大部分声称已完成的修复并未生效**，代码仍处于修改前的状态。需要整合报告内容、明确实际状态、并实施真正需要的修复。

## What Changes

### 验证结果总览

| # | 报告来源 | 修复项 | 报告声称 | 实际状态 | 需要修复 |
|---|---------|--------|---------|---------|---------|
| 1 | 技术债 P0-1 | 异步数据库架构（引擎单例） | ✅ 完成 | ⚠️ 部分生效 | 需补充 atexit 钩子 + get_db 会话管理 |
| 2 | 技术债 P0-2 | 认证逻辑三重重复统一 | ✅ 完成 | ❌ 未修复 | 需完整实施 |
| 3 | 技术债 P0-3 | 生产环境异常信息泄露 | ✅ 完成 | ❌ 未修复 | 需完整实施 |
| 4 | 技术债 P1-1 | datetime.utcnow() 全面替换 | ✅ 完成 | ❌ 未修复（60处残留） | 需完整实施 |
| 5 | 技术债 P1-2 | 前端 chat/page.tsx 组件拆分 | ✅ 完成 | ❌ 未修复 | 需完整实施 |
| 6 | 技术债 P1-3 | CoordinatorService 数据库持久化 | ✅ 完成 | ❌ 未修复 | 需完整实施 |
| 7 | 前后端 Fix#1 | StreamChat 通过 BFF 代理 | 已修复 | ❌ 未修复 | 需完整实施 |
| 8 | 前后端 Fix#2 | 审计导出认证下载 | 已修复 | ✅ 已生效 | 无需操作 |
| 9 | 前后端 Fix#3 | Agent quick-create 端点 | 已修复 | ❌ 未修复 | 需完整实施 |
| 10 | 前后端 Fix#4 | 登录页密码字段 | 已修复 | ✅ 已生效 | 无需操作 |
| 11 | 前后端 Fix#5 | MCP 管理 UI 权限控制 | 已修复 | ❌ 未修复 | 需完整实施 |

### 需要实施的变更

- **P0-2**: 统一认证逻辑 — 删除 `security.py` 的 `before_request`，`AuthMiddleware` 写入 `g.user`，`_run_middleware_sync` 写入 `g.user`
- **P0-3**: 生产环境异常信息隐藏 — `handle_generic_error` 和 `bad_request` 添加 `APP_ENV` 环境判断
- **P1-1**: 批量替换 60 处 `datetime.utcnow()` → `datetime.now(timezone.utc)`
- **P1-2**: 拆分 `chat/page.tsx` 为 5 个文件
- **P1-3**: 重写 `CoordinatorService` 为数据库持久化
- **前后端 Fix#1**: `streamChat()` 改为通过 BFF 代理 `/api/proxy/chat`
- **前后端 Fix#3**: 后端新增 `POST /agents/quick-create` 端点，前端改用该端点
- **前后端 Fix#5**: Settings 页面 MCP 操作添加 `isAdmin` 权限控制
- **补充**: `main.py` 添加 `atexit` 数据库引擎关闭钩子

## Impact

- Affected code:
  - `backend/app/core/security.py` — 移除 before_request
  - `backend/app/middleware/__init__.py` — AuthMiddleware 写入 g.user
  - `backend/app/main.py` — 错误处理环境判断 + atexit 钩子 + _run_middleware_sync 写入 g.user
  - `backend/app/api/agents.py` — 新增 quick-create 端点
  - `backend/app/services/coordinator_service.py` — 重写为数据库持久化
  - 25+ Python 文件 — datetime.utcnow() 替换
  - `frontend/lib/api.ts` — streamChat URL 修改
  - `frontend/app/chat/page.tsx` — 组件拆分 + API 路径修改
  - `frontend/app/settings/page.tsx` — isAdmin 权限控制

## ADDED Requirements

### Requirement: 认证逻辑统一

系统 SHALL 仅通过 `AuthMiddleware` 执行 JWT 认证，验证成功后同时写入 `ctx.metadata` 和 `flask.g.user`。`security.py` 的 `init_security` SHALL NOT 注册 `before_request` 处理器。`_run_middleware_sync` 回退路径 SHALL 同步写入 `g.user`。

#### Scenario: 请求经过 AuthMiddleware 认证成功
- **WHEN** 请求携带有效 JWT Token 经过 AuthMiddleware
- **THEN** `ctx.metadata["user_id"]` 和 `flask.g.user` 均被设置

#### Scenario: 请求经过 _run_middleware_sync 回退路径
- **WHEN** asyncio.run 不可用，走 _run_middleware_sync 回退
- **THEN** `ctx.metadata["user_id"]` 和 `flask.g.user` 均被设置

### Requirement: 生产环境异常信息隐藏

系统 SHALL 在非开发环境下隐藏异常详情。`handle_generic_error` 在 `APP_ENV != "development"` 时 SHALL 仅返回 `{'error': 'Internal server error', 'code': 500}`，不暴露 `str(error)` 和 `type(error).__name__`。

#### Scenario: 生产环境未处理异常
- **WHEN** 生产环境发生未处理异常
- **THEN** 响应体仅包含 `{'error': 'Internal server error', 'code': 500}`

#### Scenario: 开发环境未处理异常
- **WHEN** 开发环境发生未处理异常
- **THEN** 响应体包含 `{'error': str(error), 'type': type(error).__name__, 'code': 500}`

### Requirement: datetime.utcnow() 全面替换

系统 SHALL 在所有 Python 文件中使用 `datetime.now(timezone.utc)` 替代 `datetime.utcnow()`。所有使用 `datetime.utcnow()` 的文件 SHALL 正确导入 `timezone`。

#### Scenario: 全量替换验证
- **WHEN** 在代码库中搜索 `datetime.utcnow()`
- **THEN** 结果为 0 处

### Requirement: Agent 快速创建端点

系统 SHALL 提供 `POST /agents/quick-create` 端点，仅需 `@require_auth`（不需要 admin 角色），仅接受 `name` 和 `model` 参数，自动填充 `system_prompt` 和 `description`。

#### Scenario: 普通用户快速创建 Agent
- **WHEN** 已登录的非 admin 用户调用 `POST /agents/quick-create`
- **THEN** 返回创建成功的 Agent 对象，`config.source` 为 `'quick-create'`

### Requirement: StreamChat 通过 BFF 代理

前端 `streamChat()` SHALL 通过 Next.js BFF 代理路由 `/api/proxy/chat?sessionId=` 发送请求，而非直连后端。

#### Scenario: SSE 流式聊天请求
- **WHEN** 前端发起流式聊天请求
- **THEN** 请求路径为 `/api/proxy/chat?sessionId={id}`，由 BFF 代理转发到后端

### Requirement: MCP 管理 UI 权限控制

前端 Settings 页面的 MCP 服务器添加/移除操作 SHALL 仅对 admin 角色用户可见。非 admin 用户 SHALL 看到权限不足提示。

#### Scenario: 非 admin 用户查看 MCP 管理
- **WHEN** 非 admin 用户访问设置页 MCP 标签
- **THEN** 添加和移除按钮不可见，显示"需要管理员权限"提示

### Requirement: CoordinatorService 数据库持久化

`CoordinatorService` SHALL 使用 SQLAlchemy 异步查询数据库进行团队 CRUD 操作，而非内存字典。`self._teams` 内存字典 SHALL 被移除。

#### Scenario: 应用重启后团队数据保留
- **WHEN** 应用重启后查询已创建的团队
- **THEN** 团队数据仍然存在

### Requirement: 数据库引擎关闭钩子

系统 SHALL 在应用退出时通过 `atexit` 注册关闭钩子，调用 `dispose_engine()` 释放数据库连接池。

#### Scenario: 应用正常退出
- **WHEN** 应用进程退出
- **THEN** 数据库连接池被正确释放

### Requirement: 前端 chat/page.tsx 组件拆分

`chat/page.tsx` SHALL 拆分为以下文件结构：
- `types.ts` — 共享类型定义
- `MessageBubble.tsx` — 消息气泡 + ToolCallCard 组件
- `MemorySidebar.tsx` — 记忆库侧边栏
- `ChatInput.tsx` — 输入框 + QuickAction
- `page.tsx` — 主页面组装（不超过 300 行）

#### Scenario: 组件拆分后文件结构
- **WHEN** 检查 `frontend/app/chat/` 目录
- **THEN** 存在 `types.ts`、`MessageBubble.tsx`、`MemorySidebar.tsx`、`ChatInput.tsx`、`page.tsx` 五个文件

## MODIFIED Requirements

无（本 spec 仅涉及新增修复，不修改已有功能行为）

## REMOVED Requirements

无
