# Tasks

## P0 — 必须立即修复

- [x] Task 1: 统一认证逻辑（P0-2）
  - [x] 1.1: 修改 `backend/app/core/security.py` — 移除 `init_security` 中的 `@app.before_request` 和 `load_user_from_token` 函数，仅保留 JWT 工具函数
  - [x] 1.2: 修改 `backend/app/middleware/__init__.py` — `AuthMiddleware.before_request` 验证成功后写入 `flask.g.user = payload`，公共路径白名单改用 `frozenset`
  - [x] 1.3: 修改 `backend/app/main.py` — `_run_middleware_sync` 中认证成功后写入 `flask.g.user = payload`
  - [x] 1.4: 验证三处认证逻辑统一：`security.py` 无 `before_request`，`AuthMiddleware` 和 `_run_middleware_sync` 均写入 `g.user`

- [x] Task 2: 修复生产环境异常信息泄露（P0-3）
  - [x] 2.1: 修改 `backend/app/main.py` — `handle_generic_error` 添加 `APP_ENV` 判断，非开发环境隐藏 `str(error)` 和 `type(error).__name__`
  - [x] 2.2: 修改 `backend/app/main.py` — `bad_request` handler 同样添加环境判断
  - [x] 2.3: 验证生产环境返回 `{'error': 'Internal server error', 'code': 500}`

- [x] Task 3: 添加数据库引擎关闭钩子
  - [x] 3.1: 修改 `backend/app/core/async_utils.py` — 添加 `dispose_engine()` 函数
  - [x] 3.2: 修改 `backend/app/main.py` — 添加 `atexit.register(_shutdown_db)` 关闭钩子
  - [x] 3.3: 验证 `dispose_engine` 和 `atexit` 注册存在

## P1 — 短期改进

- [x] Task 4: 批量替换 `datetime.utcnow()`（P1-1）
  - [x] 4.1: 替换 `backend/app/core/security.py` 中 2 处 `datetime.utcnow()`
  - [x] 4.2: 替换 `backend/app/api/` 目录下所有 `datetime.utcnow()`（约 20 处）
  - [x] 4.3: 替换 `backend/app/models/` 目录下所有 `datetime.utcnow()`（约 20 处）
  - [x] 4.4: 替换 `backend/app/services/` 目录下所有 `datetime.utcnow()`（约 10 处）
  - [x] 4.5: 替换 `backend/openharness/` 目录下 `datetime.utcnow()`（约 2 处）
  - [x] 4.6: 全局验证 `datetime.utcnow()` 残留为 0

- [x] Task 5: 新增 Agent 快速创建端点（前后端 Fix#3）
  - [x] 5.1: 修改 `backend/app/api/agents.py` — 新增 `POST /agents/quick-create` 路由，使用 `@require_auth`（非 admin），仅接受 `name` 和 `model`
  - [x] 5.2: 修改 `frontend/app/chat/page.tsx` — `initSession` 中 API 路径从 `/agents` 改为 `/agents/quick-create`，仅发送 `name` 和 `model`
  - [x] 5.3: 验证后端路由存在且前端调用正确

- [x] Task 6: StreamChat 通过 BFF 代理（前后端 Fix#1）
  - [x] 6.1: 修改 `frontend/lib/api.ts` — `streamChat()` 的 URL 从 `${this.baseUrl}/sessions/${sessionId}/chat` 改为 `/api/proxy/chat?sessionId=${encodeURIComponent(sessionId)}`
  - [x] 6.2: 验证 BFF 代理路由 `frontend/app/api/proxy/chat/route.ts` 存在且 streamChat 使用它

- [x] Task 7: MCP 管理 UI 权限控制（前后端 Fix#5）
  - [x] 7.1: 修改 `frontend/app/settings/page.tsx` — 添加 `isAdmin` 状态，从 `localStorage.getItem('och_user')` 读取角色
  - [x] 7.2: 条件渲染 MCP 操作按钮 — 移除按钮仅 admin 可见，添加按钮 admin 显示/非 admin 显示权限提示
  - [x] 7.3: 验证非 admin 用户看不到 MCP 操作按钮

- [x] Task 8: 前端 chat/page.tsx 组件拆分（P1-2）
  - [x] 8.1: 新建 `frontend/app/chat/types.ts` — 提取 `Message`、`ToolUse`、`SessionInfo`、`MemoryFact` 类型定义
  - [x] 8.2: 新建 `frontend/app/chat/MessageBubble.tsx` — 提取 `MessageBubble` 和 `ToolCallCard` 组件
  - [x] 8.3: 新建 `frontend/app/chat/MemorySidebar.tsx` — 提取记忆库侧边栏
  - [x] 8.4: 新建 `frontend/app/chat/ChatInput.tsx` — 提取输入框和快捷操作
  - [x] 8.5: 重写 `frontend/app/chat/page.tsx` — 组装子组件，主文件不超过 300 行
  - [x] 8.6: 验证组件拆分后功能正常

- [x] Task 9: CoordinatorService 数据库持久化（P1-3）
  - [x] 9.1: 重写 `backend/app/services/coordinator_service.py` — 移除 `self._teams` 内存字典，所有团队 CRUD 改为 SQLAlchemy 异步数据库查询
  - [x] 9.2: Agent 定义保留为模块常量 `BUILTIN_AGENT_DEFINITIONS`，自定义 Agent 从数据库查询
  - [x] 9.3: `get_protocol_status()` 改为数据库聚合查询
  - [x] 9.4: 验证使用 Team/TeamMember 模型，无 `self._teams`

## Task Dependencies

- Task 1 (认证统一) 和 Task 2 (信息泄露) 和 Task 3 (atexit 钩子) 可并行
- Task 4 (datetime 替换) 独立，可并行
- Task 5 (quick-create) 独立，可并行
- Task 6 (BFF 代理) 独立，可并行
- Task 7 (MCP 权限) 独立，可并行
- Task 8 (组件拆分) 依赖 Task 5（chat/page.tsx 中的 API 路径需先改）
- Task 9 (CoordinatorService) 独立，可并行
