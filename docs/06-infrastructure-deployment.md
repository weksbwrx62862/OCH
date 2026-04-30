# 基础设施与部署问题

## 1. Docker Compose

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

## 2. Infrastructure 目录

| 目录 | 状态 | 调整建议 |
|------|------|---------|
| `infrastructure/nginx/` | 空 | 应添加 nginx.conf 反向代理配置 |
| `infrastructure/postgres/` | 空 | 应添加 init.sql 或迁移脚本 |
| `infrastructure/redis/` | 空 | 应添加 redis.conf 配置 |

## 3. Backend Dockerfile

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 使用 `python:3.11-slim` | `backend/Dockerfile:1` | `requirements.txt` 中部分依赖（如 `asyncpg`）需要编译，`slim` 镜像可能缺少编译工具。当前有 `build-essential` 但增加了镜像体积 |
| 2 | 未安装 Node.js | — | 部分前端相关工具可能需要 Node.js，但当前后端 Dockerfile 不包含 |

## 4. Docker 部署配置问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `.env` 与 `docker-compose.yml` 的服务发现不一致 | `.env` / `docker-compose.yml` | `.env` 中 `DATABASE_URL` 和 `REDIS_URL` 使用 `localhost`，但 Docker Compose 网络中服务名是 `db` 和 `redis`。需要创建 `.env.docker` 或在 compose 文件中覆盖环境变量 |
| 2 | `docker-compose.yml` 只使用 `env_file: .env` | `docker-compose.yml:14` | 无法区分开发/生产环境配置。应在 compose 的 `environment` 块中覆盖 Docker 专用变量，或使用多个 env 文件 |
| 3 | PostgreSQL 容器启动但未被使用 | `docker-compose.yml:db` | `.env` 指向 SQLite，PostgreSQL 容器白白运行。应修正 `DATABASE_URL` 指向 PostgreSQL |
| 4 | 健康检查依赖 `/health` 但未验证数据库连接 | `docker-compose.yml:healthcheck` | `/health` 只返回静态 `{"status": "ok"}`，不检查数据库或 OpenHarness 连接。容器可能"健康"但实际无法工作 |

## 5. Alembic 迁移不一致

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `alembic.ini` 缺少 `sqlalchemy.url` 配置 | `backend/alembic.ini` | 标准的 alembic.ini 应包含 `sqlalchemy.url`，当前依赖 `env.py` 动态设置，但缺少 fallback 时迁移命令可能失败 |
| 2 | 迁移脚本 001 中 `sessions.agent_id` 是 `nullable=False` | `alembic/versions/001_initial_schema.py:37` | 但模型定义 `session.py:28` 是 `nullable=True`。迁移脚本与模型定义不一致，Alembic autogenerate 会检测到差异 |
| 3 | `ToolResult.completed_at` 在迁移中 `server_default=sa.func.now()` | `alembic/versions/001_initial_schema.py:78` | 但模型定义 `message.py:82` 是 `nullable=True` 无默认值，迁移自动设置了创建时间，不一致 |
| 4 | `mcp_servers` 表缺少 `name` 唯一约束 | `alembic/versions/002_add_skills_teams_mcp_memory.py:68` | 模型中 `MCPServer.name` 没有设置 `unique=True`，但实际业务场景中 MCP 服务器名称应该唯一，否则会创建重复配置 |
| 5 | `sessions.agent_id` — 迁移 `nullable=False`，模型 `nullable=True` | `001_initial_schema.py:37` vs `models.py` | 迁移脚本定义 `agent_id` 为 NOT NULL，但模型定义允许 NULL。后续迁移或 ORM 操作会冲突。应统一为 `nullable=True` 并创建修正迁移 |
| 6 | `ToolResult.completed_at` — 迁移有 `server_default=sa.func.now()`，模型无默认 | `001_initial_schema.py:78` vs `models.py` | 迁移定义了数据库级别的默认值，但 ORM 模型不知道这个默认值，可能导致 ORM 插入时传 `None` 而触发默认值。应在模型中添加 `server_default` 或在 Python 层设置默认值 |
| 7 | `mcp_servers` 表缺少 `name` 唯一约束 | `002_add_skills_teams_mcp_memory.py` | 模型定义 `name` 有 `unique=True`，但迁移脚本未创建唯一索引。应添加修正迁移 |

## 6. `start.sh` 问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 未检查依赖是否安装 | `start.sh` | 直接运行 `flask`/`next` 而不检查 Python/Node 是否安装或 venv 是否存在。应添加前置检查 |
| 2 | 未运行数据库迁移 | `start.sh` | 启动后端前应执行 `alembic upgrade head`，否则新部署的数据库表不存在 |
| 3 | 未设置 `FLASK_APP` 环境变量 | `start.sh` | Flask 需要 `FLASK_APP` 才能正确找到应用工厂。应添加 `export FLASK_APP=app.main:create_app()` |

## 7. 数据库迁移与索引

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 迁移脚本 001 与模型定义不一致：`sessions.agent_id` | `001_initial_schema.py:37` vs `session.py:28` | 迁移中 `nullable=False`，模型中 `nullable=True`。执行 `alembic upgrade head` 后再 `alembic revision --autogenerate` 会检测到差异 |
| 2 | `ToolResult.completed_at` 迁移有 `server_default` 但模型没有 | `001_initial_schema.py:78` vs `message.py:82` | 同上，迁移自动设置 `sa.func.now()` 作为默认值，但模型中 `nullable=True` 无默认值 |
| 3 | 缺少 `sessions.created_at` 索引 | — | Session 列表按 `updated_at` 排序但经常按 `agent_id` 过滤，已有 `agent_id` 索引但无 `created_at` 索引 |
| 4 | `messages` 表缺少 `(session_id, created_at)` 复合索引 | — | 获取会话消息时按 `session_id` 过滤 + `created_at` 排序，复合索引可大幅提升性能 |
| 5 | `audit_logs` 缺少 `(user_id, created_at)` 复合索引 | — | 按用户筛选审计日志 + 按时间排序是常见查询模式 |
| 6 | `task_dependencies` 缺少 `(dep_task_id)` 索引 | — | 反向查找"哪些任务依赖于我"时需要此索引 |

## 8. 错误处理边界

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `alembic/env.py` 中 `from app.models import *` 在 venv 外可能失败 | `alembic/env.py:13` | 如果在非 venv 环境执行 `alembic upgrade`，`app.models` 可能找不到（依赖未安装），应添加 `try/except` 和清晰的错误提示 |
| 2 | `permissions.py` 中 `from openharness.permissions.denial_tracking import get_denial_tracker` 在顶层导入 | `permissions.py:15` | 如果 `openharness` 不完整安装，整个 Blueprint 无法加载，应延迟导入或在 `except` 中提供降级 |

## 9. 基础设施问题严重度总结

| 严重度 | 数量 | 关键问题 |
|--------|------|---------|
| **P0 - 运行时崩溃** | 0 | 无 |
| **P1 - 功能失效** | 5 | QueryEngine 创建后未使用、Redis 配置但未用、Docker 网络配置错误、SQLite 不兼容函数、WebSocket 代理缺失 |
| **P2 - 安全/数据风险** | 0 | 无 |
| **P3 - 配置/一致性** | 7 | 双 Settings 冲突、环境变量覆盖默认值、.env 缺失项、Alembic 不一致、前端 SSR 代理问题 |

## 10. 建议修复优先级

1. **P1 - 尽快修复**：
   - Docker 网络配置错误（.env vs docker-compose.yml 服务发现）
   - PostgreSQL 容器启动但未被使用
   - 健康检查不验证数据库连接
   - 未运行数据库迁移

2. **P2 - 计划修复**：
   - 缺少 `.env.example` 文件
   - Infrastructure 目录为空
   - 数据库索引缺失
   - `start.sh` 缺少前置检查

3. **P3 - 长期优化**：
   - Alembic 迁移不一致
   - Backend Dockerfile 使用 slim 镜像
