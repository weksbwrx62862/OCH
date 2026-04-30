# 数字员工仍未显示 - 诊断与修复计划

## 问题现象
用户登录后，侧边栏和仪表板仍未显示任何数字员工（特别是文档部等）

---

## 诊断结论

### 1. 后端 API 工作正常 ✅
- 健康检查通过：`{"status":"ok","version":"1.7.2"}`
- 数据库中有 **12 个智能体**（数据完好）
- 后端正在运行（端口 8008）

### 2. 前端问题定位 🔴
问题很可能出在前端的 useQuery 条件判断上：

**Layout.tsx:162** - 当前代码：
```typescript
enabled: !!user && !!useAuthStore.getState().token
```

**问题**：`useAuthStore.getState().token` 是一个静态调用，不会在 token 更新时触发组件重渲染，可能导致查询永远不会被启用。

---

## 修复方案

### 步骤 1：修复 Layout.tsx 的 useQuery 条件
将 enabled 条件从 `useAuthStore.getState().token` 改为从 React 状态中读取 token：
- 从 useAuthStore 中正确读取 token
- 确保当 token 变化时，useQuery 会正确触发

### 步骤 2：同样修复 Dashboard.tsx
确保 Dashboard.tsx 的 enabled 条件也是一致的

### 步骤 3：临时重置用户密码（如果需要）
如果登录问题持续存在，临时将用户 xxh 的密码重置为一个已知值

---

## 修改文件清单
| 文件 | 修改内容 |
|------|----------|
| `frontend/src/pages/Layout.tsx` | 修复 useQuery enabled 条件，从 store 正确读取 token |
| `frontend/src/pages/Dashboard.tsx` | 同样修复 enabled 条件 |
| `（可选）数据库` | 临时重置用户密码以便登录测试 |

---

## 预期结果
- 用户可以正常登录
- 登录后 12 个数字员工全部显示
