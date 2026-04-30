# 继续找问题 — 第二轮深度问题修复 Spec

## Why
前一轮修复（och-quality-fix、remaining-issues-fix、fix-verification-issues）已解决了安全加固、代码去重、基础Bug等问题，但深度扫描发现仍存在 **2 个 Critical、11 个 High、15 个 Medium** 级别的新问题，涵盖安全漏洞、连接池泄漏、架构缺陷、前端Bug和部署配置错误。这些问题不修复将严重影响生产环境的安全性和稳定性。

## What Changes
- 修复登录接口无密码验证（Critical 安全漏洞）
- 修复 async_utils.get_db() 连接池泄漏（Critical Bug）
- 补全缺失的数据库迁移脚本（5 张表无迁移）
- 注册 Flask 全局错误处理器
- 修复权限模式切换和审计清除端点的权限不足
- 修复 WebSocket 连接无认证校验
- 修复前端 Chat 页面多个闭包/状态Bug
- 修复前端 useApi hook 无限循环风险
- 修复部署配置问题（SocketIO CORS、容器 root、健康检查等）
- 修复测试中的宽松断言和 CI 配置问题
- 统一异常处理和分页逻辑
- 修复前端操作无反馈和审计导出无认证问题

## Impact
- Affected specs: och-quality-fix, remaining-issues-fix, fix-verification-issues
- Affected code:
  - backend/app/api/auth.py — 登录逻辑
  - backend/app/core/async_utils.py — 数据库会话管理
  - backend/app/core/database.py — 引擎单例
  - backend/app/main.py — Flask 错误处理器、SocketIO CORS
  - backend/app/api/permissions.py — 权限端点
  - backend/app/api/websocket.py — WebSocket 认证
  - backend/app/api/coordinator.py — update_team Bug
  - backend/app/api/memory.py — 竞态条件
  - backend/app/api/audit.py — 审计导出认证
  - backend/app/api/tools.py — _find_tool 空指针
  - backend/app/models/team.py — to_dict Bug
  - backend/app/models/message.py — ToolResult 时间戳
  - backend/alembic/versions/ — 迁移脚本
  - backend/Dockerfile — 非 root 用户
  - docker-compose.yml — 健康检查、--reload
  - .env.example — 端口修正
  - frontend/app/chat/page.tsx — 多个 Bug
  - frontend/lib/hooks/useApi.ts — 无限循环
  - frontend/app/audit/page.tsx — 导出认证
  - frontend/next.config.js — 安全头、环境变量
  - frontend/lib/api.ts — console.log 清理

## ADDED Requirements

### Requirement: 登录接口密码验证
系统 SHALL 在 `/api/v1/auth/login` 端点验证用户密码。当 `APP_ENV != 'development'` 时，必须验证密码哈希匹配才发放 JWT Token。

#### Scenario: 开发环境无密码登录
- **WHEN** APP_ENV 为 'development' 且请求包含有效 username
- **THEN** 系统发放 JWT Token（保持向后兼容）

#### Scenario: 生产环境密码验证
- **WHEN** APP_ENV 不为 'development' 且请求包含 username 和 password
- **THEN** 系统验证密码哈希匹配后发放 JWT Token

#### Scenario: 密码错误
- **WHEN** 密码验证失败
- **THEN** 返回 401 Unauthorized

### Requirement: 数据库连接池单例管理
系统 SHALL 使用单一数据库引擎实例管理连接池。`async_utils.get_db()` SHALL 复用 `database.py` 的引擎单例，而非每次创建新引擎。

#### Scenario: 高并发请求
- **WHEN** 多个并发 API 请求同时调用 get_db()
- **THEN** 所有请求共享同一引擎实例和连接池，不创建额外引擎

### Requirement: Flask 全局错误处理器
系统 SHALL 注册 Flask 错误处理器，将 `OCHError` 及其子类自动转换为对应 HTTP 状态码的 JSON 响应。

#### Scenario: 抛出 NotFoundError
- **WHEN** API 视图函数抛出 NotFoundError
- **THEN** 返回 404 状态码和 JSON 错误响应（而非 500 HTML 页面）

#### Scenario: 抛出 ValidationError
- **WHEN** API 视图函数抛出 ValidationError
- **THEN** 返回 422 状态码和 JSON 错误响应

### Requirement: WebSocket 连接认证
系统 SHALL 在 WebSocket 连接建立时验证客户端身份。未认证的连接 SHALL 被拒绝。

#### Scenario: 携带有效 Token 连接
- **WHEN** 客户端携带有效 JWT Token 建立 WebSocket 连接
- **THEN** 连接成功建立

#### Scenario: 无 Token 或 Token 无效
- **WHEN** 客户端未携带 Token 或 Token 无效
- **THEN** 连接被拒绝

### Requirement: 前端 Chat 页面状态修复
系统 SHALL 修复 Chat 页面中 usage 闭包陷阱、tool_end 事件污染、流式错误时用户消息丢失、多工具调用丢失等 Bug。

#### Scenario: 流式完成后 usage 正确保存
- **WHEN** 流式聊天完成
- **THEN** 消息中的 usage 数据为最新值而非旧值

#### Scenario: 流式错误时用户消息不丢失
- **WHEN** streamChat 抛出异常
- **THEN** 用户输入的消息仍被添加到消息列表

#### Scenario: 多工具调用全部保留
- **WHEN** Agent 在一个 turn 中调用多个工具
- **THEN** 所有工具调用都被保留到消息中

### Requirement: 前端操作反馈机制
系统 SHALL 在所有异步操作（创建/删除/更新）失败时向用户显示错误通知。

#### Scenario: 操作失败通知
- **WHEN** 创建智能体、删除会话等操作失败
- **THEN** 页面显示错误通知提示用户

### Requirement: 数据库迁移补全
系统 SHALL 提供完整的 Alembic 迁移脚本，覆盖所有 ORM 模型对应的数据库表。

#### Scenario: 新部署执行迁移
- **WHEN** 在新环境中执行 `alembic upgrade head`
- **THEN** 所有 14 张表（含 skills、teams、team_members、mcp_servers、memory_facts）均被创建

### Requirement: 部署安全加固
系统 SHALL 在生产部署配置中移除安全隐患：SocketIO CORS 白名单、后端容器非 root 运行、健康检查、移除 --reload。

#### Scenario: SocketIO 跨域限制
- **WHEN** WebSocket 客户端从非白名单来源发起连接
- **THEN** 连接被拒绝

#### Scenario: 后端容器非 root
- **WHEN** 后端 Docker 容器启动
- **THEN** 应用进程以非 root 用户运行

## MODIFIED Requirements

### Requirement: 权限端点访问控制
权限模式切换端点 `PUT /permissions/modes/<mode_id>` SHALL 要求 admin 角色。审计拒绝记录清除端点 `POST /permissions/denials/clear` SHALL 要求 admin 角色。

### Requirement: 前端审计导出
审计日志导出 SHALL 通过带 Authorization header 的 fetch 请求完成，而非 `window.open()` 无认证下载。

## REMOVED Requirements
无移除项。
