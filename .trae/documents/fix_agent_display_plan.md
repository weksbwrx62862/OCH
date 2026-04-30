# 新建 Agent 不显示在前端的修复计划

## 问题分析

**根本原因**：OpenClaw 和 Clawith 是两个独立的系统！

| 系统 | Agent 配置位置 | 前端显示 |
|------|---------------|----------|
| **OpenClaw** | `~/.openclaw/agents/` | OpenClaw Web UI |
| **Clawith** | Clawith 数据库 | Clawith 前端 |

当前我们在 OpenClaw 中创建了 Agent 配置，但这些 Agent 没有注册到 Clawith 数据库，所以 Clawith 前端不显示。

## 修复方案

### 方案 A：将 OpenClaw Agent 注册到 Clawith（推荐）

**步骤**：
1. 读取 OpenClaw 中已有的 Agent 配置
2. 将其注册到 Clawith 数据库（通过 API）
3. 配置 Agent 与 OpenClaw runtime 的关联

### 方案 B：使用 Clawith 的 Agent 创建功能

**步骤**：
1. 在 Clawith 前端手动创建 Agent
2. 选择对应的 OpenClaw workspace 作为 runtime

---

## 实施步骤（方案 A）

### 步骤 1：分析现有 OpenClaw Agent 配置
- [ ] 列出所有 OpenClaw Agent：`~/.openclaw/agents/`
- [ ] 读取每个 Agent 的 SOUL.md、AGENTS.md

### 步骤 2：准备 Clawith API 注册
- [ ] 获取用户认证 Token
- [ ] 准备 Agent 创建请求格式

### 步骤 3：批量注册 Agent
- [ ] 创建脚本读取 OpenClaw 配置
- [ ] 调用 Clawith API 注册每个 Agent
- [ ] 验证注册成功

### 步骤 4：验证前端显示
- [ ] 登录 Clawith 前端检查 Agent 列表
- [ ] 确认新注册的 Agent 可见

---

## 技术细节

### Clawith Agent 创建 API
```bash
POST /api/agents/
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "调度中心",
  "role_description": "AI公司的CEO，唯一对外入口",
  "bio": "用户与AI团队之间的桥梁",
  "primary_model_id": "<model-uuid>",
  "autonomy_policy": {...},
  "template_id": "<template-uuid>"
}
```

### 需要的准备工作
1. 获取 Clawith 后端 API 地址（当前：http://localhost:8000）
2. 获取管理员 Token 或创建 Token
3. 获取可用 LLM Model ID 列表

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Agent 重复创建 | 数据库冗余 | 先检查是否已存在 |
| Model ID 不匹配 | Agent 无法运行 | 提前获取可用 Model 列表 |
| 权限配置错误 | Agent 不可用 | 按模板默认配置 |

---

## 下一步

1. **确认**：用户是否同意此修复方案？
2. **执行**：获取 Clawith API Token 并开始注册

**预计工作量**：约 30 分钟（获取 Token + 创建脚本 + 注册验证）