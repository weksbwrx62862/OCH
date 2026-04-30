# 后端核心问题

## 1. 应用入口 `main.py`

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

## 2. 配置管理 `config.py`

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

## 3. 数据库层 `core/database.py` + `core/async_utils.py`

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

## 4. 安全层 `core/security.py`

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

## 5. 中间件 `middleware/__init__.py`

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

## 6. 认证 API `api/auth.py`

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

## 7. 会话与聊天 API `api/sessions.py`

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

## 8. WebSocket `api/websocket.py`

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

## 9. 模型层数据完整性问题

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

## 10. 服务层问题

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

## 11. 额外 API 模块问题

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

## 12. 新发现的补充问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `Settings.load()` 调用不存在的方法 | `memory.py:593` | OpenHarness `Settings` 是 Pydantic `BaseModel`，没有 `load` 类方法。应使用 `load_settings()` 函数：`from openharness.config import load_settings; settings = load_settings()` |
| 2 | `load_settings()` 也不是 `Settings` 的方法 | `memory.py:591-593` | `from openharness.config.settings import Settings; settings = Settings.load()` — `Settings.load` 不存在。应改为 `from openharness.config import load_settings; settings = load_settings()` |
| 3 | `CompactCache` 的 `_entries` 字段声明有数据类问题 | `cached_compact.py:63` | `_entries` 以下划线开头表示私有，但作为 dataclass field 会有序列化问题。此外 OCH 的 `cache_service.py` 在模块级创建全局单例，多线程访问 `_entries` 无锁保护，可能导致 `RuntimeError: OrderedDict mutated during iteration` |
| 4 | `_NullHookExecutor` 内部导入可能失败 | `hook_service.py:39` | 当 OpenHarness 整体不可用时（`get_hook_executor()` 失败），`_NullHookExecutor` 作为降级实现被使用。但其 `execute()` 方法内部 `from openharness.hooks.types import AggregatedHookResult` 也可能失败，导致降级方案也崩溃。应在模块顶层导入或使用简单的数据类替代 |
| 5 | `_current_permission_mode` 是模块级全局变量 | `permissions.py:69` | 多 worker 部署时（如 Gunicorn 多进程），每个 worker 有独立的 `_current_permission_mode`，修改模式只影响当前 worker。应持久化到数据库或使用 Redis 共享状态 |
| 6 | `plugin_service.py` 在 async 方法中使用阻塞 `subprocess.run` | `plugin_service.py:172-178` | `_install_from_github()` 使用 `subprocess.run` 阻塞事件循环。应使用 `asyncio.create_subprocess_exec()` |
| 7 | `_install_from_npm()` 同上 | `plugin_service.py:184-191` | 同上，npx 命令也可能耗时较长，应使用异步子进程 |
| 8 | `sandbox.py` 安全检测使用简单字符串匹配 | `sandbox.py:338` | `security_check()` 使用 `pattern.lower() in command.lower()` 而非正则。简单的子串匹配容易绕过。例如 `rrm -rf /`（含空格变异）、`/bin/rm -rf /`（带路径前缀）可绕过 `'rm -rf /'` 匹配。且部分模式如 `wget.* | sh` 含正则语法但被当作字面量处理，`.*` 不会匹配任意字符。应使用正则表达式 `re.search()` |
| 9 | `coordinator_service.py` 的 `spawn_subagent()` 不持久化 | `coordinator_service.py:152-180` | 子代理任务仅存在于返回值中，进程重启后丢失。应创建 `SubagentTask` 数据库模型并持久化，或在 `Task` 模型中存储子代理信息 |
| 10 | `HookExecutionContext` 字段 `api_client` 为必填，不可传 None | `hook_service.py:24` vs `executor.py:41` | `executor.py:41` 定义 `api_client: SupportsStreamingMessages`（无默认值、无 Optional），OCH 传入 `api_client=None`。这在类型层面不合法，且 prompt hook 和 agent hook 内部会调用 `api_client` 的方法导致 `AttributeError`。应传入真实的 API client 实例或将字段改为 `Optional` 并添加 None 检查 |
| 11 | `permissions.py` 内嵌 `SimpleSettings` 不实现 `PermissionSettings` 接口 | `permissions.py:435-451` | `SimpleSettings` 缺少 `path_rules` 和 `denied_commands` 字段的正确类型。`PermissionSettings` 定义 `path_rules: list[PathRuleConfig]` 和 `denied_commands: list[str]`，但 `SimpleSettings.path_rules: list = []` 不包含 `PathRuleConfig` 对象。`PermissionChecker.__init__` 遍历 `path_rules` 并访问 `.pattern` 属性，`SimpleSettings` 传入空列表不会报错，但无法通过 DB 动态添加路径规则 |

## 13. 竞态条件与资源泄漏

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_compact_cache` 全局单例无锁保护 | `cache_service.py:9` | 多线程并发调用 `get_compact_cache()` 可能创建多个实例 |
| 2 | `_hook_executor` 全局单例无锁保护 | `hook_service.py:10` | 同上，但更危险，因为 `HookExecutor` 可能涉及状态变更 |
| 3 | `DualPoolSubagentExecutor._running_count` 用 `Lock()` 但调度循环用 `time.sleep(0.5)` 忙等待 | `subagent_executor.py:125` | 当并发已满时，调度线程持续占用 CPU 等待槽位释放，应使用 `threading.Condition` 或 `threading.Semaphore` |
| 4 | `DualPoolSubagentExecutor._tasks` 字典无大小限制 | `subagent_executor.py:80` | 如果不断提交任务但从不清理，已完成的任务会永远留在内存中，应添加 LRU 淘汰或定期清理 |
| 5 | `PermissionService._denial_log` 截断时重新创建列表 | `permission_service.py:192` | `self._denial_log = self._denial_log[-5000:]` 创建新列表，如果在并发写入时可能丢失记录。应使用 `collections.deque(maxlen=10000)` |

## 14. SQLite 兼容性问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `MemoryFact.tags.contains([tag])` — SQLite 不支持 JSON contains | `memory.py:99` | PostgreSQL 的 `jsonb` 支持 `contains`，但 SQLite 的 `json` 类型不支持。开发环境用 SQLite 会报错。应使用 `func.json_each()` 或手动过滤 |
| 2 | `func.json_array_length(Message.tool_uses)` — SQLite 无此函数 | `session_service.py:318-321` | `json_array_length` 是 PostgreSQL 内置函数。应改用 SQLAlchemy 的 `func.json_array_length` 并在 SQLite 下降级为 Python 端计算 |
| 3 | 并发写入 — SQLite 单写锁 | 全局 | SQLAlchemy Async + SQLite 在并发写入时会遇到 `database is locked`。应确保开发环境使用 WAL 模式或切换到 PostgreSQL |

## 15. 错误处理边界

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `alembic/env.py` 中 `from app.models import *` 在 venv 外可能失败 | `alembic/env.py:13` | 如果在非 venv 环境执行 `alembic upgrade`，`app.models` 可能找不到（依赖未安装），应添加 `try/except` 和清晰的错误提示 |
| 2 | `permissions.py` 中 `from openharness.permissions.denial_tracking import get_denial_tracker` 在顶层导入 | `permissions.py:15` | 如果 `openharness` 不完整安装，整个 Blueprint 无法加载，应延迟导入或在 `except` 中提供降级 |
| 3 | `memory.py` 中 `MemoryFact.tags.contains([tag])` SQLite 不支持 | `memory.py:99` | SQLite 不支持 JSON `contains` 操作，开发模式下使用 SQLite 会报错 |
| 4 | `session_service.py` 中 `func.json_array_length(Message.tool_uses)` SQLite 不支持 | `session_service.py:318-321` | `json_array_length` 是 PostgreSQL 函数，SQLite 中不存在 |
| 5 | `memory.py` 中 `func.lower(MemoryFact.content)` 搜索在大量数据时性能差 | `memory.py:201` | `ilike` 搜索无法使用索引，大量记忆事实时查询会很慢。应考虑全文搜索或 MSA 向量检索 |

## 16. 空目录问题

| 目录 | 状态 | 说明 |
|------|------|------|
| `backend/app/schemas/` | 空目录 | 架构文档未提及 schemas，API 直接用 `request.get_json()` 解析，缺少请求/响应验证 |
| `backend/app/utils/` | 空目录 | 未使用，可删除或补充工具函数 |

**调整建议**：
- `schemas/` 应添加 Pydantic schema 或 marshmallow schema 进行请求验证
- `utils/` 要么删除，要么添加通用工具函数（如分页计算、脱敏等）
