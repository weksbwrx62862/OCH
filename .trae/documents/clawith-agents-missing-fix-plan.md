# 智能体消失问题诊断与修复计划

## 问题现象
用户登录成功后，智能体列表为空（"我的智能体也没了"）

## 根因分析

### 🔴 根因 #1（确定）：数据库 Schema 与代码模型不同步 — 缺少 4 个 plaza 字段

**Agent 模型定义了 4 个字段，但数据库表中不存在这些列：**

| 缺失的列 | 类型 | 定义位置 |
|-----------|------|----------|
| `plaza_posting_enabled` | boolean | [agent.py:109](file:///home/xxh/Clawith/backend/app/models/agent.py#L109) |
| `plaza_posting_hours` | varchar(20) | [agent.py:110](file:///home/xxh/Clawith/backend/app/models/agent.py#L110) |
| `plaza_min_interval_min` | integer | [agent.py:111](file:///home/xxh/Clawith/backend/app/models/agent.py#L111) |
| `last_plaza_post_at` | timestamp with time zone | [agent.py:112](file:///home/xxh/Clawith/backend/app/models/agent.py#L112) |

**证据链：**
1. 后端启动日志明确报错：
   ```
   UndefinedColumnError: column agents.plaza_posting_enabled does not exist
   ```
2. [trigger_daemon.py:376](file:///home/xxh/Clawith/backend/app/services/trigger_daemon.py#L376) 使用 `select(Agent)` 查询 → SQLAlchemy 自动 SELECT 所有模型字段 → 触发列不存在错误
3. 虽然 [agents.py 的 list_agents](file:///home/xxh/Clawith/backend/app/api/agents.py#L61-L71) 手动选择列避开了此问题，但其他依赖完整 Agent 对象的查询会失败
4. 数据库确认有 12 条 agent 记录（数据未丢失）

### 🟡 根因 #2（次要）：JWT_SECRET_KEY 变更

SECRET_KEY/JWT_SECRET_KEY 已更换为新值，浏览器 localStorage 中的旧 token 全部失效。
- 用户必须**清除浏览器缓存或重新登录**
- 登录接口本身工作正常（已验证返回业务响应而非 500）

---

## 修复方案

### 步骤 1：添加缺失的数据库列（立即修复）

执行 SQL ALTER TABLE 添加 4 个 plaza 字段：

```sql
ALTER TABLE agents
    ADD COLUMN IF NOT EXISTS plaza_posting_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS plaza_posting_hours VARCHAR(20) NOT NULL DEFAULT '00:00-23:59',
    ADD COLUMN IF NOT EXISTS plaza_min_interval_min INTEGER NOT NULL DEFAULT 5,
    ADD COLUMN IF NOT EXISTS last_plaza_post_at TIMESTAMP WITH TIME ZONE;
```

### 步骤 2：重启后端服务

使新 schema 生效并消除 trigger daemon 的报错。

### 步骤 3：验证修复结果

1. 确认后端日志无 `UndefinedColumnError`
2. 用有效凭据登录后调用 `GET /api/agents/` 验证返回 12 条记录
3. 前端页面刷新后应显示全部智能体

---

## 修改范围

| 文件 | 操作 |
|------|------|
| 数据库 (psql) | ALTER TABLE agents 添加 4 列 |
| 无需修改代码 | 代码模型定义是正确的，只是数据库落后于代码 |

## 预防措施

建议后续引入 Alembic 或类似数据库迁移工具，确保：
1. 模型变更自动生成 migration 脚本
2. 启动时检测 schema 差异并提示
3. 避免"代码和数据库手动同步"的不一致风险
