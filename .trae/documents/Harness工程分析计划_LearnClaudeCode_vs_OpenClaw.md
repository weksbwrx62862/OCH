# Harness 工程分析计划：Learn-Claude-Code vs OpenClaw 项目

## 📋 任务概述

**目标**: 对比分析微信文章《从0到1用Harness工程搭建类Claude Code的Agent》与现有 OpenClaw 项目的架构差异和优化方向

**文章来源**: https://mp.weixin.qq.com/s/WTD0TEKn0h_vjgNR1WGSxQ
**项目路径**: /home/xxh/.clawith/

---

## 📚 文章核心概念：Harness 工程

### 核心理念
> **别去"开发"智能体，去给它造一个好用的工作环境**

- **模型是司机，Harness 是车**
- **Harness = 工具 + 知识 + 上下文管理 + 权限边界**
- 循环代码始终不变，变的全是 Harness

### 12章节功能矩阵

| 阶段 | 章节 | 核心功能 | 解决的问题 | 实现状态 |
|------|------|---------|-----------|----------|
| **让它跑起来** | S01 | 最小智能体（循环） | 智能体能运转 | ✅ 已实现 |
| | S02 | 工具箱 + 权限围栏 | 能干活，有边界 | ✅ 已实现 |
| **让它干得好** | S03 | Todo 清单 | 防止注意力漂移 | ⚠️ 部分实现 |
| | S04 | 子智能体（上下文隔离） | 分工，上下文不臃肿 | ✅ 已实现 |
| | S05 | 技能文件夹（按需加载） | 知识储备，按需取用 | ✅ 已实现 |
| | S06 | 三层上下文压缩 | 聊多久都不爆 | ❌ 待验证 |
| **让它记得住** | S07 | 任务依赖图 | 关机了任务还在 | ⚠️ 基础实现 |
| | S08 | 后台任务线程 | 不傻等 | ❌ 未实现 |
| **让它带团队** | S09 | 多Agent协作 + 收件箱 | 团队通信 | ✅ 已实现 |
| | S10 | 通信协议（请求-响应+ID） | 关机握手，审批机制 | ⚠️ 部分实现 |
| | S11 | 自治认领机制 | 自己找活干 | ⚠️ 部分实现 |
| | S12 | Worktree 任务隔离 | 各写各的，互不干扰 | ❌ 未实现 |

---

## 🔍 项目现状深度分析

### 1. 已实现的 Harness 组件

#### ✅ S01: 最小智能体循环
**证据**:
- 多个独立 Agent 实例（10+ 个 UUID 标识的 Agent）
- 每个 Agent 有独立的 `soul.md`（灵魂/角色定义）
- Agent 具备自主工作能力（HEARTBEAT.md 存在）

**文件位置**:
```
/home/xxh/.clawith/data/agents/
├── 1c2e0af6-... (市场分析Agent)
├── 340e1e50-... (数据Agent)
├── 543526e8-... (部门管理Agent)
├── e0b80c89-... (研究Agent)
└── ... (共10+个)
```

#### ✅ S02: 工具箱 + 权限围栏
**证据**:
- 技能系统完善（SKILL.md 文件）
- 金融技能包包含 11 个子技能：
  - finance-assistant（统一入口）
  - stock, crypto, fund, macro（数据层）
  - technical, sentiment, portfolio, risk, analysis（功能层）
  - data-source（数据源管理）

**文件位置**:
```
/home/xxh/.clawith/data/agents/594e34f8-.../skills/
├── finance-assistant/SKILL.md
├── crypto/SKILL.md
├── stock/SKILL.md
├── fund/SKILL.md
├── macro/SKILL.md
└── data-source/SKILL.md
```

#### ✅ S04: 子智能体（上下文隔离）
**证据**:
- 每个 Agent 有独立的 workspace
- 独立的 memory 系统（memory.md, MEMORY_INDEX.md, curiosity_journal.md）
- 独立的 focus.md（当前任务焦点）
- 收件箱系统（inbox/ 文件夹用于消息传递）

**文件结构示例**:
```
agent_xxx/
├── soul.md              # 角色定义
├── focus.md             # 当前焦点
├── relationships.md     # 关系定义
├── memory/
│   ├── memory.md        # 长期记忆
│   ├── MEMORY_INDEX.md  # 记忆索引
│   └── curiosity_journal.md  # 好奇心日志
├── workspace/
│   ├── inbox/           # 收件箱
│   └── *.md             # 工作产出
└── skills/              # 技能库
```

#### ✅ S05: 技能文件夹（按需加载）
**证据**:
- 技能以文件夹形式组织
- SKILL.md 包含完整技能说明
- 支持多层级技能（core skills + references）
- SkillHub 管理系统支持远程技能下载

**SkillHub 配置** (`/home/xxh/.skillhub/metadata.json`):
```json
{
  "skills_index_url": "https://skillhub-.../skills.json",
  "skills_search_url": "https://lightmake.site/api/v1/search",
  "skills_download_url_template": "https://..."
}
```

#### ✅ S09: 多Agent协作 + 收件箱
**证据**:
- 多个 Agent 并存且协同工作
- inbox 系统实现消息传递：
  ```
  workspace/inbox/
  ├── 20260405_175150_188272_340e1e50_file_delivery.md
  └── files/
      └── memory.md
  ```
- 文件命名规则：`时间戳_发送者ID_接收者ID_类型.md`
- relationships.md 定义 Agent 间关系

---

### 2. 部分实现的组件

#### ⚠️ S03: Todo 清单
**现状**:
- 有 focus.md 记录当前任务焦点
- 缺少结构化的 Todo 列表（pending/in_progress/completed）
- 缺少强制串行执行机制
- 缺少 3轮无更新自动提醒

**改进建议**:
```markdown
# Todo 清单格式建议

## 当前任务
- [ ] 任务1 (in_progress)
- [ ] 任务2 (pending)
- [x] 任务3 (completed)

## 规则
- 同一时间只能有1个 in_progress
- 连续3轮未更新触发提醒
```

#### ⚠️ S07: 任务依赖图
**现状**:
- 有基础的任务管理（focus.md）
- 缺少显式的任务 ID 和依赖关系（blockedBy）
- 缺少任务状态持久化（JSON 文件）

**改进建议**:
```json
{
  "task_id": "xxx",
  "status": "pending",
  "description": "...",
  "blockedBy": ["task_id_1"],
  "created_at": "2026-04-06T..."
}
```

#### ⚠️ S10: 通信协议
**现状**:
- 有收件箱系统
- 消息有时间戳和发送者信息
- **缺少**: 请求-响应配对机制（唯一 ID）
- **缺少**: 关机握手流程
- **缺少**: 审批机制（领导审核）

**改进建议**:
```markdown
# 消息格式增强
---
request_id: "req_001"
type: "shutdown_request"
from: "leader_agent"
to: "worker_agent"
status: "pending_response"
---
```

#### ⚠️ S11: 自治认领机制
**现状**:
- Agent 可以自主工作（有 HEARTBEAT）
- **缺少**: 任务看板（Task Board）
- **缺少**: 5秒轮询机制
- **缺少**: 60秒空闲自动关机
- **缺少**: 身份信息重新注入（防压缩丢失）

---

### 3. 未实现的关键组件

#### ❌ S06: 三层上下文压缩
**缺失功能**:
1. **第一层**: 3轮前的工具返回替换为标记 `[Previous: used read_file]`
2. **第二层**: Token 超阈值时自动摘要
3. **第三层**: 智能体主动调用压缩工具

**影响**:
- 长对话可能导致上下文爆炸
- 大项目工作时性能下降
- Token 成本增加

**优先级**: 🔴 高（影响核心性能）

#### ❌ S08: 后台任务线程
**缺失功能**:
1. background_run 命令（后台启动）
2. 结果队列存储
3. 每轮自动注入完成的后台任务结果

**场景举例**:
```
用户: 安装依赖并创建配置文件
当前: 必须等安装完（10分钟）才能创建配置文件
期望: 后台安装，同时创建配置文件
```

**优先级**: 🟡 中（提升用户体验）

#### ❌ S12: Worktree 任务隔离
**缺失功能**:
1. Git Worktree 集成
2. 每个任务独立分支
3. 独立提交和合并
4. 干净回滚机制

**影响**:
- 多 Agent 同时编辑可能冲突
- 无法独立回滚单个任务的改动
- 未提交改动互相污染

**优先级**: 🟡 中（多人协作时重要）

---

## 🎯 优化路线图

### Phase 1: 核心稳定性（1-2周）
**目标**: 解决上下文爆炸问题

1. **实现 S06: 三层上下文压缩**
   - 开发 ContextCompressor 工具
   - 实现 sliding window 机制
   - 添加 token 计数器
   - 测试长对话场景

2. **增强 S03: 结构化 Todo**
   - 设计 Todo 数据结构
   - 实现状态转换逻辑
   - 添加超时提醒机制

### Phase 2: 协作效率提升（2-4周）
**目标**: 提升多 Agent 协作质量

3. **完善 S10: 通信协议**
   - 引入 request_id 机制
   - 实现关机握手流程
   - 添加审批工作流

4. **强化 S07: 任务依赖图**
   - 设计 Task JSON Schema
   - 实现依赖检查算法
   - 添加任务持久化存储

5. **实现 S08: 后台任务**
   - 开发 BackgroundRunner
   - 实现结果队列
   - 集成到主循环

### Phase 3: 自治与隔离（4-8周）
**目标**: 实现真正的自治团队

6. **完善 S11: 自治机制**
   - 构建 Task Board
   - 实现5秒轮询
   - 添加空闲超时关机
   - 身份信息防丢失

7. **实现 S12: Worktree 隔离**
   - 集成 Git Worktree API
   - 绑定任务 ID 到分支
   - 实现自动合并策略

---

## 📊 架构对比总结

| 维度 | Learn-Claude-Code (理想) | OpenClaw (现状) | 差距 |
|------|------------------------|----------------|------|
| **循环架构** | 简洁稳定 | ✅ 已实现 | 无 |
| **工具系统** | 可扩展注册 | ✅ 已实现 | 无 |
| **权限控制** | 文件围栏 | ✅ 已实现 | 无 |
| **任务管理** | 依赖图 + 状态机 | ⚠️ 基础版 | 中等 |
| **上下文管理** | 三层压缩 | ❌ 缺失 | **大** |
| **多Agent协作** | 协议化通信 | ⚠️ 基础版 | 中等 |
| **后台任务** | 异步队列 | ❌ 缺失 | 中等 |
| **任务隔离** | Git Worktree | ❌ 缺失 | 中等 |
| **自治能力** | 自动认领 | ⚠️ 部分实现 | 中小 |

---

## 💡 核心洞察

### 1. 项目优势
✅ **已掌握 Harness 工程的核心思想**
- 工具箱模式成熟
- 技能系统完善（11个金融技能）
- 多 Agent 架构清晰
- 记忆系统分层合理

✅ **超出教程的实现**
- Memento-Skills 进化系统（第19课学习笔记）
- SkillHub 远程技能管理
- Obsidian 集成（知识库联动）
- 金融领域的深度专业化

### 2. 关键短板
🔴 **上下文压缩是最大瓶颈**
- 没有 S06，长对话必崩
- 这是生产环境的硬伤

🟡 **协议化程度不足**
- 消息缺少唯一标识
- 缺少请求-响应配对
- 审批流程未标准化

🟡 **缺少异步能力**
- 无法并行执行耗时任务
- 降低整体吞吐量

### 3. 优化优先级排序
1. **🔴 P0: 上下文压缩（S06）** - 影响生存
2. **🟠 P1: 结构化Todo（S03）** - 影响质量
3. **🟡 P2: 通信协议（S10）** - 影响可靠性
4. **🟢 P3: 后台任务（S08）** - 影响效率
5. **🟢 P4: Worktree隔离（S12）** - 影响扩展性

---

## 📝 下一步行动

### 立即可做（本周）
1. **调研上下文压缩方案**
   - 研究 token counting 库（tiktoken）
   - 设计 compression prompt
   - 编写原型 PoC

2. **设计 Todo 数据结构**
   - 定义 JSON Schema
   - 设计状态转换图
   - 编写单元测试

### 短期规划（本月）
3. **实现 ContextCompressor v1.0**
   - 第一层：历史标记替换
   - 第二层：自动摘要触发
   - 第三层：手动压缩接口

4. **重构消息系统**
   - 添加 request_id 字段
   - 实现消息匹配算法
   - 编写通信协议文档

### 中期愿景（季度）
5. **构建完整的 Harness 2.0**
   - 全部 12 个模块就绪
   - 生产级稳定性测试
   - 性能基准报告

---

## 🔗 相关资源

### 项目关键文件
- **主目录**: `/home/xxh/.clawith/`
- **Agent 目录**: `/home/xxh/.clawith/data/agents/`
- **技能目录**: `/home/xxh/.clawith/data/agents/*/skills/`
- **SkillHub**: `/home/xxh/.skillhub/`
- **学习笔记**: `/home/xxh/vault/00-Inbox/🦞【龙虾学习社第19课】...md`

### 参考实现
- GitHub: https://github.com/shareAI-lab/learn-claude-code
- 文章原文: https://mp.weixin.qq.com/s/WTD0TEKn0h_vjgNR1WGSxQ

---

**文档版本**: v1.0
**创建时间**: 2026-04-06
**作者**: AI Assistant
**状态**: 待用户确认
