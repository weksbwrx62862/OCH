# OpenClaw-Harness 部署测试 Spec

## Why
OpenClaw-Harness 项目虽已通过功能验证（95/95 通过），但尚未进行实际部署测试。需要验证项目在类生产环境下能否完整部署运行，确保环境配置、依赖安装、服务启动、核心功能和错误处理机制均正常工作，并生成完整的部署测试报告。

## What Changes
- **无代码修改** — 本 spec 为纯部署测试验证性质
- 验证范围覆盖：环境配置、依赖安装、服务启动、核心功能、错误处理
- 输出：完整部署测试报告（测试步骤、测试结果、发现的问题及解决方案建议）

## Impact
- Affected code: `docker-compose.yml`、`backend/Dockerfile`、`backend/requirements.txt`、`frontend/package.json`、`.env.example`
- Affected specs: 依赖 `och-full-verification`（功能验证已通过）
- 验证环境: Docker Compose（PostgreSQL + Redis + Backend + Frontend）

## ADDED Requirements

### Requirement: DT-ENV 环境配置验证
系统 SHALL 在部署前验证所有环境配置项的正确性和完整性。

#### Scenario: 环境变量文件存在性检查
- **WHEN** 检查项目根目录是否存在 `.env` 文件
- **THEN** `.env` 文件存在且包含所有必要配置项
- **AND** 与 `.env.example` 对比无缺失的关键配置项

#### Scenario: 生产环境安全配置验证
- **WHEN** 检查 `.env` 中的安全相关配置
- **THEN** `SECRET_KEY` 不为默认值 `change-me-in-production`
- **AND** `JWT_SECRET_KEY` 不为默认值 `change-me-jwt-secret-min-32-chars`
- **AND** `APP_ENV` 设置为 `production` 或 `staging`

#### Scenario: Docker 配置验证
- **WHEN** 检查 `docker-compose.yml` 和各 `Dockerfile`
- **THEN** `docker-compose.yml` 语法正确且所有服务定义完整
- **AND** `backend/Dockerfile` 存在且基础镜像版本与 requirements 兼容
- **AND** `frontend/Dockerfile` 存在（若不存在则记录为部署阻塞问题）

#### Scenario: 数据库连接配置验证
- **WHEN** 检查 `DATABASE_URL` 配置
- **THEN** PostgreSQL 连接字符串格式正确（`postgresql+asyncpg://user:pass@host:port/db`）
- **AND** 连接参数与 `docker-compose.yml` 中 postgres 服务配置一致

### Requirement: DT-DEPS 依赖项安装检查
系统 SHALL 验证所有依赖项能够正确安装且版本兼容。

#### Scenario: 后端 Python 依赖安装
- **WHEN** 在后端虚拟环境中执行 `pip install -r requirements.txt`
- **THEN** 所有依赖包成功安装，无版本冲突
- **AND** 关键依赖（Flask、SQLAlchemy、uvicorn、redis、httpx）版本满足最低要求

#### Scenario: 前端 Node.js 依赖安装
- **WHEN** 在前端目录执行 `npm install`
- **THEN** 所有依赖包成功安装，无严重漏洞（npm audit）
- **AND** 关键依赖（next、react、zustand）版本满足要求

#### Scenario: 系统级依赖检查
- **WHEN** 检查部署环境系统级依赖
- **THEN** Python 版本 ≥ 3.11
- **AND** Node.js 版本 ≥ 20
- **AND** Docker 和 Docker Compose 可用

### Requirement: DT-STARTUP 服务启动流程测试
系统 SHALL 验证所有服务能够按正确顺序启动并达到就绪状态。

#### Scenario: Docker Compose 全栈启动
- **WHEN** 执行 `docker compose up -d --build`
- **THEN** 所有 4 个服务（postgres、redis、backend、frontend）成功启动
- **AND** 无容器在 30 秒内异常退出

#### Scenario: 数据库服务就绪检查
- **WHEN** 等待 postgres 服务健康检查通过
- **THEN** `pg_isready` 返回成功
- **AND** 数据库 `openclaw_harness` 已创建

#### Scenario: Redis 服务就绪检查
- **WHEN** 等待 redis 服务健康检查通过
- **THEN** `redis-cli ping` 返回 `PONG`

#### Scenario: 后端服务启动与数据库迁移
- **WHEN** 后端服务启动后执行 `alembic upgrade head`
- **THEN** 数据库迁移成功执行，无迁移错误
- **AND** 后端健康检查端点 `/health` 返回 200

#### Scenario: 前端服务启动
- **WHEN** 前端服务启动完成
- **THEN** `http://localhost:3000` 可访问
- **AND** 页面返回 200 状态码

#### Scenario: 服务间连通性验证
- **WHEN** 后端服务尝试连接 PostgreSQL 和 Redis
- **THEN** 数据库连接池正常建立
- **AND** Redis 缓存读写正常

### Requirement: DT-FUNC 核心功能验证
部署后的系统 SHALL 通过核心功能端到端验证。

#### Scenario: 后端 API 健康检查
- **WHEN** 请求 `http://localhost:8008/health`
- **THEN** 返回 `{status: "healthy", service: "openclaw-harness"}`

#### Scenario: API 文档可访问
- **WHEN** 请求 `http://localhost:8008/apidocs/`
- **THEN** Swagger UI 页面正常加载

#### Scenario: 核心 API 端点可达
- **WHEN** 请求各核心 API 端点（`/api/v1/agents`、`/api/v1/sessions`、`/api/v1/tasks` 等）
- **THEN** 返回有效 HTTP 响应（非连接错误）

#### Scenario: WebSocket 连接
- **WHEN** 建立 Socket.IO 连接到后端
- **THEN** 连接成功建立
- **AND** `connect` 事件正常触发

#### Scenario: 前端页面渲染
- **WHEN** 访问前端各页面路由
- **THEN** 页面正常渲染，无白屏或 500 错误

### Requirement: DT-ERROR 错误处理机制测试
系统 SHALL 在异常场景下正确处理错误并返回有意义的错误信息。

#### Scenario: 缺少环境变量时的启动行为
- **WHEN** 缺少必要环境变量（如 `DATABASE_URL`）启动后端
- **THEN** 服务启动失败并输出清晰的错误日志
- **AND** 错误信息指明缺失的配置项

#### Scenario: 数据库不可用时的错误处理
- **WHEN** PostgreSQL 服务未启动时请求后端 API
- **THEN** 后端返回 500 或 503 错误
- **AND** 错误日志记录数据库连接失败详情

#### Scenario: Redis 不可用时的降级行为
- **WHEN** Redis 服务未启动时请求后端 API
- **THEN** 后端仍能响应（降级模式）或返回明确错误
- **AND** 错误日志记录 Redis 连接失败详情

#### Scenario: 无效 API 请求的错误响应
- **WHEN** 发送格式错误的请求体到 API 端点
- **THEN** 返回 422 ValidationError + JSON 错误详情
- **AND** 错误响应包含 `error` 和 `code` 字段

#### Scenario: 未认证请求的拦截
- **WHEN** 未携带 Authorization header 请求受保护端点
- **THEN** 返回 401 + `{error: "Authentication required"}`

#### Scenario: Docker 容器异常退出后的恢复
- **WHEN** 某个服务容器异常退出
- **THEN** Docker 日志中包含异常原因
- **AND** `docker compose restart` 能恢复服务

### Requirement: DT-REPORT 部署测试报告生成
系统 SHALL 生成完整的部署测试报告。

#### Scenario: 报告内容完整性
- **WHEN** 所有部署测试步骤执行完毕
- **THEN** 报告包含：测试步骤、每步测试结果（通过/失败/跳过）
- **AND** 报告包含：发现的问题清单（严重程度、影响范围、复现步骤）
- **AND** 报告包含：解决方案建议
- **AND** 报告包含：部署环境信息（OS、Docker 版本、资源使用情况）

## MODIFIED Requirements
无 — 本 spec 为新增部署测试规格，不修改现有需求。

## REMOVED Requirements
无。
