# OpenClaw-Harness 前后端接口差距分析明细文档

> 生成时间：2026-04-12  
> 扫描范围：`frontend/app/**/*.tsx` + `frontend/lib/**/*.ts` vs `backend/app/api/*.py`  
> 后端接口总数：108（含 2 个非蓝图端点） | 前端覆盖接口数：42 | 覆盖率：约 39%  
> 审计方法：逐行阅读后端 15 个 Blueprint 源文件 + 前端 13 个页面/组件源文件

---

## 目录

1. [严重 Bug — 前端调用了不存在的后端接口](#1-严重-bug--前端调用了不存在的后端接口)
2. [后端模块完全无前端页面](#2-后端模块完全无前端页面)
3. [已有前端页面但功能覆盖不完整](#3-已有前端页面但功能覆盖不完整)
4. [WebSocket 实时通信缺失](#4-websocket-实时通信缺失)
5. [权限模型不匹配](#5-权限模型不匹配)
6. [前端基础设施问题](#6-前端基础设施问题)
7. [修复优先级总表](#7-修复优先级总表)

---

## 1. 严重 Bug — 前端调用了不存在的后端接口

### BUG-001: AuthProvider 调用 `/auth/me` 但后端仅存在 `/auth/verify`

| 项目 | 内容 |
|------|------|
| **严重级别** | 🔴 P0 — 阻断性 Bug |
| **影响** | Token 验证始终 404，所有受保护页面会被重定向到登录页，用户无法正常使用系统 |
| **前端文件** | `frontend/app/AuthProvider.tsx` 第 23 行 |
| **后端文件** | `backend/app/api/auth.py` 第 92 行 |

**当前代码（错误）：**

```typescript
// frontend/app/AuthProvider.tsx:23
fetch('/api/v1/auth/me', {
  headers: { Authorization: `Bearer ${token}` },
})
```

**后端实际路由：**

```python
# backend/app/api/auth.py:92
@auth_bp.route('/verify', endpoint='verify', methods=['GET'])
def verify():
```

**修复方案：**

将 `AuthProvider.tsx` 第 23 行的 `/api/v1/auth/me` 改为 `/api/v1/auth/verify`：

```typescript
// 修改前
fetch('/api/v1/auth/me', {

// 修改后
fetch('/api/v1/auth/verify', {
```

注意：后端 `/verify` 返回 `{ valid: true, user: { id, username, role } }`，前端当前仅检查 HTTP 状态码，逻辑兼容。但建议同时读取响应体中的 `user` 信息更新 localStorage，避免角色信息丢失。

---

### BUG-002: 前端调用 `PUT /agents/{id}` 但该接口要求 admin 角色

| 项目 | 内容 |
|------|------|
| **严重级别** | 🔴 P1 — 非管理员用户操作必失败 |
| **影响** | 非管理员用户编辑智能体时将被后端 403 拒绝，但前端无任何角色检查或错误提示 |
| **前端文件** | `frontend/app/agents/page.tsx` 第 53 行 |
| **后端文件** | `backend/app/api/agents.py` 第 303-305 行 |

**后端代码：**

```python
# backend/app/api/agents.py:303-305
@agents_bp.route('/<agent_id>', methods=['PUT'], endpoint='update_agent')
@require_auth
@require_role('admin')
def update_agent(agent_id: str):
```

**修复方案：**

在 `agents/page.tsx` 中，编辑按钮应检查用户角色：

```typescript
const isAdmin = JSON.parse(localStorage.getItem('och_user') || '{}').role === 'admin';
// 仅管理员可编辑/删除
{isAdmin && <Button onClick={() => startEdit(agent)}>编辑</Button>}
{isAdmin && <Button onClick={() => setDeleteTarget(agent)}>删除</Button>}
```

> **同类问题**：`DELETE /agents/{id}`（第 362 行）、`POST /agents`（第 129 行）也要求 `@require_role('admin')`，需同样处理。

---

### BUG-003: 前端调用 `DELETE /coordinator/teams/{id}` 但后端执行的是"解散"而非删除

| 项目 | 内容 |
|------|------|
| **严重级别** | 🟡 P2 — 行为不一致 |
| **影响** | 前端按钮显示"解散"，但 UI 交互逻辑可能期望可恢复 |
| **前端文件** | `frontend/app/swarm/page.tsx` 第 44 行 |
| **后端文件** | `backend/app/api/coordinator.py` 第 189-209 行 |

**后端代码：**

```python
# backend/app/api/coordinator.py:204-205
team.status = 'dissolved'
team.dissolved_at = datetime.now(timezone.utc)
```

后端是软删除（状态改为 `dissolved`），而非硬删除。前端应使用 `apiClient.delete()` 调用是正确的，但需确保列表展示过滤掉 `dissolved` 状态的团队，或增加筛选参数。

---

## 2. 后端模块完全无前端页面

以下 3 个后端 Blueprint 模块没有任何对应的前端页面或 UI 入口。

### MOD-001: Channels 渠道管理模块

| 项目 | 内容 |
|------|------|
| **后端文件** | `backend/app/api/channels.py` (328 行) |
| **Blueprint** | `channels_bp` (url_prefix=`/api/v1/channels`) |
| **前端页面** | ❌ 无 |
| **Sidebar 导航** | ❌ 无入口 |
| **涉及接口数** | 9 个 |

**未覆盖接口明细：**

| # | 方法 | 路径 | 功能 | 鉴权 | 说明 |
|---|------|------|------|------|------|
| 1 | GET | `/channels/types` | 列出 IM 适配器类型 | @require_auth | 支持 11 种适配器（飞书/Slack/Telegram/企业微信/Discord/钉钉/邮件/Matrix/QQ/摩可/WhatsApp） |
| 2 | GET | `/channels/registered` | 已注册渠道列表 | @require_auth | 返回所有已注册渠道实例 |
| 3 | POST | `/channels/register` | 注册新渠道 | @require_auth | Body: `{ type, name, config, enabled }` |
| 4 | GET | `/channels/{id}` | 渠道详情 | @require_auth | 返回完整配置信息 |
| 5 | PUT | `/channels/{id}` | 更新渠道配置 | @require_auth | Body: `{ config?, enabled?, name? }` |
| 6 | DELETE | `/channels/{id}` | 注销渠道 | @require_auth | — |
| 7 | POST | `/channels/{id}/send` | 发送消息 | @require_auth | Body: `{ text, recipient? }` |
| 8 | POST | `/channels/{id}/test` | 测试渠道连接 | @require_auth | 返回连接状态 |
| 9 | GET | `/channels/stats` | 渠道聚合统计 | @require_auth | 返回总数/启用数/消息数/按类型分组 |

> **注意**：渠道列表端点是 `GET /channels/registered`（而非 `GET /channels`），注册端点是 `POST /channels/register`（而非 `POST /channels`）。数据存储在文件 `~/.och/channels.json`。

**修复方案：**

1. 新建 `frontend/app/channels/page.tsx`
2. 在 `frontend/components/layout/Sidebar.tsx` 的 `navItems` 数组中添加导航项：
   ```typescript
   { href: '/channels', label: '渠道管理', icon: <Radio className="w-4 h-4" /> },
   ```
3. 页面需实现：
   - 渠道类型选择器（调用 `GET /channels/types`）
   - 已注册渠道列表卡片（调用 `GET /channels/registered`）
   - 注册新渠道 Modal（调用 `POST /channels/register`，需选 type + 填 name + config）
   - 渠道配置编辑 Modal（调用 `PUT /channels/{id}`）
   - 测试连接按钮（调用 `POST /channels/{id}/test`）
   - 发送测试消息按钮（调用 `POST /channels/{id}/send`）
   - 删除确认（调用 `DELETE /channels/{id}`）
   - 统计面板（调用 `GET /channels/stats`）

---

### MOD-002: Sandbox 沙箱模块

| 项目 | 内容 |
|------|------|
| **后端文件** | `backend/app/api/sandbox.py` (398 行) |
| **Blueprint** | `sandbox_bp` (url_prefix=`/api/v1/sandbox`) |
| **前端页面** | ❌ 无 |
| **Sidebar 导航** | ❌ 无入口 |
| **涉及接口数** | 4 个 |

**未覆盖接口明细：**

| # | 方法 | 路径 | 功能 | 鉴权 | 说明 |
|---|------|------|------|------|------|
| 1 | GET | `/sandbox/status` | 沙箱运行时状态 | @require_auth | 返回 available/enabled/provider/runtime_path/config/host_bash_allowed |
| 2 | POST | `/sandbox/execute` | 执行命令 | @require_auth + @require_role('admin') | Body: `{ command, cwd?, timeout?, use_sandbox? }`，返回 exit_code/stdout/stderr/elapsed_ms/mode |
| 3 | POST | `/sandbox/wrap` | 命令包装预览 | @require_auth | Body: `{ command }`，返回安全包装后的命令，不实际执行 |
| 4 | POST | `/sandbox/security-check` | 安全检查 | @require_auth | Body: `{ command }`，返回 risk_level/dangerous_findings/recommendation |

> **注意**：路由是 `/sandbox/wrap` 而非 `/sandbox/wrap-preview`。`/sandbox/execute` 需要 admin 角色。

**修复方案（二选一）：**

**方案 A：独立页面**
1. 新建 `frontend/app/sandbox/page.tsx`
2. Sidebar 添加导航项
3. 页面包含：状态面板（`/sandbox/status`）、命令输入+执行（`/sandbox/execute`，需 admin）、包装预览（`/sandbox/wrap`）、安全检查（`/sandbox/security-check`）

**方案 B：集成到对话页**
1. 在 `frontend/app/chat/ChatInput.tsx` 中添加「沙箱执行」按钮
2. 在 `frontend/app/chat/MessageBubble.tsx` 中添加沙箱执行结果卡片
3. 对话页添加沙箱状态指示器

---

### MOD-003: Plugins 插件模块

| 项目 | 内容 |
|------|------|
| **后端文件** | `backend/app/api/plugins.py` (188 行) |
| **Blueprint** | `plugins_bp` (url_prefix=`/api/v1/plugins`) |
| **前端页面** | ❌ 无 |
| **Sidebar 导航** | ❌ 无入口 |
| **涉及接口数** | 7 个 |

**未覆盖接口明细：**

| # | 方法 | 路径 | 功能 | 鉴权 | 说明 |
|---|------|------|------|------|------|
| 1 | GET | `/plugins` | 已安装插件列表 | @require_auth | 含内置 + DB 自定义 |
| 2 | GET | `/plugins/available` | 可用插件市场 | @require_auth | 返回可安装插件列表 |
| 3 | POST | `/plugins/install` | 安装插件 | @require_role('admin') | Body: `{ name, version?, description?, source_type?, source? }` |
| 4 | DELETE | `/plugins/{name}` | 卸载插件 | @require_role('admin') | — |
| 5 | PUT | `/plugins/{name}/enable` | 启用插件 | @require_role('admin') | — |
| 6 | PUT | `/plugins/{name}/disable` | 禁用插件 | @require_role('admin') | — |
| 7 | GET | `/plugins/{name}/detail` | 插件详情 | @require_auth | 返回 commands/hooks/agents 列表 |

> **注意**：安装端点是 `POST /plugins/install`（而非 `/plugins/{name}/install`），详情端点是 `GET /plugins/{name}/detail`（而非 `GET /plugins/{name}`）。除列表和详情外，所有写操作均需 admin 角色。

**修复方案：**

1. 新建 `frontend/app/plugins/page.tsx`（或合并到技能库页面为子标签页）
2. Sidebar 添加导航项：
   ```typescript
   { href: '/plugins', label: '插件市场', icon: <Package className="w-4 h-4" /> },
   ```
3. 页面实现：
   - 已安装/可用两个标签页
   - 安装/卸载/启用/禁用按钮（需 admin 权限检查）
   - 插件详情 Modal（调用 `GET /plugins/{name}/detail`）

---

## 3. 已有前端页面但功能覆盖不完整

### PAGE-001: Auth 认证模块

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/login/page.tsx` (127 行) | `backend/app/api/auth.py` (163 行) |
| `frontend/app/AuthProvider.tsx` (53 行) | |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `POST /auth/login` | 无 | ✅ 直接 fetch | 正常 | `login/page.tsx:29` |
| `GET /auth/verify` | 无（自行验证 Token） | ❌ 调用了 `/auth/me` | 🔴 BUG | `AuthProvider.tsx:23` |
| `POST /auth/refresh` | 无（自行验证 Token） | ❌ 未调用 | ⚠️ 缺失 | 无 |

**修复说明：**

BUG-001 见上方。Token 自动刷新缺失修复 — 在 `AuthProvider.tsx` 或 `lib/api.ts` 中添加：

```typescript
// 在 AuthProvider.tsx 中添加
const REFRESH_INTERVAL = 12 * 60 * 60 * 1000; // 12 小时（Token 有效期 24h）

useEffect(() => {
  const interval = setInterval(async () => {
    const token = localStorage.getItem('och_token');
    if (!token) return;
    try {
      const res = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('och_token', data.access_token);
      }
    } catch {}
  }, REFRESH_INTERVAL);
  return () => clearInterval(interval);
}, []);
```

> **注意**：auth 三个端点都不在 `PUBLIC_PATHS` 中，但 auth.py 的 `verify` 和 `refresh` 自行验证 Token，不依赖 `g.user`。中间件 `PUBLIC_PATHS` 包含：`/api/v1/auth/login`, `/api/v1/auth/verify`, `/api/v1/auth/refresh`, `/api/v1/health`, `/health`。

---

### PAGE-002: Agent 智能体页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/agents/page.tsx` (233 行) | `backend/app/api/agents.py` (603 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /agents` | @require_auth | ✅ | 正常 | `agents/page.tsx:13` |
| `POST /agents/quick-create` | @require_auth | ✅ | 正常 | `agents/page.tsx:31` |
| `PUT /agents/{id}` | @require_auth + @require_role('admin') | ⚠️ 无角色检查 | P1 | `agents/page.tsx:53` |
| `DELETE /agents/{id}` | @require_auth + @require_role('admin') | ⚠️ 无角色检查 | P1 | `agents/page.tsx:68` |
| `POST /agents` (admin 创建) | @require_auth + @require_role('admin') | ❌ | ⚠️ 缺失 | 无高级创建 |
| `GET /agents/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情页 |
| `POST /agents/{id}/duplicate` | @require_auth | ❌ | ⚠️ 缺失 | 无复制按钮 |
| `GET /agents/{id}/stats` | @require_auth | ❌ | ⚠️ 缺失 | 无统计展示 |
| `GET /agents/{id}/permissions` | @require_auth | ❌ | ⚠️ 缺失 | 无权限查看 |
| `PUT /agents/{id}/permissions` | @require_auth + @require_role('admin') | ❌ | ⚠️ 缺失 | 无权限编辑 |

**缺失功能修复：**

1. **角色检查** — 在编辑/删除按钮上加 `isAdmin` 守卫（见 BUG-002）
2. **复制智能体** — 在卡片操作区添加「复制」按钮：
   ```typescript
   <Button variant="ghost" size="sm" icon={<Copy />}
     onClick={async () => {
       await apiClient.post(`/agents/${agent.id}/duplicate`);
       refetch();
     }}>复制</Button>
   ```
3. **智能体统计** — 在页面顶部调用 `GET /agents/stats`
4. **权限管理** — 新增权限子页面或标签页

---

### PAGE-003: Session 会话页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/sessions/page.tsx` (153 行) | `backend/app/api/sessions.py` (899 行) |
| `frontend/app/chat/page.tsx` (321 行) | |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /sessions` | @require_auth | ✅ | 正常 | `sessions/page.tsx:14` |
| `POST /sessions` | @require_auth | ✅ | 正常 | `chat/page.tsx:103` |
| `GET /sessions/{id}` | @require_auth | ✅ | 正常 | `chat/page.tsx:115` |
| `GET /sessions/{id}/messages` | @require_auth | ✅ | 正常 | `chat/page.tsx:117` |
| `DELETE /sessions/{id}` | @require_auth | ✅ | 正常 | `sessions/page.tsx:40` |
| `PUT /sessions/{id}/pause` | @require_auth | ✅ | 正常 | `sessions/page.tsx:23` |
| `PUT /sessions/{id}/resume` | @require_auth | ✅ | 正常 | `sessions/page.tsx:32` |
| `POST /sessions/{id}/chat` | @require_auth | ✅ SSE | 正常 | `chat/page.tsx:139` (via proxy) |
| `GET /sessions/{id}/stats` | @require_auth | ❌ | ⚠️ 缺失 | — |
| `GET /sessions/compact-cache` | @require_auth | ❌ | ⚠️ 缺失 | — |
| `GET /sessions/compact-cache/{tool_id}` | @require_auth | ❌ | ⚠️ 缺失 | — |
| `POST /sessions/compact-cache/clear-expired` | @require_auth | ❌ | ⚠️ 缺失 | — |

> **注意**：compact-cache 的全局统计端点是 `GET /sessions/compact-cache`（不带 session_id），查找是 `GET /sessions/compact-cache/{tool_id}`（参数是 tool_id 而非 session_id），清理是 `POST /sessions/compact-cache/clear-expired`。会话统计是 `GET /sessions/{id}/stats`（需指定 session_id，非全局统计）。

**缺失功能修复：**

1. **会话统计** — 在会话详情区域调用 `GET /sessions/{id}/stats`
2. **Compact Cache 管理** — 在会话页添加缓存管理区域

---

### PAGE-004: Task 任务页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/tasks/page.tsx` (132 行) | `backend/app/api/tasks.py` (563 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /tasks` | @require_auth | ✅ | 正常 | `tasks/page.tsx:20` |
| `PUT /tasks/{id}/stop` | @require_auth | ✅ | 正常 | `tasks/page.tsx:28` |
| `DELETE /tasks/{id}` | @require_auth | ✅ | 正常 | `tasks/page.tsx:29` |
| `POST /tasks` | @require_auth | ❌ | 🔴 缺失 | 无创建按钮 |
| `POST /tasks/create-with-deps` | @require_auth | ❌ | ⚠️ 缺失 | 无 DAG 创建 |
| `GET /tasks/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情页 |
| `GET /tasks/{id}/output` | @require_auth | ❌ | ⚠️ 缺失 | 无输出查看 |
| `PUT /tasks/{id}/update` | @require_auth | ❌ | ⚠️ 缺失 | 无手动状态更新 |
| `GET /tasks/{id}/deps` | @require_auth | ❌ | ⚠️ 缺失 | 无依赖展示 |
| `POST /tasks/{id}/deps` | @require_auth | ❌ | ⚠️ 缺失 | 无添加依赖 |
| `GET /tasks/stats` | @require_auth | ❌ | ⚠️ 缺失 | 无统计 |

> **注意**：DAG 创建端点是 `POST /tasks/create-with-deps`（而非 `/tasks/with-deps`）。状态更新端点是 `PUT /tasks/{id}/update`（而非 `/tasks/{id}/status`）。依赖操作有 `GET /tasks/{id}/deps` 和 `POST /tasks/{id}/deps` 两个。

**缺失功能修复：**

1. **创建任务** — 在页面顶部添加「创建任务」按钮和 Modal：
   ```typescript
   <Button icon={<Plus />} onClick={() => setShowCreate(true)}>创建任务</Button>
   // Modal 中提交
   await apiClient.post('/tasks', { command, task_type, timeout? });
   ```

2. **DAG 任务创建** — 添加「创建任务链」按钮：
   ```typescript
   await apiClient.post('/tasks/create-with-deps', {
     session_id, tasks: [{ type, command, deps: [] }, ...]
   });
   ```

3. **任务输出查看** — 点击任务卡片展开输出：
   ```typescript
   const res = await apiClient.get(`/tasks/${task.id}/output`);
   ```

4. **任务统计** — 调用 `GET /tasks/stats`

---

### PAGE-005: Tools 工具库页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/tools/page.tsx` (139 行) | `backend/app/api/tools.py` (342 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /tools` | @require_auth | ✅ | 正常 | `tools/page.tsx:50` |
| `GET /tools/categories` | @require_auth | ✅ | 正常 | `tools/page.tsx:51` |
| `GET /tools/{name}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情页 |
| `GET /tools/{name}/schema` | @require_auth | ❌ | ⚠️ 缺失 | 无 Schema 查看 |
| `GET /tools/{name}/examples` | @require_auth | ❌ | ⚠️ 缺失 | 无示例展示 |
| `POST /tools/{name}/test` | @require_auth | ❌ | 🔴 缺失 | 无测试按钮 |

**缺失功能修复：**

1. **工具测试按钮** — 在工具卡片中添加「测试」按钮：
   ```typescript
   const testTool = async (name: string) => {
     const schema = await apiClient.get(`/tools/${name}/schema`);
     // 弹出参数输入 Modal，收集参数后
     const result = await apiClient.post(`/tools/${name}/test`, { input: inputParams });
   };
   ```

2. **工具详情页** — 点击卡片弹出详情 Modal，展示完整描述、参数 Schema、使用示例

---

### PAGE-006: Skills 技能库页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/skills/page.tsx` (147 行) | `backend/app/api/skills.py` (399 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /skills` | @require_auth | ✅ | 正常 | `skills/page.tsx:30` |
| `PUT /skills/{name}/enable` | @require_auth | ✅ | 正常 | `skills/page.tsx:46` |
| `PUT /skills/{name}/disable` | @require_auth | ✅ | 正常 | `skills/page.tsx:46` |
| `POST /skills/install` | @require_auth | ✅ | 正常 | `skills/page.tsx:53` |
| `DELETE /skills/{name}` | @require_auth | ✅ | 正常 | `skills/page.tsx:63` |
| `POST /skills/scan` | @require_auth | ✅ | 正常 | `skills/page.tsx:71` |
| `GET /skills/categories` | @require_auth | ❌ | ⚠️ 缺失 | 未使用分类筛选 |
| `GET /skills/{name}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情页 |

> **注意**：后端 `GET /skills` 的返回中已包含 `categories` 统计信息，但前端没有使用分类筛选。独立的 `GET /skills/categories` 端点返回更详细的分类统计。

**缺失功能修复：**

1. **分类筛选** — 调用 `GET /skills/categories` 获取分类列表，增加按分类筛选
2. **技能详情** — 点击技能卡片弹出详情 Modal

---

### PAGE-007: Swarm 协作页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/swarm/page.tsx` (138 行) | `backend/app/api/coordinator.py` (684 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /coordinator/teams` | @require_auth | ✅ | 正常 | `swarm/page.tsx:17` |
| `POST /coordinator/teams` | @require_auth | ✅ | 正常 | `swarm/page.tsx:33` |
| `DELETE /coordinator/teams/{id}` | @require_auth | ✅ 正常（软删除） | 正常 | `swarm/page.tsx:44` |
| `GET /coordinator/agents` | @require_auth | ✅ | 正常 | `swarm/page.tsx:18` |
| `GET /coordinator/tasks` | @require_auth | ✅ | 正常 | `swarm/page.tsx:19` |
| `GET /coordinator/teams/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无团队详情 |
| `PUT /coordinator/teams/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无团队编辑 |
| `GET /coordinator/agents/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无定义详情 |
| `POST /coordinator/spawn` | @require_auth | ❌ | 🔴 缺失 | 无子智能体生成 |
| `GET /coordinator/workers` | @require_auth | ❌ | 🔴 缺失 | 无 Worker 列表 |
| `POST /coordinator/workers` | @require_auth | ❌ | 🔴 缺失 | 无 Worker 生成 |
| `POST /coordinator/workers/{id}/stop` | @require_auth | ❌ | 🔴 缺失 | 无 Worker 停止 |
| `GET /coordinator/workers/stats` | @require_auth | ❌ | ⚠️ 缺失 | 无 Worker 统计 |
| `GET /coordinator/subagents` | @require_auth | ❌ | 🔴 缺失 | 无子代理任务列表 |
| `POST /coordinator/subagents` | @require_auth | ❌ | 🔴 缺失 | 无子代理任务提交 |
| `GET /coordinator/subagents/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无子代理任务查看 |
| `POST /coordinator/subagents/{id}/cancel` | @require_auth | ❌ | ⚠️ 缺失 | 无子代理任务取消 |
| `GET /coordinator/subagents/stats` | @require_auth | ❌ | ⚠️ 缺失 | 无子代理统计 |

> **注意**：子代理提交端点是 `POST /coordinator/subagents`（而非 `/coordinator/subagents/tasks`），详情是 `GET /coordinator/subagents/{id}`（task_id），取消是 `POST /coordinator/subagents/{id}/cancel`。Worker 停止是 `POST /coordinator/workers/{id}/stop`（而非 DELETE）。

**缺失功能修复：**

1. **Worker 管理** — 在团队详情中增加 Worker 区域
2. **子智能体生成** — 在智能体卡片上添加「生成」按钮
3. **子代理任务管理** — 在页面底部添加任务列表区域
4. **团队详情/编辑** — 点击团队卡片进入详情页

---

### PAGE-008: Settings 设置页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/settings/page.tsx` (236 行) | `backend/app/api/config.py` (257 行) |
| | `backend/app/api/permissions.py` (633 行) |
| | `backend/app/api/mcp.py` (298 行) |

**覆盖情况 — Config 配置：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /config` | @require_auth | ✅ | 正常 | `settings/page.tsx:30` |
| `PUT /config` | @require_role('admin') | ❌ | 🔴 缺失 | 配置只读无法保存 |
| `POST /config/reset` | @require_role('admin') | ❌ | ⚠️ 缺失 | 无重置按钮 |
| `GET /config/schema` | @require_auth | ❌ | ⚠️ 缺失 | 无 Schema 展示 |
| `GET /config/validation` | @require_auth | ❌ | ⚠️ 缺失 | 无验证状态 |

> **注意**：`GET /config/validation` 是 GET 方法（不是 POST），返回 `{ valid, errors, warnings }`。

**覆盖情况 — Providers 提供商：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /config/providers` | @require_auth | ✅ | 正常 | `settings/page.tsx:32` |
| `POST /config/providers` | @require_role('admin') | ❌ | ⚠️ 缺失 | 无添加提供商 |
| `PUT /config/providers/{id}` | @require_role('admin') | ❌ | ⚠️ 缺失 | 无编辑提供商 |
| `DELETE /config/providers/{id}` | @require_role('admin') | ❌ | ⚠️ 缺失 | 无删除提供商 |
| `POST /config/providers/{id}/test` | @require_auth | ❌ | 🔴 缺失 | 无测试连接按钮 |

**覆盖情况 — Permissions 权限：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /permissions/modes` | @require_auth | ✅ | 正常 | `settings/page.tsx:54` |
| `PUT /permissions/modes/{id}` | @require_role('admin') | ✅ | 正常 | `settings/page.tsx:63` |
| `GET /permissions/rules` | @require_auth | ❌ | 🔴 缺失 | 无规则列表 |
| `POST /permissions/rules` | @require_auth | ❌ | 🔴 缺失 | 无创建规则 |
| `PUT /permissions/rules/{id}` | @require_auth | ❌ | 🔴 缺失 | 无编辑规则 |
| `DELETE /permissions/rules/{id}` | @require_auth | ❌ | 🔴 缺失 | 无删除规则 |
| `GET /permissions/denials` | @require_auth | ❌ | ⚠️ 缺失 | 无拒绝记录 |
| `GET /permissions/denials/stats` | @require_auth | ❌ | ⚠️ 缺失 | 无拒绝统计 |
| `POST /permissions/denials/clear` | @require_role('admin') | ❌ | ⚠️ 缺失 | 无清理拒绝 |
| `GET /permissions/denials/tracker` | @require_auth | ❌ | ⚠️ 缺失 | 无追踪器状态 |
| `POST /permissions/denials/tracker/clear` | @require_auth | ❌ | ⚠️ 缺失 | 无清理追踪 |
| `POST /permissions/check` | @require_auth | ❌ | ⚠️ 缺失 | 无权限检查 |

> **注意**：`PUT /permissions/modes/{id}` 需要 admin 角色，前端没有做角色检查。`POST /permissions/denials/clear` 也需要 admin 角色。

**覆盖情况 — MCP 服务：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /mcp/servers` | @require_auth | ✅ | 正常 | `settings/page.tsx:33` |
| `POST /mcp/servers` | @require_role('admin') | ✅ | 正常 | `settings/page.tsx:72` |
| `DELETE /mcp/servers/{id}` | @require_role('admin') | ✅ | 正常 | `settings/page.tsx:81` |
| `GET /mcp/servers/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情 |
| `PUT /mcp/servers/{id}` | @require_role('admin') | ❌ | 🔴 缺失 | 无编辑 MCP |
| `GET /mcp/servers/{id}/tools` | @require_auth | ❌ | ⚠️ 缺失 | 无工具列表 |
| `GET /mcp/servers/{id}/resources` | @require_auth | ❌ | ⚠️ 缺失 | 无资源列表 |
| `POST /mcp/servers/{id}/test` | @require_auth | ❌ | 🔴 缺失 | 无测试连接 |

**缺失功能修复：**

1. **配置保存** — 通用标签页改为可编辑表单 + 保存/重置按钮
2. **配置验证状态** — 在页面顶部显示 `GET /config/validation` 结果
3. **权限规则管理** — 权限标签页增加规则 CRUD 区域
4. **MCP 编辑/测试** — MCP 服务器卡片增加编辑和测试按钮
5. **提供商测试** — 提供商卡片增加测试连接按钮

---

### PAGE-009: Audit 审计页面

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/audit/page.tsx` (145 行) | `backend/app/api/audit.py` (227 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /audit` | @require_auth | ✅ | 正常 | `audit/page.tsx:28` |
| `GET /audit/stats` | @require_auth | ✅ | 正常 | `audit/page.tsx:29` |
| `POST /audit/purge` | @require_role('admin') | ✅ | 正常 | `audit/page.tsx:37` |
| `GET /audit/export` | @require_role('admin') | ⚠️ 部分 | 硬编码 CSV | `audit/page.tsx:44` |
| `GET /audit/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情查看 |

**问题说明：**

- `handleExport` 使用直接 `fetch()` 而非 `apiClient`（第 44 行），因为需要下载二进制文件
- 导出格式硬编码为 CSV，后端支持 `format=json` 参数
- `POST /audit/purge` 需要 admin 角色，前端无角色检查
- `GET /audit/export` 也需要 admin 角色

**缺失功能修复：**

1. **导出格式选择** — 修改 `handleExport` 支持 format 参数：
   ```typescript
   const handleExport = async (format: 'csv' | 'json' = 'csv') => {
     const response = await fetch(`/api/v1/audit/export?format=${format}`, {
       headers: { 'Authorization': `Bearer ${token}` },
     });
     a.download = `audit_export.${format}`;
   };
   ```

2. **审计详情** — 点击日志条目展开详情

---

### PAGE-010: Memory 记忆模块

| 前端文件 | 后端文件 |
|----------|----------|
| `frontend/app/chat/MemorySidebar.tsx` (41 行) | `backend/app/api/memory.py` (746 行) |

**覆盖情况：**

| 后端接口 | 鉴权 | 前端调用 | 状态 | 位置 |
|----------|------|----------|------|------|
| `GET /memory/facts` | @require_auth | ✅ | 只读列表 | `chat/page.tsx:71` |
| `POST /memory/facts` | @require_auth | ❌ | 🔴 缺失 | 无创建按钮 |
| `GET /memory/facts/{id}` | @require_auth | ❌ | ⚠️ 缺失 | 无详情 |
| `PUT /memory/facts/{id}` | @require_auth | ❌ | 🔴 缺失 | 无编辑 |
| `DELETE /memory/facts/{id}` | @require_auth | ❌ | 🔴 缺失 | 无删除（软删除） |
| `GET /memory/stats` | @require_auth | ❌ | ⚠️ 缺失 | 无统计 |
| `POST /memory/recall` | @require_auth | ❌ | 🔴 缺失 | 无语义搜索 |
| `POST /memory/signal/correction` | @require_auth | ❌ | ⚠️ 缺失 | 无纠正信号 |
| `POST /memory/signal/reinforcement` | @require_auth | ❌ | ⚠️ 缺失 | 无强化信号 |
| `POST /memory/msa/init` | @require_auth | ❌ | ⚠️ 缺失 | 无 MSA 初始化 |
| `POST /memory/msa/recall` | @require_auth | ❌ | ⚠️ 缺失 | 无 MSA 回忆 |
| `GET /memory/msa/status` | @require_auth | ❌ | ⚠️ 缺失 | 无 MSA 状态 |
| `POST /memory/msa/encode` | @require_auth | ❌ | ⚠️ 缺失 | 无 MSA 编码 |
| `DELETE /memory/msa/shutdown` | @require_auth | ❌ | ⚠️ 缺失 | 无 MSA 关闭 |

> **注意**：MSA 关闭端点是 `DELETE /memory/msa/shutdown`（而非 POST）。

**缺失功能修复：**

1. **记忆 CRUD** — 将 `MemorySidebar` 升级为可交互组件
2. **语义搜索** — 在侧边栏顶部添加搜索框，调用 `POST /memory/recall`
3. **新建独立记忆管理页** — 建议新增 `/memory` 路由，Sidebar 添加导航项

---

## 4. WebSocket 实时通信缺失

| 项目 | 内容 |
|------|------|
| **后端文件** | `backend/app/api/websocket.py` (163 行) |
| **前端集成** | ❌ 完全未集成 Socket.IO 客户端 |
| **前端依赖** | `socket.io-client@^4.7.0` 已安装但零引用 |
| **Next.js 代理** | `next.config.js` 已配置 `/socket.io/:path*` 重写规则 |

**后端定义的实时事件（服务端 emit）：**

| 事件名 | 功能 | 触发场景 | 前端使用 |
|--------|------|----------|----------|
| `session_event` | 会话状态变更 | 会话暂停/恢复/完成 | ❌ |
| `tool_progress` | 工具执行进度 | 工具开始/结束执行 | ❌ |
| `system_notification` | 系统通知推送 | 系统级事件 | ❌ |
| `agent_status` | 智能体状态变化 | 智能体启动/停止 | ❌ |

**后端 Socket.IO 客户端事件处理：**

| 事件名 | 功能 | 数据 |
|--------|------|------|
| `connect` | 连接（需 JWT 认证） | query param `token` 或 Authorization header |
| `disconnect` | 断开 | — |
| `join_session` | 加入会话房间 | `{ session_id }` |
| `leave_session` | 离开会话房间 | `{ session_id }` |
| `ping` | 心跳 | — |

**修复方案：**

1. 新建 `frontend/lib/socket.ts`（`socket.io-client` 已安装）：
   ```typescript
   import { io, Socket } from 'socket.io-client';
   
   let socket: Socket | null = null;
   
   export function getSocket(): Socket {
     if (!socket) {
       const token = localStorage.getItem('och_token');
       socket = io({
         path: '/socket.io',
         auth: { token },
         transports: ['websocket', 'polling'],
       });
     }
     return socket;
   }
   ```

2. 在 `ChatPage` 中集成实时更新：
   ```typescript
   useEffect(() => {
     const sock = getSocket();
     sock.emit('join_session', { session_id: sessionId });
     
     sock.on('tool_progress', (data) => {
       setActiveToolCalls(prev => updateToolCall(prev, data));
     });
     
     sock.on('session_event', (data) => {
       // 更新会话状态
     });
     
     return () => {
       sock.emit('leave_session', { session_id: sessionId });
       sock.off('tool_progress');
       sock.off('session_event');
     };
   }, [sessionId]);
   ```

3. 在 `appStore.ts` 中添加系统通知处理

---

## 5. 权限模型不匹配

后端大量接口使用 `@require_role('admin')` 装饰器限制操作，但前端几乎没有角色检查。以下是所有需要 admin 角色的接口及前端现状：

| 模块 | 接口 | 前端角色检查 |
|------|------|-------------|
| agents | `POST /agents` (admin 创建) | ❌ 无此功能 |
| agents | `PUT /agents/{id}` | ❌ 无检查 |
| agents | `DELETE /agents/{id}` | ❌ 无检查 |
| agents | `PUT /agents/{id}/permissions` | ❌ 无此功能 |
| config | `PUT /config` | ❌ 无此功能 |
| config | `POST /config/reset` | ❌ 无此功能 |
| config | `POST /config/providers` | ❌ 无此功能 |
| config | `PUT /config/providers/{id}` | ❌ 无此功能 |
| config | `DELETE /config/providers/{id}` | ❌ 无此功能 |
| permissions | `PUT /permissions/modes/{id}` | ❌ 无检查 |
| permissions | `POST /permissions/denials/clear` | ❌ 无此功能 |
| mcp | `POST /mcp/servers` | ⚠️ settings 页面有 `isAdmin` 检查 |
| mcp | `PUT /mcp/servers/{id}` | ❌ 无此功能 |
| mcp | `DELETE /mcp/servers/{id}` | ⚠️ settings 页面有 `isAdmin` 检查 |
| sandbox | `POST /sandbox/execute` | ❌ 无此页面 |
| plugins | `POST /plugins/install` | ❌ 无此页面 |
| plugins | `DELETE /plugins/{name}` | ❌ 无此页面 |
| plugins | `PUT /plugins/{name}/enable` | ❌ 无此页面 |
| plugins | `PUT /plugins/{name}/disable` | ❌ 无此页面 |
| audit | `GET /audit/export` | ❌ 无检查 |
| audit | `POST /audit/purge` | ❌ 无检查 |

**修复方案：**

1. 在 `lib/api.ts` 的 403 处理中增加角色提示：
   ```typescript
   if (response.status === 403) {
     throw new Error('权限不足：此操作需要管理员权限');
   }
   ```

2. 在需要 admin 权限的按钮上统一添加守卫：
   ```typescript
   const isAdmin = JSON.parse(localStorage.getItem('och_user') || '{}').role === 'admin';
   {isAdmin && <Button>...</Button>}
   ```

3. 建议 `appStore.ts` 中存储 `isAdmin` 计算属性，全局可用

---

## 6. 前端基础设施问题

### 6.1 直接 fetch() 调用绕过 apiClient

以下 3 处使用直接 `fetch()` 而非 `apiClient`，导致缺少统一的 Token 注入、401 处理和重试逻辑：

| 文件 | 行号 | URL | 原因 |
|------|------|-----|------|
| `AuthProvider.tsx` | 23 | `/api/v1/auth/me` | 登录前无 Token，需独立逻辑 |
| `login/page.tsx` | 29 | `/api/v1/auth/login` | 登录前无 Token |
| `audit/page.tsx` | 44 | `/api/v1/audit/export` | 需下载二进制文件 |

**修复建议**：AuthProvider 和 login 的直接 fetch 合理（无 Token 场景），但 audit 导出应在 apiClient 中增加 `download()` 方法以统一鉴权。

### 6.2 仪表盘硬编码统计数据

`frontend/app/page.tsx` 第 74-75 行：

```typescript
todayCost: '-',
tokensUsed: '-',
```

后端没有全局统计接口（如 `GET /stats` 或 `GET /dashboard`），仪表盘无法展示费用和 Token 用量。

**修复方案**：新增后端聚合统计端点，或在仪表盘页面分别调用 `GET /sessions/stats`（不存在）、`GET /agents/stats`（不存在）等接口组合数据。

### 6.3 环境变量

前端使用以下环境变量，但无 `.env*` 文件：

| 变量 | 位置 | 默认值 | 用途 |
|------|------|--------|------|
| `BACKEND_URL` | `next.config.js:1`, `api.ts:9`, `proxy/chat/route.ts:3` | `http://localhost:8008` | 服务端后端地址 |
| `NEXT_PUBLIC_API_URL` | `api.ts:12` | `/api/v1` | 客户端 API 基础路径 |

### 6.4 API 代理路由

仅 1 个 Next.js API Route：

| 文件 | 功能 |
|------|------|
| `frontend/app/api/proxy/chat/route.ts` (55 行) | SSE 流式聊天代理，转发到 `BACKEND_URL/api/v1/sessions/{sid}/chat` |

其他所有 API 请求通过 `next.config.js` 的 rewrite 规则直接代理到后端。

---

## 7. 修复优先级总表

| 优先级 | 编号 | 问题 | 涉及文件 | 工作量 | 说明 |
|--------|------|------|----------|--------|------|
| 🔴 P0 | BUG-001 | AuthProvider 路由错误 | `AuthProvider.tsx:23` | 1 行 | `/auth/me` → `/auth/verify` |
| 🔴 P1 | BUG-002 | Agent 编辑/删除无角色检查 | `agents/page.tsx:53,68` | 小 | 添加 `isAdmin` 守卫 |
| 🔴 P1 | PAGE-004 | 任务创建缺失 | `tasks/page.tsx` | 小 | 添加创建按钮和 Modal |
| 🔴 P1 | PAGE-008 | 配置无法保存 | `settings/page.tsx` | 中 | 通用标签改为可编辑表单+保存 |
| 🔴 P1 | PAGE-008 | 权限规则管理缺失 | `settings/page.tsx` | 中 | 增加规则 CRUD 区域 |
| 🔴 P1 | PAGE-005 | 工具测试按钮缺失 | `tools/page.tsx` | 小 | 添加测试按钮+参数输入 |
| 🔴 P1 | MOD-001 | Channels 模块无页面 | 新建 `channels/page.tsx` | 中 | 新建渠道管理页（9 个接口） |
| 🔴 P1 | SEC-001 | admin 接口无前端角色检查 | 多个页面 | 小 | 统一添加 `isAdmin` 守卫 |
| 🟡 P2 | MOD-002 | Sandbox 模块无页面 | 新建 `sandbox/page.tsx` | 中 | 新建沙箱管理页（4 个接口） |
| 🟡 P2 | MOD-003 | Plugins 模块无页面 | 新建 `plugins/page.tsx` | 中 | 新建插件市场页（7 个接口） |
| 🟡 P2 | PAGE-010 | Memory 仅只读 | `MemorySidebar.tsx` | 大 | 升级为完整管理页（14 个接口） |
| 🟡 P2 | PAGE-007 | Swarm Worker/Subagent 管理 | `swarm/page.tsx` | 中 | 增加 Worker/子代理管理（13 个接口） |
| 🟡 P2 | PAGE-002 | Agent 权限/复制/统计 | `agents/page.tsx` | 中 | 增加权限/复制/统计功能 |
| 🟡 P2 | PAGE-008 | MCP 编辑/测试缺失 | `settings/page.tsx` | 中 | MCP 卡片增加编辑和测试按钮 |
| 🟡 P2 | SEC-002 | WebSocket 未集成 | 新建 `lib/socket.ts` | 大 | 集成 Socket.IO 客户端 |
| 🟡 P2 | PAGE-008 | 提供商测试/删除缺失 | `settings/page.tsx` | 小 | 提供商卡片增加操作按钮 |
| 🟡 P2 | PAGE-008 | 配置验证状态缺失 | `settings/page.tsx` | 小 | 调用 `GET /config/validation` |
| 🟢 P3 | PAGE-003 | Session 统计/缓存管理 | `sessions/page.tsx` | 中 | 增加后端统计和缓存管理 |
| 🟢 P3 | PAGE-009 | Audit 导出格式/详情 | `audit/page.tsx` | 小 | 格式选择+详情查看+角色检查 |
| 🟢 P3 | PAGE-006 | Skills 分类/详情 | `skills/page.tsx` | 小 | 分类筛选+详情 Modal |
| 🟢 P3 | PAGE-001 | Token 自动刷新 | `AuthProvider.tsx` | 小 | 定时调用 `/auth/refresh` |
| 🟢 P3 | INFRA-001 | 仪表盘硬编码统计 | `page.tsx:74-75` | 中 | 新增后端聚合统计端点 |
| 🟢 P3 | INFRA-002 | audit 导出绕过 apiClient | `audit/page.tsx:44` | 小 | apiClient 增加 download 方法 |

---

**总计：** 2 个 Bug（1 阻断性 + 1 权限缺失） + 3 个完全缺失的后端模块（20 个接口） + 约 66 个未覆盖的后端接口 + WebSocket 实时通信完全缺失 + 19 个需 admin 角色的接口无前端权限检查 + 2 个基础设施问题。

---

## 附录：后端接口完整清单

### Auth (`/api/v1/auth`) — 3 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | POST | `/auth/login` | 无 | 31 |
| 2 | GET | `/auth/verify` | 自行验证 | 92 |
| 3 | POST | `/auth/refresh` | 自行验证 | 127 |

### Agents (`/api/v1/agents`) — 10 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/agents` | @require_auth | 23 |
| 2 | POST | `/agents` | @require_auth + @require_role('admin') | 129 |
| 3 | POST | `/agents/quick-create` | @require_auth | 246 |
| 4 | GET | `/agents/{id}` | @require_auth | 278 |
| 5 | PUT | `/agents/{id}` | @require_auth + @require_role('admin') | 303 |
| 6 | DELETE | `/agents/{id}` | @require_auth + @require_role('admin') | 362 |
| 7 | POST | `/agents/{id}/duplicate` | @require_auth | 392 |
| 8 | GET | `/agents/{id}/stats` | @require_auth | 469 |
| 9 | GET | `/agents/{id}/permissions` | @require_auth | 518 |
| 10 | PUT | `/agents/{id}/permissions` | @require_auth + @require_role('admin') | 550 |

### Sessions (`/api/v1/sessions`) — 12 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/sessions` | @require_auth | 67 |
| 2 | POST | `/sessions` | @require_auth | 144 |
| 3 | GET | `/sessions/{id}` | @require_auth | 243 |
| 4 | DELETE | `/sessions/{id}` | @require_auth | 274 |
| 5 | PUT | `/sessions/{id}/pause` | @require_auth | 301 |
| 6 | PUT | `/sessions/{id}/resume` | @require_auth | 325 |
| 7 | POST | `/sessions/{id}/chat` | @require_auth | 354 |
| 8 | GET | `/sessions/{id}/messages` | @require_auth | 638 |
| 9 | GET | `/sessions/{id}/stats` | @require_auth | 673 |
| 10 | GET | `/sessions/compact-cache` | @require_auth | 840 |
| 11 | GET | `/sessions/compact-cache/{tool_id}` | @require_auth | 858 |
| 12 | POST | `/sessions/compact-cache/clear-expired` | @require_auth | 886 |

### Tools (`/api/v1/tools`) — 6 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/tools` | @require_auth | 74 |
| 2 | GET | `/tools/categories` | @require_auth | 135 |
| 3 | GET | `/tools/{name}` | @require_auth | 153 |
| 4 | GET | `/tools/{name}/schema` | @require_auth | 188 |
| 5 | GET | `/tools/{name}/examples` | @require_auth | 198 |
| 6 | POST | `/tools/{name}/test` | @require_auth | 206 |

### Skills (`/api/v1/skills`) — 8 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/skills` | @require_auth | 26 |
| 2 | GET | `/skills/categories` | @require_auth | 130 |
| 3 | GET | `/skills/{name}` | @require_auth | 164 |
| 4 | PUT | `/skills/{name}/enable` | @require_auth | 194 |
| 5 | PUT | `/skills/{name}/disable` | @require_auth | 201 |
| 6 | POST | `/skills/install` | @require_auth | 236 |
| 7 | DELETE | `/skills/{name}` | @require_auth | 296 |
| 8 | POST | `/skills/scan` | @require_auth | 331 |

### Tasks (`/api/v1/tasks`) — 11 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/tasks` | @require_auth | 23 |
| 2 | POST | `/tasks` | @require_auth | 83 |
| 3 | POST | `/tasks/create-with-deps` | @require_auth | 166 |
| 4 | GET | `/tasks/{id}` | @require_auth | 245 |
| 5 | GET | `/tasks/{id}/output` | @require_auth | 271 |
| 6 | PUT | `/tasks/{id}/stop` | @require_auth | 295 |
| 7 | PUT | `/tasks/{id}/update` | @require_auth | 332 |
| 8 | DELETE | `/tasks/{id}` | @require_auth | 408 |
| 9 | GET | `/tasks/{id}/deps` | @require_auth | 435 |
| 10 | POST | `/tasks/{id}/deps` | @require_auth | 473 |
| 11 | GET | `/tasks/stats` | @require_auth | 523 |

### Coordinator (`/api/v1/coordinator`) — 18 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/coordinator/teams` | @require_auth | 47 |
| 2 | POST | `/coordinator/teams` | @require_auth | 95 |
| 3 | GET | `/coordinator/teams/{id}` | @require_auth | 138 |
| 4 | PUT | `/coordinator/teams/{id}` | @require_auth | 162 |
| 5 | DELETE | `/coordinator/teams/{id}` | @require_auth | 189 |
| 6 | GET | `/coordinator/agents` | @require_auth | 212 |
| 7 | GET | `/coordinator/agents/{id}` | @require_auth | 245 |
| 8 | POST | `/coordinator/spawn` | @require_auth | 254 |
| 9 | GET | `/coordinator/tasks` | @require_auth | 327 |
| 10 | GET | `/coordinator/workers` | @require_auth | 366 |
| 11 | POST | `/coordinator/workers` | @require_auth | 397 |
| 12 | POST | `/coordinator/workers/{id}/stop` | @require_auth | 460 |
| 13 | GET | `/coordinator/workers/stats` | @require_auth | 476 |
| 14 | GET | `/coordinator/subagents` | @require_auth | 507 |
| 15 | POST | `/coordinator/subagents` | @require_auth | 521 |
| 16 | GET | `/coordinator/subagents/{id}` | @require_auth | 617 |
| 17 | POST | `/coordinator/subagents/{id}/cancel` | @require_auth | 646 |
| 18 | GET | `/coordinator/subagents/stats` | @require_auth | 664 |

### Permissions (`/api/v1/permissions`) — 12 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/permissions/modes` | @require_auth | 23 |
| 2 | PUT | `/permissions/modes/{id}` | @require_role('admin') | 110 |
| 3 | GET | `/permissions/rules` | @require_auth | 122 |
| 4 | POST | `/permissions/rules` | @require_auth | 148 |
| 5 | PUT | `/permissions/rules/{id}` | @require_auth | 214 |
| 6 | DELETE | `/permissions/rules/{id}` | @require_auth | 236 |
| 7 | GET | `/permissions/denials` | @require_auth | 254 |
| 8 | GET | `/permissions/denials/stats` | @require_auth | 307 |
| 9 | POST | `/permissions/denials/clear` | @require_role('admin') | 350 |
| 10 | GET | `/permissions/denials/tracker` | @require_auth | 405 |
| 11 | POST | `/permissions/denials/tracker/clear` | @require_auth | 427 |
| 12 | POST | `/permissions/check` | @require_auth | 493 |

### Config (`/api/v1/config`) — 9 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/config` | @require_auth | 35 |
| 2 | PUT | `/config` | @require_role('admin') | 83 |
| 3 | POST | `/config/reset` | @require_role('admin') | 141 |
| 4 | GET | `/config/schema` | @require_auth | 148 |
| 5 | GET | `/config/providers` | @require_auth | 163 |
| 6 | POST | `/config/providers` | @require_role('admin') | 198 |
| 7 | PUT | `/config/providers/{id}` | @require_role('admin') | 207 |
| 8 | DELETE | `/config/providers/{id}` | @require_role('admin') | 213 |
| 9 | POST | `/config/providers/{id}/test` | @require_auth | 219 |
| 10 | GET | `/config/validation` | @require_auth | 246 |

### MCP (`/api/v1/mcp`) — 8 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/mcp/servers` | @require_auth | 21 |
| 2 | POST | `/mcp/servers` | @require_role('admin') | 47 |
| 3 | GET | `/mcp/servers/{id}` | @require_auth | 134 |
| 4 | PUT | `/mcp/servers/{id}` | @require_role('admin') | 150 |
| 5 | DELETE | `/mcp/servers/{id}` | @require_role('admin') | 174 |
| 6 | GET | `/mcp/servers/{id}/tools` | @require_auth | 192 |
| 7 | GET | `/mcp/servers/{id}/resources` | @require_auth | 212 |
| 8 | POST | `/mcp/servers/{id}/test` | @require_auth | 232 |

### Audit (`/api/v1/audit`) — 5 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/audit` | @require_auth | 22 |
| 2 | GET | `/audit/{id}` | @require_auth | 118 |
| 3 | GET | `/audit/stats` | @require_auth | 134 |
| 4 | GET | `/audit/export` | @require_role('admin') | 172 |
| 5 | POST | `/audit/purge` | @require_role('admin') | 207 |

### Memory (`/api/v1/memory`) — 14 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/memory/facts` | @require_auth | 39 |
| 2 | POST | `/memory/facts` | @require_auth | 125 |
| 3 | GET | `/memory/facts/{id}` | @require_auth | 250 |
| 4 | PUT | `/memory/facts/{id}` | @require_auth | 268 |
| 5 | DELETE | `/memory/facts/{id}` | @require_auth | 294 |
| 6 | GET | `/memory/stats` | @require_auth | 318 |
| 7 | POST | `/memory/recall` | @require_auth | 381 |
| 8 | POST | `/memory/signal/correction` | @require_auth | 507 |
| 9 | POST | `/memory/signal/reinforcement` | @require_auth | 543 |
| 10 | POST | `/memory/msa/init` | @require_auth | 591 |
| 11 | POST | `/memory/msa/recall` | @require_auth | 633 |
| 12 | GET | `/memory/msa/status` | @require_auth | 670 |
| 13 | POST | `/memory/msa/encode` | @require_auth | 705 |
| 14 | DELETE | `/memory/msa/shutdown` | @require_auth | 728 |

### Channels (`/api/v1/channels`) — 9 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/channels/types` | @require_auth | 62 |
| 2 | GET | `/channels/registered` | @require_auth | 103 |
| 3 | POST | `/channels/register` | @require_auth | 115 |
| 4 | GET | `/channels/{id}` | @require_auth | 198 |
| 5 | PUT | `/channels/{id}` | @require_auth | 210 |
| 6 | DELETE | `/channels/{id}` | @require_auth | 229 |
| 7 | POST | `/channels/{id}/send` | @require_auth | 242 |
| 8 | POST | `/channels/{id}/test` | @require_auth | 278 |
| 9 | GET | `/channels/stats` | @require_auth | 307 |

### Sandbox (`/api/v1/sandbox`) — 4 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/sandbox/status` | @require_auth | 111 |
| 2 | POST | `/sandbox/execute` | @require_auth + @require_role('admin') | 134 |
| 3 | POST | `/sandbox/wrap` | @require_auth | 285 |
| 4 | POST | `/sandbox/security-check` | @require_auth | 330 |

### Plugins (`/api/v1/plugins`) — 7 个端点

| # | 方法 | 路径 | 鉴权 | 行号 |
|---|------|------|------|------|
| 1 | GET | `/plugins` | @require_auth | 25 |
| 2 | GET | `/plugins/available` | @require_auth | 47 |
| 3 | POST | `/plugins/install` | @require_role('admin') | 60 |
| 4 | DELETE | `/plugins/{name}` | @require_role('admin') | 95 |
| 5 | PUT | `/plugins/{name}/enable` | @require_role('admin') | 113 |
| 6 | PUT | `/plugins/{name}/disable` | @require_role('admin') | 120 |
| 7 | GET | `/plugins/{name}/detail` | @require_auth | 141 |

### WebSocket — 5 个客户端事件 + 4 个服务端 emit

| 类型 | 事件名 | 功能 |
|------|--------|------|
| 客户端→服务端 | `connect` | 连接（JWT 认证） |
| 客户端→服务端 | `disconnect` | 断开 |
| 客户端→服务端 | `join_session` | 加入会话房间 |
| 客户端→服务端 | `leave_session` | 离开会话房间 |
| 客户端→服务端 | `ping` | 心跳 |
| 服务端→客户端 | `session_event` | 会话状态变更 |
| 服务端→客户端 | `tool_progress` | 工具执行进度 |
| 服务端→客户端 | `system_notification` | 系统通知推送 |
| 服务端→客户端 | `agent_status` | 智能体状态变化 |

### 非蓝图端点 — 2 个

| 方法 | 路径 | 功能 | 行号 |
|------|------|------|------|
| GET | `/health` | 健康检查 | `main.py:153` |
| GET | `/api/v1/middleware` | 中间件管道信息 | `main.py:192` |
