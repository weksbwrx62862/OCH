# OpenClaw-Harness (OCH) 项目完成计划

> 基于 `/home/xxh/openclaw-harness` 当前代码状态分析
> 状态日期: 2026-04-07 | 已通过测试: 34/34 单元测试 + 9/9 E2E 测试

---

## 📊 项目当前状态总览

### ✅ 已完成（可生产使用）

| 模块 | 文件 | 行数 | 完成度 |
|------|------|------|--------|
| **核心框架** | main.py, config.py, database.py, security.py, exceptions.py | ~506 | **100%** |
| **Agent CRUD** | api/agents.py | 483 | **100%** — 全量 DB 操作 + 权限 + 统计 + 复制 |
| **Session + Chat** | api/sessions.py | 727 | **100%** — SSE 流式 + Agent Loop 模拟 + 消息管理 |
| **WebSocket** | api/websocket.py | 156 | **100%** — Socket.IO 事件处理 + emit 辅助函数 |
| **Tools API** | api/tools.py | 267 | **70%** — 列表/分类/搜索/测试 (部分 mock) |
| **数据模型** | models/*.py (7个) | 544 | **100%** — Agent, Session, Message, Task, Permission, Plugin, Tool |
| **服务层** | services/*.py (6个) | 1326 | **80%** — 已实现但 API 层未全部接入 |
| **OpenHarness 迁移** | openharness/ (30子模块) | ~30K | **100%** — 完整源码迁移 |
| **基础设施** | Dockerfile, docker-compose.yml, start.sh, .env.example | - | **90%** |
| **单元测试** | tests/*.py | - | **100%** — 34/34 通过 |
| **前端骨架** | layout.tsx, page.tsx, chat/page.tsx, api.ts, appStore.ts | 884 | **30%** |

### ⚠️ 骨架代码需重写为 DB 实现（8 个 API 模块）

这些文件目前使用**内存字典 (dict)** 存储数据，重启即丢失，且无法跨进程共享：

| 模块 | 文件 | 行数 | 当前存储方式 | 需改为 |
|------|------|------|-------------|---------|
| **Tasks** | api/tasks.py | 162 | `_active_tasks = {}` dict | DB: Task + TaskDependency 模型 |
| **Skills** | api/skills.py | 161 | `_skills = {}` dict | DB: Skill 模型 + 文件系统 |
| **Coordinator** | api/coordinator.py | 157 | `_teams = {}` dict | DB: Team + TeamMember 模型 |
| **Permissions** | api/permissions.py | 106 | 部分 DB + `_denied_list` | 完全 DB: PermissionRule + AuditLog |
| **MCP Servers** | api/mcp.py | 115 | `_mcp_servers = {}` dict | DB: MCPServer 模型 |
| **Plugins** | api/plugins.py | 144 | `_plugins = {}` dict | DB: Plugin 模型 |
| **Config** | api/config.py | 174 | 读 settings 无持久化 | DB: ConfigEntry 模型或 Redis |
| **Audit** | api/audit.py | 94 | `_audit_logs = []` list | DB: AuditLog 模型 |

### ❌ 前端缺失页面（导航栏已引用）

Dashboard 导航栏引用了以下页面，但均未创建：

| 路由 | 页面名称 | 优先级 | 功能描述 |
|------|----------|--------|----------|
| `/dashboard` | Dashboard | P0 | ✅ 已有 (但路径是 `/`) |
| `/chat` | 聊天 | P0 | ✅ 已有 |
| `/tools` | 工具管理 | **P1** | 工具列表/搜索/分类/权限配置 |
| `/skills` | 技能库 | **P1** | .md 技能浏览/安装/启用/禁用 |
| `/swarm` | 多智能体协作 | **P1** | 团队管理/任务分配/状态监控 |
| `/settings` | 设置 | **P2** | 配置管理/API 密钥/模型选择 |

其他缺失：
- `globals.css` — Tailwind 基础样式（文件存在但可能不完整）
- 认证/登录页面 (`(auth)` 目录存在但无内容)
- 错误页面 (404, 500)
- Agent 管理详情页

---

## 🎯 执行计划（分 Phase 推进）

### Phase 1：后端 API 数据库化改造（最高优先级）

将 8 个 Mock API 改为真实数据库操作，参考 agents.py 和 sessions.py 的成熟模式。

#### Step 1.1: Tasks API 重写
- [ ] 引入 `Task`, `TaskDependency` 模型
- [ ] 实现 `list_tasks` — 分页 + 状态筛选 + DAG 视图
- [ ] 实现 `create_task` — 支持 DAG 依赖声明
- [ ] 实现 `get_task` — 含依赖树和子任务列表
- [ ] 实现 `update_task` — 状态流转 (pending→running→completed/error)
- [ ] 实现 `delete_task` — 级联删除依赖
- [ ] 实现 `stop_task` / `list_subtasks`
- [ ] 所有路由添加 `endpoint=` 参数 + `_run_async()` 包装

#### Step 1.2: Skills API 重写
- [ ] 创建 Skill 模型（如不存在则新建）
- [ ] 实现 `list_skills` — 从 DB + 文件系统扫描
- [ ] 实现 `get_skill` / `install_skill` / `enable_skill`
- [ ] 实现 `disable_skill` / `uninstall_skill`
- [ ] 对接 `skill_service.py` 中已有的逻辑

#### Step 1.3: Coordinator (Swarm) API 重写
- [ ] 创建 Team / TeamMember 模型
- [ ] 实现 `list_teams` / `create_team` / `get_team`
- [ ] 实现 `update_team` / `dissolve_team`
- [ ] 实现 `spawn_agent` — 在团队中启动子智能体
- [ ] 实现 `list_team_agents` / `get_agent_status`
- [ ] 对接 `coordinator_service.py`

#### Step 1.4: Permissions API 增强
- [ ] 将内存 `_denied_list` 改为 DB `AuditLog` 持久化
- [ ] 实现 `list_rules` / `create_rule` / `update_rule` / `delete_rule`
- [ ] 实现 `list_denials` / `clear_denials`
- [ ] 实现 3 种模式切换: default/auto/plan
- [ ] 对接 `permission_service.py`

#### Step 1.5: MCP Servers API 重写
- [ ] 创建 MCPServer 模型
- [ ] 实现 CRUD + 连接测试
- [ ] 实现 `list_resources` / `list_tools` (发现 MCP 工具)

#### Step 1.6: Plugins API 重写
- [ ] 使用已有 Plugin 模型
- [ ] 实现 `list_plugins` / `install_plugin` / `uninstall_plugin`
- [ ] 实现 `enable_plugin` / `disable_plugin` / `get_detail`
- [ ] 对接 `plugin_service.py`

#### Step 1.7: Config API 增强
- [ ] 实现运行时配置读取/更新
- [ ] 敏感信息脱敏返回
- [ ] LLM Provider 管理 (CRUD + 连接测试)

#### Step 1.8: Audit Log API 重写
- [ ] 使用 AuditLog 模型
- [ ] 实现分页查询 + 筛选 (时间范围/用户/操作类型)
- [ ] 实现导出 (JSON/CSV)

#### Step 1.9: Tools API 完善
- [ ] 补充缺失的 DB 操作
- [ ] 工具执行历史记录
- [ ] 工具分类的 DB 持久化

#### Step 1.10: 补充测试用例
- [ ] 为每个新实现的 API 编写测试
- [ ] 目标: 总测试数 ≥ 80，覆盖率 > 70%

---

### Phase 2：前端页面补全

#### Step 2.0: 前端基础完善
- [ ] 完善 `globals.css` — Tailwind base + 自定义变量 + 暗色主题
- [ ] 创建共享组件: `NavLink`, `Sidebar`, `Header`, `Modal`, `DataTable`, `StatusBadge`
- [ ] 创建 `lib/utils.ts` — 日期格式化、截断、状态颜色映射
- [ ] 创建 `components/ui/` — Button, Input, Card, Tabs, Badge, Toast 等

#### Step 2.1: Tools 页面 (`/tools`)
```
frontend/app/tools/page.tsx
```
- [ ] 工具分类侧边栏 (Bash/Read/Write/Grep/Glob/WebFetch/Edit...)
- [ ] 工具卡片网格展示 (名称/描述/参数 schema/危险等级)
- [ ] 搜索和筛选
- [ ] 工具详情弹窗 (完整参数说明+示例)
- [ ] 权限配置面板 (allow/deny/ask per-tool)

#### Step 2.2: Skills 页面 (`/skills`)
```
frontend/app/skills/page.tsx
```
- [ ] 已安装技能列表 (卡片: 名称/来源/状态/文件数)
- [ ] 技能市场/浏览 (从 openharness/skills/ 扫描 .md 文件)
- [ ] 技能详情 (Markdown 渲染 + 元数据)
- [ ] 安装/卸载/启用/禁用操作按钮
- [ ] 技能搜索和标签过滤

#### Step 2.3: Swarm 协作页面 (`/swarm`)
```
frontend/app/swarm/page.tsx
```
- [ ] 团队列表视图 (卡片/表格切换)
- [ ] 创建团队弹窗 (选 Agent + 定义角色)
- [ ] 团队详情 (成员列表 + 任务看板)
- [ ] 子智能体状态实时更新 (WebSocket)
- [ ] 任务 DAG 可视化 (依赖关系图)

#### Step 2.4: Settings 页面 (`/settings`)
```
frontend/app/settings/page.tsx
```
- [ ] General: 模型选择/Max Tokens/Turns/超时
- [ ] Providers: API Key 管理 (Anthropic/OpenAI/自定义)
- [ ] Permissions: 全局模式切换 (default/auto/plan)
- [ ] MCP Servers: 连接配置管理
- [ ] 关于/系统信息

#### Step 2.5: Agents 管理页 (`/agents` 或 Dashboard 内嵌)
- [ ] Agent 列表 (卡片: 名称/模型/状态/会话数)
- [ ] 创建/编辑 Agent 弹窗 (含工具权限矩阵)
- [ ] Agent 详情 (统计图表 + 最近会话 + 权限表)
- [ ] Agent 复制/删除/激活/停用

#### Step 2.6: Session 列表页 (`/sessions`)
- [ ] 会话列表 (时间线/标题/Agent/状态/消息数)
- [ ] 搜索/筛选/排序
- [ ] 会话导出 (JSON/Markdown)
- [ ] 批量操作 (暂停/恢复/删除)

---

### Phase 3：深度集成与优化

#### Step 3.1: OpenHarness Engine 对接
- [ ] 将 sessions.py 中的模拟 `_generate_ai_response` 替换为真实 OpenHarness QueryEngine 调用
- [ ] 将 `_execute_tool` 替换为真实 ToolRegistry 执行
- [ ] 实现真实的 Permission 检查流程 (ask→approve/deny)
- [ ] Hook 系统 (PreToolUse/PostToolUse) 接入

#### Step 3.2: WebSocket 实时推送增强
- [ ] Session 状态变更实时推送到前端
- [ ] 工具执行进度条 (WebSocket → 前端进度组件)
- [ ] Agent 心跳和在线状态
- [ ] 系统通知 (任务完成/错误/警告)

#### Step 3.3: 认证系统完善
- [ ] 登录页面 (`/auth/login`)
- [ ] Token 自动刷新机制
- [ ] 用户注册 (可选)
- [ ] Session 管理界面 (查看/撤销活跃 Token)

#### Step 3.4: 性能与安全
- [ ] Redis 缓存集成 (替代内存 _active_sessions dict)
- [ ] Rate Limiting 中间件实现
- [ ] 输入验证加强 (SQL 注入/XSS 防护)
- [ ] CORS 策略精细化
- [ ] 敏感日志脱敏

#### Step 3.5: Docker 与部署
- [ ] frontend Dockerfile (Next.js standalone 构建)
- [ ] docker-compose.yml 完善 (健康检查/重启策略/卷挂载)
- [ ] Nginx 反向代理配置 (API + 静态文件 + WebSocket)
- [ ] 一键部署脚本优化

#### Step 3.6: 文档
- [ ] README.md 更新 (安装/配置/架构/截图)
- [ ] API 文档 (Swagger/OpenAPI 或 Markdown)
- [ ] 部署指南

---

## 📋 执行优先级矩阵

```
优先级    │ Phase 1 (后端DB化) │ Phase 2 (前端)   │ Phase 3 (集成)
──────────┼───────────────────┼────────────────┼───────────────
P0 必须  │ tasks, skills    │ globals, 共享组件│ Engine对接
P1 重要  │ coordinator,     │ tools, skills, │ WebSocket,  
          │ permissions,      │ swarm 页面     │ Auth 登录
          │ mcp, plugins                              
P2 完善  │ config, audit,   │ settings,       │ Redis缓存,
          │ tools 完善        │ agents, sessions│ 性能, Docker
```

## 🔧 技术约束与约定

1. **异步模式**: 所有 API 路由必须使用 `_run_async(coro())` + `endpoint='xxx'` 模式
2. **数据库**: 使用 `async_session_factory()` 获取 session，SQLite 兼容 (不用 `func.if_()`)
3. **认证**: `@require_auth` + `@require_role('admin')` 装饰器顺序不能反
4. **错误处理**: 统一使用 `raise OCHError(...)` → 被 main.py 异常处理器捕获
5. **前端**: Next.js 14 App Router + Tailwind CSS + Zustand + TypeScript strict
6. **命名**: 中文注释 + 英文变量/函数名
