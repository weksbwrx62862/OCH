# Tasks

## 第一阶段：安全加固（Critical）

- [x] Task 1: sandbox.py 安全加固
  - [x] 1.1: 为 `/status` 和 `/execute` 和 `/wrap` 和 `/security-check` 端点添加 `@require_auth` 装饰器
  - [x] 1.2: 为 `/execute` 端点额外添加 `@require_role('admin')` 装饰器
  - [x] 1.3: `_execute_locally` 和 `_execute_in_sandbox` 移除 `shell=True`，改用 `shlex.split()` 将命令拆分为参数列表
  - [x] 1.4: 将 `__import__('time')` 替换为顶部 `import time`

- [x] Task 2: channels.py 安全加固
  - [x] 2.1: 为所有 9 个端点添加 `@require_auth` 装饰器（types, registered, register, channel_detail, channel_update, channel_delete, channel_send, channel_test, stats）
  - [x] 2.2: 为 register/channel_update/channel_delete/channel_send 端点添加 `from app.core.security import require_auth` 导入

- [x] Task 3: 默认密钥启动保护
  - [x] 3.1: 在 config.py 的 Settings 类中添加 `model_validator`，检测 SECRET_KEY 和 JWT_SECRET_KEY 是否为默认值
  - [x] 3.2: 当 APP_ENV != 'development' 且密钥为默认值时，抛出 ValueError 阻止启动
  - [x] 3.3: 在 development 模式下输出 WARNING 日志但允许启动

- [x] Task 4: API 密钥前缀泄露修复
  - [x] 4.1: 修改 api/config.py 的 `list_providers` 端点，移除 `key_preview` 字段
  - [x] 4.2: 替换为 `key_configured: bool` 和 `key_source: str`（'env' 或 'config'）

- [x] Task 5: CORS 硬编码修复
  - [x] 5.1: 修改 sessions.py `_chat_stream_impl` 中的 SSE 响应 headers，移除 `Access-Control-Allow-Origin: *`
  - [x] 5.2: 从 Flask app 配置中获取 CORS 允许的域名列表

- [x] Task 6: 前端 XSS 漏洞修复
  - [x] 6.1: 安装 `rehype-sanitize` 依赖（react-markdown 已安装）
  - [x] 6.2: 替换 chat/page.tsx 中的 MarkdownRenderer 组件，使用 react-markdown + rehype-sanitize
  - [x] 6.3: 移除 `dangerouslySetInnerHTML` 的使用
  - [x] 6.4: 保留 CodeBlock 组件的功能（代码高亮、复制按钮）

## 第二阶段：代码去重与基础修复（High）

- [x] Task 7: 创建统一异步工具模块
  - [x] 7.1: 创建 `app/core/async_utils.py`，包含 `run_async(coro)` 和 `get_db()` 函数
  - [x] 7.2: run_async 使用 `asyncio.Runner`（Python 3.12+）或安全的 fallback 实现
  - [x] 7.3: get_db 统一使用 `database.async_session_factory()`

- [x] Task 8: 替换所有文件中的重复 `_run_async` 和 `_get_db`
  - [x] 8.1: 替换 agents.py 中的 `_run_async` 和 `_get_db_session`
  - [x] 8.2: 替换 sessions.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.3: 替换 coordinator.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.4: 替换 config.py (api) 中的 `_run_async`
  - [x] 8.5: 替换 audit.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.6: 替换 permissions.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.7: 替换 memory.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.8: 替换 tasks.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.9: 替换 skills.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.10: 替换 plugins.py 中的 `_run_async` 和 `_get_db`
  - [x] 8.11: 替换 mcp.py 中的 `_run_async` 和 `_get_db`

- [x] Task 9: 修复 update_agent 名称唯一性检查顺序
  - [x] 9.1: 在 agents.py `_update_agent_impl` 中，将名称唯一性检查移到 `setattr(agent, 'name', ...)` 之前

- [x] Task 10: 修复 before_request async 问题
  - [x] 10.1: 将 main.py 中的 `async def run_middleware_before_request` 改为同步函数
  - [x] 10.2: 使用 `asyncio.run()` 或 `loop.run_until_complete()` 在同步函数中执行异步中间件
  - [x] 10.3: 替换 `__import__('app.middleware', ...)` 为顶部正常导入

- [x] Task 11: 修复前端闭包 bug
  - [x] 11.1: 在 chat/page.tsx 中使用 `useRef` 保存 streamingContent 和 activeToolCall 的最新值
  - [x] 11.2: 在流式完成后使用 ref 值而非 state 值来构建消息对象

- [x] Task 12: 全局缓存添加 LRU 上限
  - [x] 12.1: sessions.py `_active_sessions` 添加最大条目数限制（如 1000）
  - [x] 12.2: coordinator.py `_active_workers` 添加最大条目数限制
  - [x] 12.3: channels.py `_registered_channels` 添加最大条目数限制
  - [x] 12.4: middleware RateLimitMiddleware `_requests` 添加清理机制

- [x] Task 13: 替换 datetime.utcnow() 为 datetime.now(timezone.utc)
  - [x] 13.1: 替换所有 24 个后端文件中的 `datetime.utcnow()` 为 `datetime.now(timezone.utc)`
  - [x] 13.2: 确保所有使用 datetime 的文件顶部有 `from datetime import timezone` 导入

- [x] Task 14: 替换 __import__ 为正常导入
  - [x] 14.1: sandbox.py 中 `__import__('time')` 替换为顶部 `import time`
  - [x] 14.2: channels.py 中 `__import__('datetime')` 和 `__import__('uuid')` 替换为顶部正常导入
  - [x] 14.3: audit.py 中 `__import__('sqlalchemy')` 替换为顶部 `from sqlalchemy import func`
  - [x] 14.4: main.py 中 `__import__('app.middleware', ...)` 替换为顶部正常导入

- [x] Task 15: Session agent_id 改为 nullable
  - [x] 15.1: 修改 session.py 模型，将 `agent_id` 的 `nullable=False` 改为 `nullable=True`
  - [x] 15.2: 修改 sessions.py `_create_session`，将 `agent_id or 'default'` 改为 `agent_id or None`

## 第三阶段：性能与代码规范优化（Medium 精选）

- [x] Task 16: 数据库查询优化
  - [x] 16.1: session_service.py 中 `len(result.all())` 改用 `func.count()`
  - [x] 16.2: audit.py 逐条删除改用批量 `DELETE FROM ... WHERE created_at < cutoff`
  - [x] 16.3: permissions.py 逐条删除改用批量 DELETE

- [x] Task 17: 线程安全修复
  - [x] 17.1: permissions.py `get_permission_checker()` 添加 `threading.Lock`
  - [x] 17.2: session_service.py `get_hook_executor()` 添加 `threading.Lock`（如存在）

- [x] Task 18: 前端性能优化
  - [x] 18.1: chat/page.tsx 中 MessageBubble 和 ToolCallCard 添加 `React.memo`
  - [x] 18.2: 关键回调函数添加 `useCallback`（sendMessage, initSession）
  - [x] 18.3: 关键计算值添加 `useMemo`

- [x] Task 19: 前端数据获取封装
  - [x] 19.1: 创建 `lib/hooks/useApi.ts`，封装通用的数据获取逻辑（loading/error/data 状态）
  - [x] 19.2: 在各页面中使用 useApi hook 替代重复的 fetch + state 模式

- [x] Task 20: 清理未使用的 npm 依赖
  - [x] 20.1: 检查 package.json 中未使用的依赖并移除

# Task Dependencies
- Task 7 → Task 8（必须先创建 async_utils.py 才能替换）
- Task 6 → Task 18（XSS 修复后再做 memo 优化）
- Task 1-6 可并行执行（互相独立的安全修复）
- Task 8 依赖 Task 7
- Task 9-15 可并行执行（互相独立的修复）
- Task 16-17 可并行执行
- Task 18-20 可并行执行
