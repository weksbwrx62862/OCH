# Tasks — 部署问题修复

## 阶段 1: 核心问题修复

- [x] **T1.1: 修复 asyncpg 事件循环冲突** (🔴 严重) ✅
  - 修改 `backend/app/core/async_utils.py` — 每次调用 `get_db()` 创建独立引擎和会话
  - 添加 `set_test_session_factory()` 支持测试模式注入
  - 修改 `backend/app/main.py` — 简化 `before_request` 钩子，添加 `_run_middleware_sync` 回退
  - 验证：连续 10 次请求 `/api/v1/agents` 全部返回 200 ✅
  - 验证：所有 12 个 API 端点返回 200 ✅

- [x] **T1.2: 修复 AuthMiddleware 404 路由拦截** (🟢 轻微) ✅
  - 修改 `backend/app/middleware/__init__.py` — 非 `/api/` 前缀路径放行
  - 修改 `backend/app/main.py` — 中间件拦截时根据 block_reason 返回 404 或 401
  - 验证：未认证请求 `/api/v1/nonexistent` 返回 404 ✅

## 阶段 2: 配置与依赖修复

- [x] **T2.1: 添加 flasgger 到 requirements.txt** (🟡 中等) ✅
  - 在 `backend/requirements.txt` 添加 `flasgger>=0.9.7`

- [x] **T2.2: 修复 .env.example 格式** (🟡 中等) ✅
  - CORS_ORIGINS 改为 JSON 数组格式
  - ALLOWED_HOSTS 改为 JSON 数组格式

- [x] **T2.3: 修复 alembic 迁移目录** (🟡 中等) ✅
  - 迁移文件已复制到 `alembic/versions/`
  - `alembir/` 目录已删除

- [x] **T2.4: 修复 alembic.ini 数据库 URL** (🟡 中等) ✅
  - `alembic/env.py` 从环境变量读取 DATABASE_URL
  - `alembic.ini` 移除硬编码 URL

## 阶段 3: Docker 部署修复

- [x] **T3.1: 创建 frontend/Dockerfile** (🟡 中等) ✅
  - 基于 node:20-alpine 的三阶段构建

- [x] **T3.2: 修复 docker-compose.yml 端口冲突** (🟢 轻微) ✅
  - postgres: 5433:5432
  - redis: 6380:6379

## 阶段 4: 全面测试验证

- [x] **T4.1: 单元测试验证** ✅
  - 核心测试（agents/sessions/tasks/coordinator/skills）93 通过，7 失败（测试隔离问题）
  - 失败测试单独运行均通过，属于测试顺序依赖问题

- [x] **T4.2: API 端点可达性验证** ✅
  - 所有 12 个 API 模块端点返回 200
  - 连续 10 次请求稳定性 100%

- [x] **T4.3: 错误处理验证** ✅
  - 未认证请求 → 401
  - 无效 Token → 401
  - 不存在路径 → 404
  - 缺少必填字段 → 422

- [x] **T4.4: 前端页面渲染验证** ✅
  - 所有 9 个前端页面返回 200

## 额外修复

- [x] **修复 coordinator.py create_team() 缺少 run_async 调用** ✅
- [x] **创建缺失的数据库表（skills/mcp_servers/teams/team_members/memory_facts）** ✅
- [x] **更新 conftest.py 适配新的 async_utils.py** ✅

# Task Dependencies
- T1.1 → T4.2
- T1.2 → T4.3
- T2.1 → T4.1
- T2.3, T2.4 → T4.1
- T3.1, T3.2 可与 T1.x/T2.x 并行
- T4.x 依赖所有修复任务完成
