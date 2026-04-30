# 部署验证问题迭代修复 Spec

## Why
全面部署验证（95.8% 通过率）发现 3 个问题需要修复：Agent 删除关联 Session 时 IntegrityError、MCP 服务器详情 GET 接口缺失、工具名大小写敏感。本轮迭代修复这些问题并重新验证。

## What Changes
- 修复 Agent 模型 `sessions` 关系缺少级联删除配置
- 补充 MCP 服务器详情 GET 路由
- 工具详情接口支持大小写不敏感匹配
- 重新执行部署验证确认所有问题已修复

## Impact
- Affected code: `backend/app/models/agent.py`、`backend/app/api/mcp.py`、`backend/app/api/tools.py`
- Affected specs: `comprehensive-deployment-verification`（验证报告中的3个问题）

## ADDED Requirements

### Requirement: FIX-AGENT-CASCADE Agent 级联删除
系统 SHALL 在删除 Agent 时正确处理关联的 Session 记录。

#### Scenario: 删除有关联 Session 的 Agent
- **WHEN** 删除一个存在关联 Session 的 Agent
- **THEN** 关联 Session 被级联删除（或 Agent 删除被拒绝并返回明确错误）
- **AND** 不出现 IntegrityError 500 错误

#### Scenario: 删除无关联 Session 的 Agent
- **WHEN** 删除一个没有关联 Session 的 Agent
- **THEN** 删除成功返回 200
- **AND** 删除后 GET 返回 404

### Requirement: FIX-MCP-GET MCP 服务器详情 GET 接口
系统 SHALL 提供获取单个 MCP 服务器详情的 GET 接口。

#### Scenario: 获取存在的 MCP 服务器详情
- **WHEN** GET `/api/v1/mcp/servers/{id}` 且服务器存在
- **THEN** 返回 200 + 服务器详情 JSON

#### Scenario: 获取不存在的 MCP 服务器详情
- **WHEN** GET `/api/v1/mcp/servers/{id}` 且服务器不存在
- **THEN** 返回 404 + NotFoundError

### Requirement: FIX-TOOL-CASE 工具名大小写不敏感
系统 SHALL 在工具详情接口中支持大小写不敏感的工具名匹配。

#### Scenario: 使用小写工具名查询
- **WHEN** GET `/api/v1/tools/bash`
- **THEN** 返回 200 + Bash 工具详情（与 `/tools/Bash` 结果一致）

#### Scenario: 使用混合大小写工具名查询
- **WHEN** GET `/api/v1/tools/webfetch`
- **THEN** 返回 200 + WebFetch 工具详情

### Requirement: FIX-REVERIFY 修复后重新验证
修复完成后 SHALL 重新执行部署验证确认所有问题已解决。

#### Scenario: 重新验证修复项
- **WHEN** 对修复的 3 个问题重新执行验证
- **THEN** Agent 级联删除正常（无 IntegrityError）
- **AND** MCP 服务器详情 GET 返回 200
- **AND** 工具详情大小写不敏感匹配正常

## MODIFIED Requirements
无。

## REMOVED Requirements
无。
