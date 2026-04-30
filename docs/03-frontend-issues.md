# 前端问题

## 1. 依赖安装与启动

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `next.config.js` 中 WebSocket rewrite 可能不正确 | `next.config.js:17-19` | `/ws/:path*` → `${BACKEND_URL}/ws/:path*`，但 SocketIO 使用 `/socket.io/*` 路径，应改为 `/socket.io/:path*` |
| 2 | Docker 环境下前端使用 `npm run dev` | `docker-compose.yml:70` | 生产镜像用多阶段构建了 standalone 模式，但 `command: npm run dev` 会覆盖 Dockerfile 的 CMD，导致总是以开发模式运行 |
| 3 | `BACKEND_URL` 在 Docker 中为 `http://backend:8008` | `docker-compose.yml:64` | 但 `next.config.js` 的 rewrite 在服务端执行，`http://backend:8008` 可达。SSE 代理 `route.ts` 也读取 `BACKEND_URL`，这是正确的 |

## 2. API 客户端 `lib/api.ts`

**调试步骤**：

```bash
# 检查 API 连通性
cd /home/xxh/openclaw-harness/frontend
curl http://localhost:3000/api/v1/health  # 应代理到后端
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | SSE 流式聊天不经过 rewrite 代理 | `api.ts:114` | `streamChat()` 直接请求 `/api/proxy/chat`，这是正确的（Next.js rewrite 不支持 SSE），但需确保 Route Handler 正常工作 |
| 2 | `getHeaders()` 在 SSR 时 `localStorage` 不可用 | `api.ts:26-31` | 已用 `typeof window !== 'undefined'` 守护，OK |
| 3 | 超时 30 秒对于长对话可能不够 | `api.ts:37` | AI 生成+工具执行可能超过 30 秒，建议聊天请求使用更长的超时 |

## 3. 认证流程 `AuthProvider.tsx`

**调试步骤**：

1. 访问 `http://localhost:3000` — 应重定向到 `/login`
2. 输入任意用户名（开发模式）登录
3. 检查 `localStorage` 中 `och_token` 是否存在

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `AuthProvider` 只检查 token 存在性 | `AuthProvider.tsx:13` | `!!token` 只检查 token 非空，不验证有效性。如果 token 已过期，用户不会被重定向到登录页，直到 API 调用返回 401 |
| 2 | 没有全局 401 拦截 | `api.ts` 全局 | 当 API 返回 401 时，应自动清除 token 并重定向到登录页。当前 `api.ts` 只抛出错误，未处理 401 |
| 3 | 登录页未处理 token 已存在的情况 | `login/page.tsx` | 如果用户已登录再访问 `/login`，应重定向到首页 |

**调整建议**：在 `api.ts` 的 `request()` 方法中添加 401 响应拦截，自动清除 `localStorage.och_token` 并跳转 `/login`。

## 4. 页面组件

**各页面调试检查清单**：

| 页面 | 路由 | 检查要点 |
|------|------|---------|
| Dashboard | `/` | API 调用 `/sessions`, `/agents`, `/audit` 是否返回正确格式 |
| Login | `/login` | 开发模式无密码登录是否正常 |
| Chat | `/chat` | SSE 流式是否工作，quick-create Agent + Session 是否成功 |
| Agents | `/agents` | CRUD 操作是否正常，权限配置是否保存 |
| Sessions | `/sessions` | 列表分页、状态筛选是否正常 |
| Tasks | `/tasks` | 任务创建、状态更新是否正常 |
| Skills | `/skills` | 技能列表是否加载 |
| Tools | `/tools` | 工具列表是否显示 |
| Audit | `/audit` | 审计日志是否有数据 |
| Settings | `/settings` | 配置读取和更新是否正常 |
| Swarm | `/swarm` | 团队管理是否正常 |

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `components/chat/` 等目录为空 | `components/chat/`, `coordinator/`, `dashboard/`, `skills/`, `tools/` | 架构文档描述了 `MemorySidebar`, `ToolCallCard` 等组件，实际它们位于 `app/chat/` 中。组件目录结构应整理 |
| 2 | `(dashboard)/` 路由组下所有目录为空 | `app/(dashboard)/` | 子路由如 `agents/[agentId]/edit/`、`chat/[sessionId]/` 等目录存在但无页面文件，这些详情页未实现 |
| 3 | `(auth)/` 路由组为空 | `app/(auth)/` | 未使用，可删除 |
| 4 | `hooks/` 根目录为空 | `hooks/` | 自定义 hooks 在 `lib/hooks/` 中，根 `hooks/` 目录多余 |
| 5 | `styles/themes/` 为空 | `styles/themes/` | 主题通过 CSS 变量实现，此目录多余 |

## 5. 类型定义 `lib/types.ts`

**调试步骤**：

```bash
cd /home/xxh/openclaw-harness/frontend
npx tsc --noEmit
```

**问题与调整**：

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `ToolPermission.path_rules` 类型为 `string[]` | `types.ts:43` | 后端模型中 `path_rules` 是 JSON 类型，实际可能为对象数组而非字符串数组 |
| 2 | `Task` 类型字段与后端不完全对齐 | `types.ts:86-102` | 前端有 `title`, `description`, `priority`, `progress`, `parent_task_id` 等字段，但后端 Task 模型字段为 `task_type`, `command`, `exit_code`, `pid` 等，差异较大 |
| 3 | 缺少 `Team`, `TeamMember`, `MCPServer`, `Plugin` 类型 | `types.ts` | 后端有这些模型但前端未定义对应类型 |

## 6. 前端代理与 API 边缘案例

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `NEXT_PUBLIC_API_URL` 默认相对路径 `/api/v1` — SSR 时无法解析 | `lib/api.ts:3` | Next.js SSR（服务端渲染）时，相对路径 `/api/v1` 无法解析为后端地址（SSR 运行在 Node.js 进程，不是浏览器）。SSR 请求会 404。应在 SSR 环境使用完整 URL |
| 2 | WebSocket 代理 — `next.config.js` 只代理 HTTP | `next.config.js:rewrites` | SocketIO WebSocket 连接不会被 Next.js rewrites 处理。需要配置 `ws` 协议代理或客户端直连后端 |
| 3 | 前端 `fetchApi` 无重试逻辑 | `lib/api.ts:fetchApi` | 网络抖动或后端重启时，API 调用直接失败。应添加指数退避重试 |

## 7. 前后端类型对齐

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 前端 `Task` 类型完全偏离后端模型 | `types.ts:86-102` | 前端有 `title/description/priority/progress`，后端有 `task_type/command/exit_code/pid`。前端代码无法正确渲染任务列表 |
| 2 | 前端缺少 `Team`/`TeamMember`/`MCPServer`/`Plugin` 类型 | `types.ts` | 后端有完整的 CRUD API，但前端未定义这些类型，导致 `/swarm`、`/tools` (MCP)、`/settings` (Plugins) 页面无法正确交互 |
| 3 | 前端 `ToolPermission.path_rules` 类型可能不匹配 | `types.ts:43` | 前端定义为 `string[]`，后端 `agent.py:80` 定义为 `Optional[List[Dict]]`（对象数组），实际是路径规则对象数组而非字符串数组 |
| 4 | `MCPServer.to_dict()` 输出 `type` 而非 `server_type` | `mcp_server.py:57` | `to_dict()` 中键名是 `'type': self.server_type`，但模型字段名是 `server_type`，前端如果按 `server_type` 取值会取不到 |

## 8. 前端依赖与配置问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `package.json` 缺少 `socket.io-client` | `frontend/package.json` | 后端有完整的 WebSocket/SockerIO 实现，但前端未安装 `socket.io-client` 依赖 |
| 2 | `package.json` 缺少 `aiofiles` 的前端等价物 | — | 后端 `skill_service.py` 使用 `aiofiles`，前端技能管理页面可能需要异步文件操作支持 |
| 3 | `next.config.js` 缺少 MCP API 路由代理 | `next.config.js` | 后端有 `/api/v1/mcp/*` 端点，但前端 `next.config.js` 的 rewrite 规则未覆盖 MCP 路由 |

## 9. SSE 事件格式问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | SSE 流中 `asyncio.run()` 与 Flask 线程冲突 | `sessions.py` | Flask 的 SSE 在独立线程中运行，内部调用 `asyncio.run()` 创建新事件循环。如果该线程中已有其他异步操作，会抛出 `RuntimeError` |
| 2 | SSE 客户端断开时服务端无感知 | `sessions.py` | `stream_with_context` 在客户端断开后可能继续生成数据，浪费资源。应添加 `request.environ.get('werkzeug.socket')` 检测或使用 `generate()` 中的 `should_abort` 信号 |
| 3 | 长时间流式响应可能超时 | `api.ts:37` | 前端 30 秒超时对于需要工具执行的长对话不够。AI 回复可能涉及多轮工具调用，单次响应可能超过 5 分钟 |
| 4 | SSE 流中 `queue.Queue` 无大小限制 | `sessions.py` | 如果消费端（Flask 响应线程）慢于生产端（异步生成器），队列会无限增长，可能导致内存溢出 |

## 10. 前端 SSE 代理问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 前端 `streamChat()` 通过 `/api/proxy/chat` 代理，但 SSE 事件格式未校验 | `lib/api.ts:174-184` vs `session_service.py:278` | 前端定义 `StreamEvent.type` 包括 `thinking`, `text_delta`, `tool_start`, `tool_end`, `turn_complete`, `error`。但后端 `_simulate_stream()` 输出 `text_delta`（有 `content` 字段）和 `turn_complete`（有 `stop_reason`, `usage`, `hooks_triggered` 字段），与 OpenHarness 真实 `StreamEvent` 的 `AssistantTextDelta(text=...)` 格式完全不同。若未来切换到真实引擎，前端解析会全面崩溃 |
