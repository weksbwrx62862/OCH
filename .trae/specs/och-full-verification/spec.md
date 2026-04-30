# OpenClaw-Harness 全面功能验证 Spec

## Why
OpenClaw-Harness 项目已完成 Phase 1（后端 API 数据库化）和 Phase 2（前端页面补全），需要进行全面功能验证以确保：
- 项目能够正常启动运行
- 89 个 API 路由全部正确注册且可访问
- 8 个前端页面正常渲染
- 核心业务流程（Agent CRUD、Session/Chat、Task DAG）端到端可用
- 数据库操作正确无误，无数据丢失或异常

## What Changes
- **无代码修改** — 本 spec 为纯验证性质
- 验证范围覆盖：启动流程、API 路由、认证授权、数据库模型、前端渲染、E2E 流程
- 输出：详细验证报告（通过/失败/异常记录）

## Impact
- Affected code: 全部 `backend/app/` + `frontend/app/`
- Affected specs: 无前置 spec 依赖
- 验证环境: Python 3.13 + Flask + SQLite (测试模式) + Next.js 14

## ADDED Requirements

### Requirement: V-STARTUP 项目启动验证
系统 SHALL 能够在测试环境下成功初始化 Flask 应用实例。

#### Scenario: 应用创建与路由注册
- **WHEN** 执行 `create_app()` 并传入测试环境变量
- **THEN** 应用实例成功创建，无 ImportError / AttributeError
- **AND** 89 个 API 路由全部注册到 URL Map
- **AND** Socket.IO 事件处理器正确绑定
- **AND** 认证中间件 (`init_security`) 已激活

#### Scenario: 数据库表自动创建
- **WHEN** 使用内存 SQLite 引擎调用 `_init_db_tables()`
- **THEN** 所有 14 个模型对应的数据库表成功创建
- **AND** 表结构包含所有定义的字段和关系

### Requirement: V-API API 路由完整性验证
系统 SHALL 提供 89 个可访问的 RESTful API 端点。

#### Scenario: Blueprint 路由注册检查
- **WHEN** 遍历 `app.url_map.iter_rules()` 过滤 `/api/v1` 前缀的路由
- **THEN** 每个路由具有唯一的 endpoint 名称（无冲突）
- **AND** 每个路由关联到正确的 HTTP 方法集合
- **AND** 各 Blueprint 路由数量符合预期：agents(9), sessions(9), tasks(11), skills(8), coordinator(9), permissions(8), mcp(7), plugins(7), config(10), tools(6), audit(5)

### Requirement: V-AUTH 认证与权限验证
系统的 JWT 认证和 RBAC 权限控制 SHALL 正常工作。

#### Scenario: 未认证访问拦截
- **WHEN** 未携带 Authorization header 请求受保护端点
- **THEN** 返回 HTTP 401 + JSON 错误体 `{error: "Authentication required"}`

#### Scenario: 角色权限控制
- **WHEN** 普通用户 (`role: user`) 请求管理员端点（如 POST /agents）
- **THEN** 返回 HTTP 403 + JSON 错误体 `{error: "Insufficient permissions"}`

#### Scenario: Token 创建与验证
- **WHEN** 调用 `create_jwt({user_id, username, role})` 生成 token
- **THEN** Token 可被正确解码并提取 user_id/username/role

### Requirement: V-DB 数据库操作验证
所有 CRUD 操作 SHALL 正确读写数据库，数据一致性有保障。

#### Scenario: Agent 完整生命周期
- **WHEN** 依次执行 Agent 的 Create → List → Get → Update → Stats → Delete 操作
- **THEN** 每步返回正确的 HTTP 状态码和数据内容
- **AND** 删除后再次 GET 返回 404
- **AND** 重名 Agent 时检测到冲突返回 422

#### Scenario: Session 与 Chat 完整流程
- **WHEN** 创建 Session → 发送消息(非流式) → 获取消息历史 → 获取统计 → 删除 Session
- **THEN** 全部操作成功，消息计数准确
- **AND** 空消息内容返回 422 ValidationError

#### Scenario: Task DAG 创建与依赖
- **WHEN** 通过 `create-with-deps` 创建带依赖的任务组
- **THEN** 返回任务列表和依赖关系
- **AND** 任务状态流转符合规则 (pending→running→completed)

### Requirement: V-FRONTEND 前端渲染验证
前端 8 个页面 SHALL 能够被 Next.js 正确编译和渲染。

#### Scenario: 页面文件存在性
- **WHEN** 检查 `frontend/app/` 下所有 `page.tsx` 文件
- **THEN** 以下 8 个页面全部存在：/, /chat, /tools, /skills, /swarm, /settings, /agents, /sessions

#### Scenario: 前端编译检查
- **WHEN** 在 frontend 目录执行 TypeScript 编译检查
- **THEN** 无 Type Error（允许 warning）

### Requirement: V-E2E 端到端完整流程验证
核心业务场景 SHALL 从 API 层面端到端可用。

#### Scenario E2E-1: 完整聊天会话
- **WHEN** 模拟完整流程：登录 → 创建 Agent → 创建 Session → 发送消息 → 查看历史 → 查看 Agent 统计
- **THEN** 每步返回预期状态码 (201/200)，数据链路完整

#### Scenario E2E-2: 多模块协作
- **WHEN** 依次调用 Tasks API → Skills API → Coordinator API → Permissions API → Audit API
- **THEN** 每个 API 模块返回有效响应（非 500 Internal Server Error）

## MODIFIED Requirements
无 — 本 spec 为新增验证规格，不修改现有需求。

## REMOVED REQUIREMENTS
无。
