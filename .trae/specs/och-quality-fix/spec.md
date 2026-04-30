# OpenClaw-Harness 质量修复 Spec

## Why
项目存在 6 个 Critical 级安全漏洞（含 RCE、未认证端点、密钥泄露、XSS）、11 个 High 级问题（代码重复、线程不安全、逻辑 bug）、以及大量 Medium 级性能和代码质量问题。综合评分后端 4.6/10、前端 2.6/10，需要系统性修复以使项目达到生产可用标准。

## What Changes

### 第一阶段：安全加固（Critical）
- **C-01**: sandbox.py `/execute` 端点添加 `@require_auth` + `@require_role('admin')`，移除 `shell=True`，改用参数列表
- **C-02**: channels.py 所有 9 个端点添加 `@require_auth`
- **C-03**: config.py 启动时检测默认 SECRET_KEY/JWT_SECRET_KEY，若未修改则拒绝启动
- **C-04**: config API 的 providers 端点移除 `key_preview` 字段，改为 `key_configured: bool` + `key_source: str`
- **C-05**: sessions.py SSE 响应移除硬编码 `Access-Control-Allow-Origin: *`，使用 Flask CORS 配置
- **C-06**: 前端 chat/page.tsx 替换自写 MarkdownRenderer 为已安装的 `react-markdown` + `rehype-sanitize`

### 第二阶段：代码去重与基础修复（High）
- **H-01**: 创建 `app/core/async_utils.py`，统一 `_run_async()` 和 `_get_db()`，替换 11 个文件中的重复定义
- **H-02**: 修复 `update_agent` 名称唯一性检查顺序（先检查再 setattr）
- **H-03**: 修复 `before_request` 使用 `async def` 的问题（Flask 不支持 async before_request）
- **H-04**: 修复前端 chat/page.tsx 闭包 bug（消息无法保存），使用 ref 保存流式内容
- **H-05**: 全局缓存添加 LRU 上限（sessions/coordinator/channels/middleware）
- **H-06**: 替换所有 `datetime.utcnow()` 为 `datetime.now(timezone.utc)`（24 个文件）
- **H-07**: 替换所有 `__import__('datetime')` / `__import__('sqlalchemy')` 为顶部正常导入
- **H-08**: Session `agent_id='default'` 外键违反问题，改为 nullable

### 第三阶段：性能与代码规范优化（Medium 精选）
- **M-06**: `len(result.all())` 计数改用 `func.count()`
- **M-08**: 逐条删除日志改用批量 DELETE
- **M-11**: `get_permission_checker()` 添加 `threading.Lock`
- **M-15**: 前端关键位置添加 `useMemo`/`useCallback`/`React.memo`
- **M-16**: 前端 6 页面数据获取模式封装 `useApi` Hook
- **M-17**: 清理未使用的 npm 依赖

## Impact
- 受影响后端文件：sandbox.py, channels.py, config.py, api/config.py, sessions.py, agents.py, coordinator.py, main.py, audit.py, permissions.py, memory.py, tasks.py, skills.py, plugins.py, mcp.py, 所有模型文件, session_service.py, subagent_executor.py
- 受影响前端文件：chat/page.tsx, 所有页面组件, lib/api.ts
- 新增文件：app/core/async_utils.py
- **BREAKING**: sandbox.py `/execute` 端点现在需要认证和 admin 角色
- **BREAKING**: channels.py 所有端点现在需要认证
- **BREAKING**: config API providers 端点不再返回 `key_preview`
- **BREAKING**: Session.agent_id 从 `nullable=False` 改为 `nullable=True`

## ADDED Requirements

### Requirement: 安全认证覆盖
系统 SHALL 确保所有 API 端点（除 `/health` 和登录端点外）都需要认证。

#### Scenario: 未认证请求被拒绝
- **WHEN** 用户未提供有效 JWT Token 访问 sandbox/channels 端点
- **THEN** 返回 401 Unauthorized

#### Scenario: 非 admin 用户执行沙箱命令
- **WHEN** 非 admin 角色用户访问 `/sandbox/execute`
- **THEN** 返回 403 Forbidden

### Requirement: 默认密钥启动保护
系统 SHALL 在启动时检测 SECRET_KEY 和 JWT_SECRET_KEY 是否为默认值。

#### Scenario: 使用默认密钥启动
- **WHEN** SECRET_KEY 或 JWT_SECRET_KEY 为默认值
- **THEN** 应用拒绝启动并输出错误日志

### Requirement: API 密钥不泄露
系统 SHALL 不在 API 响应中返回 API 密钥的任何部分。

#### Scenario: 查询 Provider 列表
- **WHEN** 用户请求 `/config/providers`
- **THEN** 响应包含 `key_configured: bool` 和 `key_source: str`，不包含 `key_preview`

### Requirement: XSS 防护
系统 SHALL 对 AI 输出进行 HTML 消毒后再渲染。

#### Scenario: AI 输出包含恶意脚本
- **WHEN** AI 响应中包含 `<script>` 标签
- **THEN** 脚本标签被消毒移除，不执行

### Requirement: 统一异步工具
系统 SHALL 使用单一 `_run_async()` 和 `_get_db()` 实现，消除 11 处重复代码。

#### Scenario: API 文件使用异步工具
- **WHEN** 新 API 模块需要运行异步协程
- **THEN** 从 `app.core.async_utils` 导入统一实现

### Requirement: 前端消息保存
系统 SHALL 正确保存流式聊天消息到消息列表。

#### Scenario: 流式聊天完成
- **WHEN** SSE 流式响应完成
- **THEN** 用户消息和 AI 响应都被正确添加到 messages 列表

## MODIFIED Requirements

### Requirement: Session 模型 agent_id 字段
Session.agent_id 字段 SHALL 允许为空（nullable=True），当未指定 agent 时使用 NULL 而非 'default' 字符串。

## REMOVED Requirements
（无移除项）
