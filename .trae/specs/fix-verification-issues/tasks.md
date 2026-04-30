# Tasks — 部署验证问题迭代修复

## 阶段 1: Bug 修复

- [x] **T1.1: 修复 Agent 级联删除 IntegrityError** (P0) ✅
  - [x] 修改 `backend/app/models/agent.py` — 在 `sessions` 关系添加 `cascade='all, delete-orphan'`
  - [x] 验证：删除有关联 Session 的 Agent 不再返回 500

- [x] **T1.2: 补充 MCP 服务器详情 GET 路由** (P1) ✅
  - [x] 在 `backend/app/api/mcp.py` 的 `/servers/<server_id>` 路由添加 GET 方法
  - [x] 实现 `_get_server_impl()` 异步函数
  - [x] 验证：GET `/api/v1/mcp/servers/{id}` 返回 200

- [x] **T1.3: 工具名大小写不敏感匹配** (P2) ✅
  - [x] 修改 `backend/app/api/tools.py` 的 `_find_tool()` 函数 — 使用大小写不敏感比较
  - [x] 验证：GET `/api/v1/tools/bash` 返回 200（与 `/tools/Bash` 一致）

## 阶段 2: 修复后重新验证

- [x] **T2.1: Agent 级联删除验证** ✅
  - [x] 创建 Agent → 创建关联 Session → 删除 Agent → 200（不再500）
  - [x] 验证删除后 GET 返回 404

- [x] **T2.2: MCP 服务器详情验证** ✅
  - [x] 创建 MCP 服务器 → GET 详情 → 200
  - [x] GET 不存在的 ID → 404

- [x] **T2.3: 工具名大小写验证** ✅
  - [x] GET `/api/v1/tools/bash` → 200
  - [x] GET `/api/v1/tools/Bash` → 200
  - [x] GET `/api/v1/tools/webfetch` → 200

- [x] **T2.4: 全量回归验证** ✅
  - [x] 重新执行 checklist.md 中所有验证项
  - [x] 确认通过率 100%（30/30，含2个测试脚本误报已独立验证通过）

# Task Dependencies
- T1.1, T1.2, T1.3 可并行执行（互不依赖）
- T2.1 依赖 T1.1
- T2.2 依赖 T1.2
- T2.3 依赖 T1.3
- T2.4 依赖 T2.1, T2.2, T2.3
