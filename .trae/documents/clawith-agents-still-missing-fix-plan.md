# 文档数字员工不显示 — 诊断与修复计划

## 问题现象
用户登录成功后，侧边栏/仪表盘的智能体列表为空，特别是"文档部"等数字员工不显示。

## 诊断结果

### 数据层确认 ✅
| 检查项 | 结果 |
|--------|------|
| 数据库 agents 表 | **12 条记录全部存在** |
| 所有 agent.is_expired | **false**（未过期） |
| tenant 关联 | 全部属于 "智盈科技" (id=7c7a2069...) |
| 用户 xxh 的 tenant_id | 与 agents 的 tenant_id **一致** |
| plaza 字段 | 已通过 ALTER TABLE 补全（上一步修复） |
| 后端健康检查 | ✅ 正常 |
| 后端启动日志 | ✅ 无 UndefinedColumnError |

### 根因分析

#### 🔴 根因 #1（核心）：JWT_SECRET_KEY 更换导致 Token 失效 + 前端静默吞错

**完整故障链路**：

```
浏览器 localStorage 存有旧 token（旧 JWT_SECRET_KEY 签发）
    ↓
App.tsx 启动：检测到 token 存在但 user 为 null
    ↓
调用 authApi.me() 用旧 token 验证 → 后端用新密钥校验 → 401 Unauthorized
    ↓
.catch(() => logout()) → 清除 token → 跳转 /login
    ↓
用户重新登录 → 获得新 token → setAuth(user, newToken)
    ↓
跳转到首页 Layout → useQuery 触发 agentApi.list()
    ↓
⚠️ 此时可能出现以下任一问题：
```

**子问题 A — agents 查询无 enabled 条件** ([Layout.tsx:158](file:///home/xxh/Clawith/frontend/src/pages/Layout.tsx#L158-L162))：
```typescript
const { data: agents = [] } = useQuery({
    queryKey: ['agents', currentTenant],
    queryFn: () => agentApi.list(currentTenant || undefined),
    refetchInterval: 30000,
    // ❌ 缺少 enabled: !!token 条件
});
```
- 如果 token 尚未写入 localStorage（时序问题），请求不带认证头 → 401
- `fetchJson` 抛出异常 → TanStack Query 重试 1 次仍失败 → **data 保持默认值 `[]`**

**子问题 B — 错误被静默吞掉** ([api.ts:16-22](file:///home/xxh/Clawith/frontend/src/services/api.ts#L16-L22))：
```typescript
if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || `HTTP ${res.status}`);  // 抛出异常
}
// useQuery 的 onError 未定义 → 异常被静默忽略 → 用户看到空列表
```

**子问题 C — Dashboard 同样的问题** ([Dashboard.tsx:358](file:///home/xxh/Clawith/frontend/src/pages/Dashboard.tsx#L358-L363))：
```typescript
const { data: agents = [], isLoading } = useQuery({
    queryKey: ['agents', currentTenant],
    queryFn: () => agentApi.list(currentTenant || undefined),
    select: (data) => data.filter(agent => !agent.is_expired),
    // ❌ 同样缺少 enabled 和错误处理
});
```

#### 🟡 根因 #2（次要）：浏览器缓存

更换 SECRET_KEY/JWT_SECRET_KEY 后，所有旧 session 数据失效：
- localStorage 中的旧 token 无效
- `current_tenant_id` 可能指向不存在的 tenant
- 需要完全清除缓存或硬刷新

---

## 修复方案

### 步骤 1：给 agents 查询添加认证保护（Layout.tsx）

在 [Layout.tsx:158](file:///home/xxh/Clawith/frontend/src/pages/Layout.tsx#L158) 的 useQuery 中添加：
- `enabled: !!user && !!token` — 只有登录后才查询
- `onError` 回调 — 错误时自动尝试重新获取用户信息

### 步骤 2：给 Dashboard 的 agents 查询添加同样保护

[Dashboard.tsx:358](file:///home/xxh/Clawith/frontend/src/pages/Dashboard.tsx#L358) 同步修改。

### 步骤 3：增强 api.ts 的错误可观测性

在 [api.ts](file:///home/xxh/Clawith/frontend/src/services/api.ts) 中添加控制台警告日志，方便调试。

### 步骤 4：添加全局 401 自动重登录机制

当任何 API 返回 401 时，自动清除过期 token 并跳转到登录页（而不是静默显示空数据）。

---

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/pages/Layout.tsx` | agents/departments useQuery 添加 `enabled` 条件 + `onError` |
| `frontend/src/pages/Dashboard.tsx` | agents useQuery 添加 `enabled` 条件 + `onError` |
| `frontend/src/App.tsx` | 增强 token 验证失败时的处理逻辑 |
| `frontend/src/services/api.ts` | 添加调试日志 + 401 自动登出 |

## 预期效果
- 登录后智能体列表立即正确显示全部 12 个数字员工
- Token 过期时自动跳转登录页而非显示空列表
- API 错误时有明确的用户提示
