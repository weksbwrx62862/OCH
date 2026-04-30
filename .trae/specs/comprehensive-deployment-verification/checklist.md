# Checklist — OpenClaw-Harness 全面部署验证

## 阶段 1: 环境就绪与服务状态
- [x] 后端 `/health` 返回 200 + `{status: "healthy"}`
- [x] 前端 `http://localhost:3000` 返回 200
- [x] PostgreSQL 连接正常
- [x] Redis 连接正常
- [x] 认证登录成功获取有效 JWT Token

## 阶段 2: 核心业务流程

### Agent CRUD
- [x] POST /agents 创建成功 → 201
- [x] GET /agents 列表包含新建 Agent → 200
- [x] GET /agents/{id} 详情数据一致 → 200
- [x] PUT /agents/{id} 更新字段生效 → 200
- [x] GET /agents/{id}/stats 返回统计 → 200
- [x] GET /agents/{id}/permissions 返回权限 → 200
- [x] DELETE /agents/{id} 删除成功 → 200（含级联删除Session）
- [x] 删除后 GET /agents/{id} → 404
- [x] 同名创建返回 422 冲突

### Session & Chat
- [x] POST /sessions 创建成功 → 201
- [x] PUT /sessions/{id}/pause 状态变 paused → 200
- [x] PUT /sessions/{id}/resume 状态变 active → 200
- [x] POST /sessions/{id}/chat 非流式消息 → 200 + response
- [x] GET /sessions/{id}/messages 包含发送消息 → 200
- [x] GET /sessions/{id}/stats 统计准确 → 200
- [x] POST /sessions/{id}/chat 空消息 → 422
- [x] DELETE /sessions/{id} 删除成功 → 200

### Task DAG
- [x] POST /tasks 单任务创建 → 201
- [x] 任务状态流转 pending→running→completed → 200
- [x] POST /tasks/create-with-deps DAG 创建 → 201 + 依赖
- [x] GET /tasks 列表+筛选+分页 → 200
- [x] GET /tasks/{id} 详情含依赖树 → 200
- [x] PUT /tasks/{id}/stop 停止任务 → 200
- [x] DELETE /tasks/{id} 删除 → 200
- [x] GET /tasks/stats 全局统计 → 200

### Skills
- [x] GET /skills 列表返回 → 200
- [x] GET /skills/categories 分类 → 200
- [x] GET /skills/{name} 详情 → 200
- [x] PUT /skills/{name}/enable 启用 → 200
- [x] PUT /skills/{name}/disable 禁用 → 200

### Coordinator
- [x] GET /coordinator/teams 列表 → 200
- [x] POST /coordinator/teams 创建 → 201
- [x] GET /coordinator/teams/{id} 详情 → 200
- [x] GET /coordinator/agents 定义列表 → 200

## 阶段 3: 权限与安全
- [x] 无 Token 请求受保护端点 → 401
- [x] 无效 Token 请求 → 401
- [x] GET /permissions/modes → 200
- [x] GET /permissions/rules → 200
- [x] POST /permissions/rules 创建规则 → 201
- [x] GET /permissions/denials → 200
- [x] 普通用户创建 Agent → 403
- [x] Admin 创建 Agent → 201

## 阶段 4: 系统集成点

### MCP
- [x] GET /mcp/servers 列表 → 200
- [x] POST /mcp/servers 创建 → 201
- [x] GET /mcp/servers/{id} 详情 → 200（已修复）
- [x] DELETE /mcp/servers/{id} 删除 → 200

### 记忆事实库
- [x] POST /memory/facts 创建 → 200
- [x] GET /memory/facts 列表 → 200
- [x] GET /memory/facts/{id} 详情 → 200
- [x] DELETE /memory/facts/{id} 删除 → 200

### 审计
- [x] GET /audit 日志列表 → 200
- [x] GET /audit/stats 统计 → 200
- [x] GET /audit/export JSON → 200
- [x] GET /audit/export?format=csv → 200

### 配置与插件
- [x] GET /config → 200
- [x] GET /config/schema → 200
- [x] GET /config/providers → 200
- [x] GET /plugins → 200

### 工具
- [x] GET /tools → 200
- [x] GET /tools/categories → 200
- [x] GET /tools/{name} → 200（大小写不敏感，已修复）

### WebSocket
- [x] Socket.IO 连接成功建立
- [x] join_session 事件正常工作

### 前端页面
- [x] 首页 `/` → 200
- [x] `/chat` → 200
- [x] `/agents` → 200
- [x] `/sessions` → 200
- [x] `/tasks` → 200
- [x] `/skills` → 200
- [x] `/tools` → 200
- [x] `/swarm` → 200
- [x] `/settings` → 200
- [x] `/audit` → 200

## 阶段 5: 数据处理与边界场景
- [x] 创建后列表包含新记录
- [x] 更新后详情反映更新
- [x] 删除后列表不包含该记录
- [x] 请求不存在资源 → 404
- [x] 缺少必填字段 → 422
- [x] 同名冲突 → 422
- [x] 跨模块集成场景通过（Agent→Session→Chat→Audit）

## 阶段 6: 验证报告
- [x] 报告包含所有验证项结果
- [x] 报告包含异常项详情
- [x] 报告包含潜在风险评估
- [x] 报告包含修复建议
- [x] 报告包含环境信息
