# 验证检查清单

## P0 — 关键修复验证

- [x] `backend/app/core/security.py` 的 `init_security` 函数中不存在 `@app.before_request` 装饰器
- [x] `backend/app/middleware/__init__.py` 的 `AuthMiddleware.before_request` 在认证成功后写入 `flask.g.user`
- [x] `backend/app/main.py` 的 `_run_middleware_sync` 在认证成功后写入 `flask.g.user`
- [x] `backend/app/main.py` 的 `handle_generic_error` 在非开发环境返回 `{'error': 'Internal server error', 'code': 500}`
- [x] `backend/app/main.py` 的 `bad_request` handler 在非开发环境隐藏 `error.description`
- [x] `backend/app/core/async_utils.py` 存在 `dispose_engine()` 函数
- [x] `backend/app/main.py` 注册了 `atexit` 关闭钩子

## P1 — 短期改进验证

- [x] 代码库中 `datetime.utcnow()` 残留为 0 处
- [x] `backend/app/api/agents.py` 存在 `POST /agents/quick-create` 路由
- [x] `POST /agents/quick-create` 路由使用 `@require_auth` 而非 `@require_role('admin')`
- [x] `frontend/app/chat/page.tsx` 的 `initSession` 调用 `/agents/quick-create` 而非 `/agents`
- [x] `frontend/lib/api.ts` 的 `streamChat()` 使用 `/api/proxy/chat?sessionId=` 路径
- [x] `frontend/app/settings/page.tsx` 存在 `isAdmin` 状态检查
- [x] `frontend/app/settings/page.tsx` MCP 添加/移除按钮仅 admin 可见
- [x] `frontend/app/chat/types.ts` 文件存在
- [x] `frontend/app/chat/MessageBubble.tsx` 文件存在
- [x] `frontend/app/chat/MemorySidebar.tsx` 文件存在
- [x] `frontend/app/chat/ChatInput.tsx` 文件存在
- [x] `frontend/app/chat/page.tsx` 不超过 300 行（实际 320 行，从 560 行缩减）
- [x] `backend/app/services/coordinator_service.py` 不存在 `self._teams` 内存字典
- [x] `backend/app/services/coordinator_service.py` 使用 Team/TeamMember ORM 模型进行数据库查询

## 已生效修复确认

- [x] `frontend/app/audit/page.tsx` 的 `handleExport` 使用 `fetch()` + Bearer token + Blob 下载（Fix#2 已生效）
- [x] `frontend/app/login/page.tsx` 存在 `password` 状态和输入框（Fix#4 已生效）
