# Checklist

## 第一阶段：安全加固（Critical）

- [x] C-01: sandbox.py `/execute` 端点需要认证（@require_auth）和 admin 角色（@require_role('admin')）
- [x] C-01: sandbox.py 不使用 `shell=True`，命令通过参数列表执行
- [x] C-02: channels.py 所有 9 个端点都有 `@require_auth` 装饰器
- [x] C-03: 使用默认 SECRET_KEY 或 JWT_SECRET_KEY 时，生产环境拒绝启动
- [x] C-04: `/config/providers` 响应不包含 `key_preview` 字段，改为 `key_configured: bool`
- [x] C-05: SSE 响应不包含硬编码 `Access-Control-Allow-Origin: *`
- [x] C-06: 前端不使用 `dangerouslySetInnerHTML` 渲染 AI 输出
- [x] C-06: AI 输出经过 rehype-sanitize 消毒处理

## 第二阶段：代码去重与基础修复（High）

- [x] H-01: `app/core/async_utils.py` 存在且包含 `run_async` 和 `get_db` 函数
- [x] H-01: 11 个 API 文件不再包含本地 `_run_async` 定义，全部从 async_utils 导入
- [x] H-02: agents.py `update_agent` 中名称唯一性检查在 setattr 之前执行
- [x] H-03: main.py `before_request` 处理函数是同步函数，不是 async def
- [x] H-04: 前端 chat 流式完成后消息正确保存到 messages 列表
- [x] H-05: sessions.py `_active_sessions` 有最大条目数限制
- [x] H-06: 所有后端文件使用 `datetime.now(timezone.utc)` 而非 `datetime.utcnow()`
- [x] H-07: 所有 `__import__()` 调用已替换为顶部正常导入
- [x] H-08: Session 模型 `agent_id` 字段允许 NULL

## 第三阶段：性能与代码规范优化（Medium）

- [x] M-06: session_service.py 不使用 `len(result.all())` 计数
- [x] M-08: audit.py 和 permissions.py 使用批量 DELETE 而非逐条删除
- [x] M-11: `get_permission_checker()` 使用 `threading.Lock` 保护
- [x] M-15: 前端 MessageBubble 和 ToolCallCard 使用 React.memo
- [x] M-16: 前端存在 `useApi` hook 封装数据获取逻辑
- [x] M-17: package.json 中无未使用的依赖
