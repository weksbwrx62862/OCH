# 全局配置与环境问题

## 1. 技术栈版本不一致

| 组件 | 架构文档描述 | 实际代码 | 问题 |
|------|------------|---------|------|
| Next.js | 14 (App Router) | **15.5.14** | `package.json` 实际使用 Next.js 15，文档需更新 |
| React | — | **19.2.4** | Next.js 15 配套 React 19，与 Next.js 14 + React 18 的文档不匹配 |
| SocketIO async_mode | — | `threading` | 生产环境应使用 `gevent` 或 `eventlet` 以获得更好并发性能 |

**调整建议**：更新架构文档中技术栈版本号为实际值，或降级前端依赖至 Next.js 14。

## 2. `.env` 配置问题

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

## 3. 配置一致性问题

### 3.1 双 Settings 系统耦合冲突

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | OCH `app/config.py` 和 OpenHarness `openharness/config/settings.py` 共享环境变量 | `config.py` / `settings.py` | 两套 Settings 都读取 `OPENHARNESS_MAX_TOKENS`、`OPENHARNESS_MAX_TURNS`、`ANTHROPIC_API_KEY`，形成隐式耦合。应明确单一配置源，OCH 应将 OpenHarness 的配置项透传而非重复定义 |
| 2 | OCH 默认值覆盖 OpenHarness 更优默认值 | `config.py:OPENHARNESS_MAX_TOKENS=4096` vs `settings.py:max_tokens=16384` | OCH 设置 `OPENHARNESS_MAX_TOKENS=4096`，OpenHarness 默认 `max_tokens=16384`。由于 OpenHarness 的 `_apply_env_overrides()` 读取同一环境变量，OCH 的较低值会覆盖 OpenHarness 的较高默认值。应将 OCH 默认值提升到 16384 或删除重复定义 |
| 3 | OCH 默认 `max_turns=8` vs OpenHarness 默认 `max_turns=200` | `config.py:OPENHARNESS_MAX_TURNS=8` | 同上，OCH 的 8 轮对话上限极低（对比 OpenHarness 的 200），会严重限制 Agent 能力。应至少提升到 50 或直接使用 OpenHarness 默认值 |
| 4 | `ANTHROPIC_API_KEY` 环境变量冲突 | `.env:ANTHROPIC_API_KEY=` (空) | `.env` 中 `ANTHROPIC_API_KEY` 为空字符串，OpenHarness `_apply_env_overrides()` 会将空字符串设为 API key，导致认证失败而非缺少 key 的清晰错误。应在 OpenHarness Settings 中对空字符串做 falsy 检查 |

### 3.2 `.env` 配置缺失与错误

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `ADMIN_PASSWORD` 未设置 | `.env` 缺失 | `auth.py:49-51` 使用 `os.getenv('ADMIN_PASSWORD', '')`，空密码意味着生产环境登录完全失效。应在 `.env` 中设置强密码，并添加非空校验 |
| 2 | `JWT_ALGORITHM` 未设置 | `.env` 缺失 | `auth.py` 默认 `'HS256'`，但如果环境变量拼写错误或缺失，可能导致 token 验证失败。建议在 `.env` 中显式设置 |
| 3 | `DATABASE_URL=sqlite+aiosqlite:///./och.db` — Docker 中无效 | `.env:6` | Docker 容器中使用 SQLite 相对路径 `./och.db` 会写入容器内部，容器重启后丢失。应改为 PostgreSQL URL `postgresql+asyncpg://och:och@db:5432/och` |
| 4 | `REDIS_URL=redis://localhost:6379/0` — Docker 中无效 | `.env:7` | Docker 中 Redis 容器名是 `redis`，不是 `localhost`。应改为 `redis://redis:6379/0` |
| 5 | `ANTHROPIC_API_KEY=` / `OPENAI_API_KEY=` 空值 | `.env:1-2` | 空字符串不同于未设置，某些库会将空字符串视为有效 key 导致认证失败。应删除等号或添加占位说明 |

### 3.3 Redis 配置但未使用

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `requirements.txt` 包含 `redis>=5.0.0`，`.env` 定义 `REDIS_URL` | `requirements.txt:54`, `.env:7` | 整个后端代码中没有实际使用 Redis 的地方（无 `import redis` 或 `aioredis`）。要么移除依赖和配置，要么实现 Redis 缓存/发布订阅功能 |
| 2 | `docker-compose.yml` 启动 Redis 容器 | `docker-compose.yml:redis` | Redis 容器占用资源但无用途。如不需要，应移除以节省资源 |
| 3 | SocketIO 未配置 Redis 消息队列 | `main.py:socketio` | 多 worker 部署时，SocketIO 需要 Redis 或其他消息队列来跨进程广播事件。当前使用默认内存队列，多 worker 下事件会丢失 |

### 3.4 requirements.txt 问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `requirements.txt` 中 `httpx` 重复声明 | `requirements.txt:38,62` | 第 38 行 `httpx>=0.25.0` 和第 62 行 `httpx>=0.25.0` 重复，应去重 |
