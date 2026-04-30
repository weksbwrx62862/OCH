# Checklist — 前后端功能对应关系检查

## 阶段 1: 前端 API 调用与后端路由匹配

- [x] 前端所有 apiClient 调用已提取并记录（文件、行号、方法、URL、类型）
- [x] 后端所有 Blueprint 路由已提取并记录（模块、路径、方法、endpoint）
- [x] 前端每个 API 调用都能在后端找到匹配路由
- [x] 后端无前端调用的"孤岛"端点已识别并记录
- [x] 前端调用无后端匹配的情况已识别并记录

## 阶段 2: 数据交互格式一致性

- [x] Dashboard 页面 — 硬编码数据 vs 后端 API 对比完成
- [x] Chat 页面 — SessionInfo/Message/StreamEvent 类型与后端响应格式对比完成
- [x] Agents 页面 — Agent 接口与后端 agents.to_dict() 格式对比完成
- [x] Sessions 页面 — Session 接口与后端 sessions.to_dict() 格式对比完成
- [x] Tools 页面 — ToolInfo 接口与后端 tools 响应格式对比完成（重点：data/categories/danger_level）
- [x] Skills 页面 — Skill 接口与后端 skills 响应格式对比完成
- [x] Swarm 页面 — Team/AgentDef 接口与后端 coordinator 响应格式对比完成
- [x] Settings 页面 — Config 接口与后端 config 响应格式对比完成
- [x] SSE StreamEvent 类型定义包含所有后端实际发送的事件类型
- [x] 前端 POST/PUT 请求体字段与后端期望字段一致

## 阶段 3: 界面元素与后端功能对应

- [x] Dashboard 页面 — Stats Cards 数据来源验证（应为 API 而非硬编码）
- [x] Dashboard 页面 — Recent Activity 数据来源验证
- [x] Dashboard 页面 — Quick Actions 链接目标有效性验证
- [x] Dashboard 页面 — 导航链接（/dashboard）目标页面存在性验证
- [x] Agents 页面 — "编辑"按钮 onClick 绑定验证
- [x] Agents 页面 — "删除"按钮 onClick 绑定验证
- [x] Agents 页面 — "创建智能体"按钮 API 调用验证
- [x] Sessions 页面 — 暂停/恢复/删除操作按钮存在性验证
- [x] Skills 页面 — 安装/卸载功能 UI 存在性验证
- [x] Skills 页面 — 启用/禁用切换 API 调用验证
- [x] Swarm 页面 — 创建团队 API 调用验证
- [x] Settings 页面 — Providers Tab API 调用验证
- [x] Settings 页面 — Permissions Tab API 调用验证
- [x] Settings 页面 — MCP Tab API 调用验证
- [x] Settings 页面 — MCP "添加服务器"按钮功能验证
- [x] Chat 页面 — 创建会话 API 调用验证
- [x] Chat 页面 — 发送消息（SSE）API 调用验证

## 阶段 4: 功能模块覆盖度

- [x] agents 模块覆盖度已统计（后端 9 路由 vs 前端 2 调用 = 22%）
- [x] sessions 模块覆盖度已统计（后端 12 路由 vs 前端 3 调用 = 25%）
- [x] tasks 模块覆盖度已统计（后端 11 路由 vs 前端 0 调用 = 0%）
- [x] skills 模块覆盖度已统计（后端 8 路由 vs 前端 3 调用 = 38%）
- [x] coordinator 模块覆盖度已统计（后端 18 路由 vs 前端 3 调用 = 17%）
- [x] permissions 模块覆盖度已统计（后端 11 路由 vs 前端 0 调用 = 0%）
- [x] mcp 模块覆盖度已统计（后端 7 路由 vs 前端 0 调用 = 0%）
- [x] plugins 模块覆盖度已统计（后端 7 路由 vs 前端 0 调用 = 0%）
- [x] config 模块覆盖度已统计（后端 10 路由 vs 前端 1 调用 = 10%）
- [x] tools 模块覆盖度已统计（后端 6 路由 vs 前端 1 调用 = 17%）
- [x] audit 模块覆盖度已统计（后端 5 路由 vs 前端 0 调用 = 0%）
- [x] memory 模块覆盖度已统计（后端 9 路由 vs 前端 0 调用 = 0%）
- [x] channels 模块覆盖度已统计（后端 9 路由 vs 前端 0 调用 = 0%）
- [x] sandbox 模块覆盖度已统计（后端 4 路由 vs 前端 0 调用 = 0%）
- [x] 覆盖率为 0% 的"盲区"模块已识别（8个：tasks/permissions/mcp/plugins/audit/memory/channels/sandbox）
- [x] 各模块前端缺失影响评估完成

## 阶段 5: 检查报告

- [x] 所有问题按严重程度分类完成（关键/重要/一般/建议）
- [x] 前后端对应关系矩阵已生成
- [x] 每个问题包含：位置、描述、影响、调整建议
- [x] 调整建议按优先级排列
- [x] 报告覆盖所有 8 个前端页面和 14 个后端模块
