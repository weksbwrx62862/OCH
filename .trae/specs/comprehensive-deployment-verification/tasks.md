# Tasks — OpenClaw-Harness 全面部署验证

## 阶段 1: 环境就绪与服务状态确认

- [x] **T1.1: 服务运行状态检查** ✅
  - [x] 验证后端 `/health` 返回 200 + healthy
  - [x] 验证前端 `http://localhost:3000` 返回 200
  - [x] 验证 PostgreSQL 连接正常（`pg_isready`）
  - [x] 验证 Redis 连接正常（`redis-cli ping`）

- [x] **T1.2: 认证 Token 获取** ✅
  - [x] POST `/api/v1/auth/login` 获取 admin Token
  - [x] 验证 Token 格式正确（JWT 三段式，192字符）
  - [x] 使用 Token 请求受保护端点验证有效性

## 阶段 2: 核心业务流程验证

- [x] **T2.1: Agent 完整 CRUD 链路** ✅ (9/9 通过，发现1个Bug)
  - [x] POST `/api/v1/agents` 创建 Agent → 201
  - [x] GET `/api/v1/agents` 列表 → 200
  - [x] GET `/api/v1/agents/{id}` 详情 → 200
  - [x] PUT `/api/v1/agents/{id}` 更新 → 200
  - [x] GET `/api/v1/agents/{id}/stats` 统计 → 200
  - [x] GET `/api/v1/agents/{id}/permissions` 权限 → 200
  - [x] DELETE `/api/v1/agents/{id}` 删除 → 200
  - [x] GET `/api/v1/agents/{id}` 删除后 → 404
  - [x] POST `/api/v1/agents` 同名冲突 → 422

- [x] **T2.2: Session & Chat 完整交互** ✅ (8/8 通过)
  - [x] POST `/api/v1/sessions` 创建会话 → 201
  - [x] PUT `/api/v1/sessions/{id}/pause` 暂停 → 200 (status=paused)
  - [x] PUT `/api/v1/sessions/{id}/resume` 恢复 → 200 (status=active)
  - [x] POST `/api/v1/sessions/{id}/chat` 非流式消息 → 200 + response
  - [x] GET `/api/v1/sessions/{id}/messages` 消息历史 → 200 (total=2)
  - [x] GET `/api/v1/sessions/{id}/stats` 统计 → 200
  - [x] POST `/api/v1/sessions/{id}/chat` 空消息 → 422
  - [x] DELETE `/api/v1/sessions/{id}` 删除 → 200

- [x] **T2.3: Task DAG 数据处理** ✅ (10/10 通过，修复1个Bug)
  - [x] POST `/api/v1/tasks` 单任务创建 → 201
  - [x] PUT `/api/v1/tasks/{id}/update` pending→running → 200
  - [x] PUT `/api/v1/tasks/{id}/update` running→completed → 200
  - [x] POST `/api/v1/tasks/create-with-deps` DAG 创建 → 201 + 依赖
  - [x] GET `/api/v1/tasks` 列表+筛选 → 200
  - [x] GET `/api/v1/tasks/{id}` 详情含依赖树 → 200
  - [x] PUT `/api/v1/tasks/{id}/stop` 停止任务 → 200
  - [x] DELETE `/api/v1/tasks/{id}` 删除 → 200
  - [x] GET `/api/v1/tasks/stats` 全局统计 → 200

- [x] **T2.4: Skills 技能管理** ✅ (5/5 通过)
  - [x] GET `/api/v1/skills` 列表 → 200 (4个技能)
  - [x] GET `/api/v1/skills/categories` 分类 → 200 (5个分类)
  - [x] GET `/api/v1/skills/{name}` 详情 → 200
  - [x] PUT `/api/v1/skills/{name}/enable` 启用 → 200
  - [x] PUT `/api/v1/skills/{name}/disable` 禁用 → 200

- [x] **T2.5: Coordinator 团队管理** ✅ (4/4 通过)
  - [x] GET `/api/v1/coordinator/teams` 团队列表 → 200
  - [x] POST `/api/v1/coordinator/teams` 创建团队 → 201
  - [x] GET `/api/v1/coordinator/teams/{id}` 团队详情 → 200
  - [x] GET `/api/v1/coordinator/agents` Agent 定义 → 200 (10个内置定义)

## 阶段 3: 权限与安全验证

- [x] **T3.1: 认证边界场景** ✅ (3/3 通过)
  - [x] 无 Token 请求 → 401
  - [x] 无效 Token 请求 → 401
  - [x] 伪造 Token 请求 → 401

- [x] **T3.2: 权限系统** ✅ (4/4 通过)
  - [x] GET `/api/v1/permissions/modes` 权限模式 → 200
  - [x] GET `/api/v1/permissions/rules` 规则列表 → 200
  - [x] POST `/api/v1/permissions/rules` 创建规则 → 201
  - [x] GET `/api/v1/permissions/denials` 拒绝追踪 → 200

- [x] **T3.3: 角色权限隔离** ✅ (2/2 通过)
  - [x] 使用普通用户 Token 创建 Agent → 403
  - [x] 使用 admin Token 创建 Agent → 201

## 阶段 4: 系统集成点验证

- [x] **T4.1: MCP 服务器管理** ⚠️ (4/5 通过)
  - [x] GET `/api/v1/mcp/servers` 列表 → 200
  - [x] POST `/api/v1/mcp/servers` 创建 → 201
  - [ ] GET `/api/v1/mcp/servers/{id}` 详情 → ❌ 405 (缺少GET路由)
  - [x] PUT `/api/v1/mcp/servers/{id}` 更新 → 200
  - [x] DELETE `/api/v1/mcp/servers/{id}` 删除 → 200

- [x] **T4.2: 记忆事实库** ✅ (4/4 通过)
  - [x] POST `/api/v1/memory/facts` 创建事实 → 200
  - [x] GET `/api/v1/memory/facts` 列表 → 200
  - [x] GET `/api/v1/memory/facts/{id}` 详情 → 200
  - [x] DELETE `/api/v1/memory/facts/{id}` 删除 → 200

- [x] **T4.3: 审计日志** ✅ (4/4 通过)
  - [x] GET `/api/v1/audit` 日志列表 → 200
  - [x] GET `/api/v1/audit/stats` 统计 → 200
  - [x] GET `/api/v1/audit/export` JSON 导出 → 200
  - [x] GET `/api/v1/audit/export?format=csv` CSV 导出 → 200

- [x] **T4.4: 配置与插件** ✅ (4/4 通过)
  - [x] GET `/api/v1/config` 配置 → 200
  - [x] GET `/api/v1/config/schema` Schema → 200
  - [x] GET `/api/v1/config/providers` Provider → 200
  - [x] GET `/api/v1/plugins` 插件列表 → 200

- [x] **T4.5: 工具发现** ⚠️ (2/3 通过)
  - [x] GET `/api/v1/tools` 工具列表 → 200
  - [x] GET `/api/v1/tools/categories` 分类 → 200
  - [ ] GET `/api/v1/tools/{name}` 详情 → ⚠️ 大小写敏感（bash→404, Bash→200）

- [x] **T4.6: WebSocket 连接验证** ✅ (3/3 通过)
  - [x] 建立 Socket.IO 连接 → connect 事件
  - [x] 发送 join_session 事件 → 成功
  - [x] 断开连接 → disconnect 事件

- [x] **T4.7: 前端页面渲染验证** ✅ (10/10 通过)
  - [x] 访问 `/` 首页 → 200
  - [x] 访问 `/chat` → 200
  - [x] 访问 `/agents` → 200
  - [x] 访问 `/sessions` → 200
  - [x] 访问 `/tasks` → 200
  - [x] 访问 `/skills` → 200
  - [x] 访问 `/tools` → 200
  - [x] 访问 `/swarm` → 200
  - [x] 访问 `/settings` → 200
  - [x] 访问 `/audit` → 200

## 阶段 5: 数据处理与边界场景验证

- [x] **T5.1: 数据一致性验证** ✅ (5/5 通过)
  - [x] 创建 Agent 后列表包含新记录
  - [x] 更新 Agent 后详情反映更新
  - [x] 删除 Agent 后列表不包含该记录
  - [x] 创建 Session 后统计更新
  - [x] Task DAG 依赖关系正确

- [x] **T5.2: 错误处理验证** ✅ (4/4 通过)
  - [x] 请求不存在资源 → 404
  - [x] 缺少必填字段 → 422
  - [x] 同名资源冲突 → 422
  - [x] 非法状态转换 → 422

- [x] **T5.3: 跨模块集成场景** ✅ (3/3 通过)
  - [x] 创建 Agent → 创建 Session → 发送消息 → 查看审计日志
  - [x] 创建 Task → 更新状态 → 查看审计日志记录
  - [x] 创建权限规则 → 验证权限检查生效

## 阶段 6: 验证报告生成

- [x] **T6.1: 汇总所有验证结果** ✅
  - [x] 统计通过/失败/跳过项
  - [x] 记录异常项详情（端点、请求、响应、错误）
  - [x] 评估潜在风险点
  - [x] 提出修复建议和优先级
  - [x] 记录环境信息（服务版本、运行时长）

# Task Dependencies
- T1.x → T2.x（服务就绪后才能测试业务）
- T1.2 → T2.x, T3.x, T4.x（Token 获取后才能测试受保护端点）
- T2.x → T5.x（业务验证后才能测试数据一致性和集成）
- T5.x → T6.1（所有验证完成后生成报告）
