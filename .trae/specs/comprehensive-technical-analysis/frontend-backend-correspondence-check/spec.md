# 前后端功能对应关系检查 Spec

## Why
OpenClaw-Harness 项目包含 89 个后端 API 端点和 8 个前端页面，但前端与后端之间存在多处不对应问题：部分后端 API 无前端调用、部分前端界面元素缺少后端对接、数据交互格式不一致。需要全面检查前后端映射关系，确保功能完整性。

## What Changes
- **无代码修改** — 本 spec 为纯检查分析性质
- 检查范围覆盖：前端 API 调用与后端端点映射、数据格式一致性、界面元素与后端逻辑对应、缺失的前后端连接
- 输出：详细检查报告（对应/不对应/缺失记录 + 调整建议）

## Impact
- Affected code: `frontend/app/` (8 个页面) + `frontend/lib/api.ts` + `backend/app/api/` (14 个 Blueprint)
- Affected specs: 无前置 spec 依赖
- 验证环境: 静态代码分析，无需运行时环境

## ADDED Requirements

### Requirement: FE-BE-MAP 前端 API 调用与后端端点映射检查
系统 SHALL 确保前端每个页面发起的 API 请求都有对应的后端处理逻辑，且后端每个面向用户的 API 端点都有前端界面触发。

#### Scenario: 前端页面 API 调用完整性
- **WHEN** 遍历所有前端页面中的 `apiClient.get/post/put/delete/streamChat` 调用
- **THEN** 每个调用的 URL 路径都能在后端 Blueprint 路由中找到匹配
- **AND** HTTP 方法一致（前端 POST 对应后端 POST 等）

#### Scenario: 后端 API 前端覆盖度
- **WHEN** 遍历所有后端 `/api/v1` 路由
- **THEN** 识别出无任何前端页面调用的"孤岛"端点
- **AND** 按业务模块分类统计覆盖度

### Requirement: FE-BE-FORMAT 前后端数据交互格式一致性检查
系统 SHALL 确保前端期望的响应数据格式与后端实际返回格式一致。

#### Scenario: 响应体结构匹配
- **WHEN** 对比前端 TypeScript 接口定义与后端 `jsonify()` 返回结构
- **THEN** 前端接口字段名与后端 JSON 键名一致
- **AND** 数据类型兼容（如后端返回 number，前端期望 string 则标记不一致）

#### Scenario: SSE 流式事件格式匹配
- **WHEN** 对比前端 `StreamEvent.type` 枚举与后端 `_make_sse_event()` 事件类型
- **THEN** 所有后端发送的事件类型在前端都有对应处理分支
- **AND** 前端处理的类型在后端都有发送逻辑

### Requirement: FE-BE-UI 前端界面元素与后端功能对应检查
系统 SHALL 确保前端每个交互元素（按钮、表单、链接）都有对应的后端处理逻辑。

#### Scenario: 按钮功能绑定
- **WHEN** 检查前端页面中所有 `<button>` 元素的 onClick 事件
- **THEN** 每个 onClick 事件要么调用后端 API，要么执行纯前端逻辑
- **AND** 不存在"空壳按钮"（有 UI 但无功能）

#### Scenario: 导航链接有效性
- **WHEN** 检查前端页面中所有 `<Link href>` 路径
- **THEN** 每个链接路径对应一个实际存在的页面路由
- **AND** 不存在指向不存在页面的死链接

### Requirement: FE-BE-COVERAGE 功能模块前后端同步检查
系统 SHALL 按 14 个后端 Blueprint 模块逐一检查前端覆盖情况。

#### Scenario: 模块覆盖度统计
- **WHEN** 按 agents/sessions/tasks/skills/coordinator/permissions/mcp/plugins/config/tools/audit/memory/channels/sandbox 分类
- **THEN** 每个模块统计：后端端点总数、前端调用数、覆盖率百分比
- **AND** 标记覆盖率为 0% 的"盲区"模块

## MODIFIED Requirements
无 — 本 spec 为新增检查规格，不修改现有需求。

## REMOVED Requirements
无。

---

## 初步分析发现的问题摘要

### 问题 1: Dashboard 页面完全使用硬编码数据
- **文件**: `frontend/app/page.tsx`
- **问题**: Stats Cards (Active Sessions=12, Total Agents=8, Today's Cost=$2.34, Tokens Used=125K) 和 Recent Activity 全部硬编码
- **影响**: 用户看到的仪表盘数据与实际系统状态无关
- **建议**: 调用 `GET /sessions`、`GET /agents`、`GET /audit/stats` 获取真实数据

### 问题 2: Agents 页面"编辑"和"删除"按钮无功能
- **文件**: `frontend/app/agents/page.tsx` L89-91
- **问题**: "编辑"和"删除"按钮存在但无 onClick 事件绑定
- **影响**: 用户无法编辑或删除 Agent
- **建议**: 编辑按钮绑定 `PUT /agents/{id}`，删除按钮绑定 `DELETE /agents/{id}`

### 问题 3: Tools 页面数据格式不匹配
- **文件**: `frontend/app/tools/page.tsx` L24 vs `backend/app/api/tools.py` L107-110
- **问题**: 前端期望 `{ data: ToolInfo[], categories: unknown[] }`，后端返回 `{ total, categories: { [catName]: tool[] } }`
- **影响**: 工具列表可能无法正确渲染
- **建议**: 统一前后端数据格式，或在前端做适配转换

### 问题 4: Tools 页面字段名不一致
- **文件**: `frontend/app/tools/page.tsx` L12 vs `backend/app/api/tools.py` L96-98
- **问题**: 前端使用 `danger_level: 'safe' | 'caution' | 'danger'`，后端返回 `dangerous: boolean` 和 `requires_permission: boolean`
- **影响**: 危险等级标签无法正确显示
- **建议**: 后端增加 `danger_level` 字段，或前端根据 `dangerous` 布尔值映射

### 问题 5: Settings 页面多个 Tab 无 API 调用
- **文件**: `frontend/app/settings/page.tsx`
- **问题**: Providers/Permissions/MCP Tab 仅有静态 UI，未调用 `GET /config/providers`、`GET /permissions/modes`、`GET /mcp/servers`
- **影响**: 设置页的模型提供商、权限模式、MCP 服务器管理功能不可用
- **建议**: 各 Tab 加载时调用对应后端 API

### 问题 6: Dashboard 导航链接指向不存在的页面
- **文件**: `frontend/app/page.tsx` L20
- **问题**: NavLink href="/dashboard" 但实际页面路由为 `/`（page.tsx 在 app/ 根目录）
- **影响**: 点击 Dashboard 导航可能 404
- **建议**: 修改 href 为 `/`

### 问题 7: 6 个后端模块完全无前端页面
- **模块**: tasks (13 路由), plugins (8 路由), audit (6 路由), memory (9+ 路由), channels (9+ 路由), sandbox (4 路由)
- **问题**: 共计约 49 个后端 API 端点无任何前端界面
- **影响**: 这些功能只能通过 API 直接调用，普通用户无法使用
- **建议**: 优先为 tasks 和 audit 模块创建前端页面

### 问题 8: SSE StreamEvent 类型定义不完整
- **文件**: `frontend/lib/api.ts` L158-166
- **问题**: `StreamEvent.type` 枚举缺少 `'thinking'` 类型，但 `chat/page.tsx` L89 处理了该类型
- **影响**: TypeScript 类型检查可能报错
- **建议**: 在 StreamEvent 类型中添加 `'thinking'`

### 问题 9: Sessions 页面缺少操作按钮
- **文件**: `frontend/app/sessions/page.tsx`
- **问题**: 后端支持 pause/resume/delete session，但前端仅有列表展示和跳转链接
- **建议**: 添加暂停/恢复/删除操作按钮

### 问题 10: Skills 页面缺少安装和卸载功能
- **文件**: `frontend/app/skills/page.tsx`
- **问题**: 后端有 `POST /skills/install` 和 `DELETE /skills/{name}` 端点，但前端无安装/卸载 UI
- **建议**: 添加"安装技能"和"卸载"按钮
