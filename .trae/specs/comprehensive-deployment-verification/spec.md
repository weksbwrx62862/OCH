# OpenClaw-Harness 全面部署验证 Spec

## Why
项目已完成基础部署测试和功能验证，但尚未进行系统性的命令行部署验证。需要通过命令行工具（curl/httpie/pytest）对运行中的系统执行全面验证，覆盖核心业务流程、用户交互场景、数据处理逻辑及系统集成点，确保部署环境满足业务需求和质量标准。

## What Changes
- **无代码修改** — 本 spec 为纯验证性质
- 验证范围覆盖：核心业务流程（CRUD全链路）、用户交互场景（认证/权限/聊天）、数据处理逻辑（DAG/级联/事务）、系统集成点（WebSocket/前后端/数据库/Redis）
- 输出：完整部署验证报告（功能正常项、异常项、潜在风险点、修复建议）

## Impact
- Affected code: 全部 `backend/app/api/` + `frontend/app/`
- Affected specs: 依赖 `deployment-testing`（基础部署已通过）、`och-full-verification`（功能验证已通过）
- 验证环境: 本地运行的后端(8008) + 前端(3000) + PostgreSQL(5432) + Redis(6379)

## ADDED Requirements

### Requirement: DV-AUTH 认证与用户交互验证
系统 SHALL 在部署环境下正确处理完整的认证生命周期。

#### Scenario: 登录获取 Token
- **WHEN** 使用有效凭据 POST `/api/v1/auth/login`
- **THEN** 返回 200 + `access_token` + `user` 对象
- **AND** Token 可被后续请求成功使用

#### Scenario: Token 过期/无效拒绝
- **WHEN** 使用无效或过期 Token 请求受保护端点
- **THEN** 返回 401 + `{error: "Invalid or expired token"}`

#### Scenario: 角色权限隔离
- **WHEN** 普通用户尝试管理员操作（如创建 Agent）
- **THEN** 返回 403 + `{error: "Insufficient permissions"}`

#### Scenario: 未认证请求拦截
- **WHEN** 不携带 Authorization 请求受保护端点
- **THEN** 返回 401 + `{error: "Authentication required"}`

### Requirement: DV-AGENT Agent 完整业务流程验证
系统 SHALL 支持从创建到删除的 Agent 完整生命周期，且数据一致性有保障。

#### Scenario: Agent CRUD 全链路
- **WHEN** 依次执行 创建→列表→详情→更新→统计→权限查询→删除
- **THEN** 每步返回正确状态码和数据
- **AND** 删除后再次 GET 返回 404
- **AND** 创建同名 Agent 返回 422 冲突

#### Scenario: Agent 数据一致性
- **WHEN** 创建 Agent 后查询列表和详情
- **THEN** 列表中包含新建 Agent，详情数据与创建时一致
- **AND** 更新后详情反映更新内容

#### Scenario: Agent 权限配置
- **WHEN** 查询 Agent 的工具权限
- **THEN** 返回权限配置数组，结构包含 tool_name 和 permission 字段

### Requirement: DV-SESSION 会话与聊天交互验证
系统 SHALL 支持完整的会话生命周期和聊天消息交互。

#### Scenario: 会话生命周期
- **WHEN** 创建→暂停→恢复→统计→删除会话
- **THEN** 状态正确流转：active→paused→active
- **AND** 统计数据准确

#### Scenario: 非流式聊天消息
- **WHEN** 向活跃会话发送消息
- **THEN** 返回 200 + response 字段
- **AND** 消息历史中包含发送的消息

#### Scenario: 流式 SSE 聊天
- **WHEN** 发送流式聊天请求
- **THEN** 返回 200 + content-type 含 text/event-stream
- **AND** 响应体包含 data: 前缀的 SSE 事件

#### Scenario: 空消息验证
- **WHEN** 发送空内容消息
- **THEN** 返回 422 ValidationError

### Requirement: DV-TASK 任务 DAG 数据处理验证
系统 SHALL 正确处理任务依赖关系和状态流转。

#### Scenario: 单任务创建与状态流转
- **WHEN** 创建任务并依次更新状态 pending→running→completed
- **THEN** 每次状态更新返回 200 + 新状态
- **AND** 不合法的状态流转被拒绝

#### Scenario: DAG 依赖创建
- **WHEN** 使用 create-with-deps 创建带依赖的任务组
- **THEN** 返回任务列表和依赖关系
- **AND** 依赖任务状态正确关联

#### Scenario: 任务停止与删除
- **WHEN** 停止运行中的任务并删除
- **THEN** 停止操作成功，删除后 GET 返回 404
- **AND** 级联删除正确处理依赖关系

#### Scenario: 任务统计
- **WHEN** 查询全局任务统计
- **THEN** 返回 total 和 by_status 分组数据

### Requirement: DV-SKILL 技能管理验证
系统 SHALL 正确管理技能的注册、发现和启用/禁用。

#### Scenario: 技能列表与分类
- **WHEN** 查询技能列表和分类
- **THEN** 返回合并的 DB+FS 技能数据和分类统计

#### Scenario: 技能启用/禁用
- **WHEN** 启用/禁用指定技能
- **THEN** 操作成功返回 200
- **AND** 技能状态正确切换

### Requirement: DV-COORD 协调器与团队管理验证
系统 SHALL 支持多智能体团队的创建和管理。

#### Scenario: 团队 CRUD
- **WHEN** 创建→列表→详情→删除团队
- **THEN** 每步返回正确状态码和数据

#### Scenario: Agent 定义列表
- **WHEN** 查询可用 Agent 定义
- **THEN** 返回内置和自定义 Agent 定义列表

### Requirement: DV-PERM 权限系统验证
系统 SHALL 正确执行 RBAC 权限控制和路径规则管理。

#### Scenario: 权限模式与规则
- **WHEN** 查询权限模式和规则列表
- **THEN** 返回可用模式和当前规则

#### Scenario: 规则创建
- **WHEN** 创建新的权限规则
- **THEN** 返回 201 + 规则数据

#### Scenario: DenialTracker 状态
- **WHEN** 查询拒绝追踪器状态
- **THEN** 返回当前拒绝记录和统计

### Requirement: DV-INTEG 系统集成点验证
系统 SHALL 在各集成点正确交互。

#### Scenario: WebSocket 实时通信
- **WHEN** 建立 Socket.IO 连接
- **THEN** 连接成功建立并触发 connect 事件
- **AND** join_session 事件可正常加入会话房间

#### Scenario: 前端页面可达性
- **WHEN** 访问前端所有页面路由
- **THEN** 每个页面返回 200，无白屏或 500 错误

#### Scenario: 前后端 API 连通性
- **WHEN** 前端通过 API 代理访问后端
- **THEN** 请求正确转发，响应正常返回

#### Scenario: 数据库连接池
- **WHEN** 后端执行数据库读写操作
- **THEN** 连接池正常建立和释放
- **AND** 无连接泄漏警告

#### Scenario: Redis 缓存
- **WHEN** 后端执行缓存操作
- **THEN** Redis 读写正常

### Requirement: DV-MCP-MEM MCP与记忆系统集成验证
系统 SHALL 正确管理 MCP 服务器和记忆事实库。

#### Scenario: MCP 服务器管理
- **WHEN** 执行 MCP 服务器 CRUD 操作
- **THEN** 列表、创建、详情、更新、删除均正常

#### Scenario: 记忆事实库 CRUD
- **WHEN** 执行记忆事实的创建→列表→详情→删除
- **THEN** 每步返回正确状态码和数据

### Requirement: DV-ERR 错误处理与边界场景验证
系统 SHALL 在异常场景下正确处理并返回有意义的错误信息。

#### Scenario: 资源不存在
- **WHEN** 请求不存在的资源 ID
- **THEN** 返回 404 + NotFoundError

#### Scenario: 数据验证错误
- **WHEN** 发送缺少必填字段的请求
- **THEN** 返回 422 + ValidationError 详情

#### Scenario: 重复资源创建
- **WHEN** 创建已存在的同名资源
- **THEN** 返回 422 冲突错误

#### Scenario: 非法状态转换
- **WHEN** 执行不合法的状态转换（如 completed→running）
- **THEN** 返回 422 业务逻辑错误

### Requirement: DV-REPORT 部署验证报告生成
系统 SHALL 生成完整的部署验证报告。

#### Scenario: 报告内容完整性
- **WHEN** 所有验证步骤执行完毕
- **THEN** 报告包含：每项验证结果（通过/失败/跳过）
- **AND** 报告包含：异常项详情（端点、请求、响应、错误信息）
- **AND** 报告包含：潜在风险点评估
- **AND** 报告包含：修复建议和优先级
- **AND** 报告包含：环境信息（服务版本、运行时长、资源使用）

## MODIFIED Requirements
无 — 本 spec 为新增验证规格，不修改现有需求。

## REMOVED Requirements
无。
