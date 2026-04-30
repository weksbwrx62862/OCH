# 部署问题修复 Spec

## Why
部署测试发现 10 个问题（1 严重、6 中等、3 轻微），其中 asyncpg 与 Flask 同步模式的事件循环冲突导致 5+ 个 API 端点间歇性 500 错误，是影响生产部署的最严重问题。需要系统性地修复所有已识别问题并验证修复效果。

## What Changes
- 修复 `run_async()` 事件循环冲突 — 为每个请求创建独立事件循环和数据库会话
- 添加 `flasgger` 到 `requirements.txt`
- 修复 `.env.example` 中 `List[str]` 字段格式
- 修复 `alembic` 迁移目录名拼写（`alembir` → `alembic`）
- 修复 `AuthMiddleware` 对 404 路由的误拦截
- 创建 `frontend/Dockerfile`
- 修复 `docker-compose.yml` 端口冲突

## Impact
- Affected code: `backend/app/core/async_utils.py`、`backend/app/core/database.py`、`backend/requirements.txt`、`.env.example`、`backend/app/middleware/__init__.py`、`frontend/Dockerfile`、`docker-compose.yml`
- Affected specs: 依赖 `deployment-testing`（问题来源）

## ADDED Requirements

### Requirement: FIX-ASYNC 修复 asyncpg 事件循环冲突
系统 SHALL 在 Flask 同步上下文中正确运行 async 数据库操作，不产生事件循环冲突。

#### Scenario: 连续多次请求 API 端点
- **WHEN** 连续 10 次请求 `/api/v1/agents` 端点
- **THEN** 全部返回 HTTP 200，无 500 错误

#### Scenario: 并发请求多个不同 API 端点
- **WHEN** 同时请求 sessions、skills、coordinator、mcp、audit 端点
- **THEN** 全部返回有效 HTTP 响应（200 或预期业务错误码），无 500 内部错误

### Requirement: FIX-DEPS 修复依赖声明
`requirements.txt` SHALL 包含所有运行时依赖。

#### Scenario: 全新环境安装依赖
- **WHEN** 在全新虚拟环境中执行 `pip install -r requirements.txt`
- **THEN** 所有依赖（包括 flasgger）成功安装，应用可正常启动

### Requirement: FIX-ENV 修复环境配置模板
`.env.example` SHALL 提供与 pydantic-settings 兼容的配置格式。

#### Scenario: 从 .env.example 复制配置
- **WHEN** 将 `.env.example` 复制为 `.env` 并启动应用
- **THEN** 应用正常启动，无 `SettingsError` 解析错误

### Requirement: FIX-ALEMBIC 修复数据库迁移配置
alembic 迁移文件 SHALL 位于正确的 `alembic/versions/` 目录，且 `alembic.ini` 支持从环境变量读取数据库 URL。

#### Scenario: 执行数据库迁移
- **WHEN** 执行 `alembic upgrade head`
- **THEN** 迁移成功执行，所有表创建在目标数据库中

### Requirement: FIX-MIDDLEWARE 修复中间件路由拦截
AuthMiddleware SHALL 仅拦截需要认证的 API 路径，对不存在的路径返回 404 而非 401。

#### Scenario: 请求不存在的 API 路径
- **WHEN** 未认证请求 `/api/v1/nonexistent`
- **THEN** 返回 HTTP 404 + `{error: "Not found"}`

### Requirement: FIX-DOCKER 修复 Docker 部署配置
Docker Compose 全栈部署 SHALL 可成功构建和启动所有服务。

#### Scenario: 创建 frontend/Dockerfile
- **WHEN** 执行 `docker compose build frontend`
- **THEN** 前端镜像成功构建

#### Scenario: 端口冲突解决
- **WHEN** 本地 PostgreSQL/Redis 运行时执行 `docker compose up`
- **THEN** Docker 服务可正常启动（使用不同端口或条件启动）

## MODIFIED Requirements
无 — 本 spec 为新增修复规格。

## REMOVED Requirements
无。
