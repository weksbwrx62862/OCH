# 前端功能按钮验证与修复 Spec

## Why
用户反馈前端很多功能按钮没有效果。需要系统性地验证所有前端页面的按钮和交互功能，识别无效按钮并修复，确保前端与后端 API 正确对接。

## What Changes
- 验证所有前端页面的按钮功能
- 识别无效按钮（无 onClick、API 调用失败、路由错误等）
- 修复按钮功能或添加缺失的实现
- 确保前端与后端 API 正确对接

## Impact
- Affected code: `frontend/app/*/page.tsx`、`frontend/lib/api.ts`、`frontend/components/*`
- Affected specs: 依赖 `frontend-backend-correspondence-check`

## ADDED Requirements

### Requirement: FE-BTN 所有按钮必须有有效功能
前端所有可见按钮 SHALL 有明确的 onClick 处理或链接目标。

#### Scenario: 点击按钮有响应
- **WHEN** 用户点击任意按钮
- **THEN** 系统执行预期操作（导航、API 调用、状态变更等）
- **AND** 用户能看到操作结果（页面跳转、数据更新、提示消息等）

### Requirement: FE-API 所有 API 调用必须成功
前端所有 API 调用 SHALL 正确配置并返回预期数据。

#### Scenario: API 调用成功
- **WHEN** 前端调用后端 API
- **THEN** 返回 HTTP 200 或预期状态码
- **AND** 响应数据格式与前端期望一致

### Requirement: FE-NAV 所有导航链接必须有效
前端所有导航链接 SHALL 指向存在的页面。

#### Scenario: 导航链接有效
- **WHEN** 用户点击导航链接
- **THEN** 页面跳转到目标 URL
- **AND** 目标页面返回 HTTP 200

## MODIFIED Requirements
无 — 本 spec 为新增验证规格。

## REMOVED Requirements
无。
