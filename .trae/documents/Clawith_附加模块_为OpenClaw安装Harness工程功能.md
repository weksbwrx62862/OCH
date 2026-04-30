# Clawith 附加模块 - 为 OpenClaw 安装 Harness 工程功能

## 📋 计划概述

**目标**: 将 Clawith 项目中的 Harness 工程功能作为附加模块，安装到 OpenClaw 中，保持 OpenClaw 核心不变

| 项目 | 位置 | 用途 |
|------|------|------|
| **OpenClaw** | `~/.clawith/`, `~/.openclaw/` | 核心保持不变 |
| **Clawith** | `~/Clawith/` | Harness 工程功能来源 |
| **附加模块** | 待确定 | 从 Clawith 移植的功能 |

---

## 🔍 Clawith 项目中的 Harness 工程功能清单

让我们先看看 Clawith 已经实现了哪些我们需要的功能：

### ✅ 已有的核心功能

| 功能 | Clawith 文件 | 说明 |
|------|-------------|------|
| **Token 追踪** | `services/token_tracker.py` | 已有！OpenAI/Anthropic 格式兼容 |
| **摘要器** | `services/summarizer.py` | 已有！BART 模型 + 抽取式 |
| **工具系统** | `services/agent_tools.py` (333KB) | 完整的工具引擎！ |
| **任务执行** | `services/task_executor.py` | 任务执行器 |
| **自主服务** | `services/autonomy_service.py` | Aware 自主意识系统 |
| **Agent 上下文** | `services/agent_context.py` (30KB) | 上下文管理 |
| **工作空间存储** | `services/workspace_storage.py` | 文件系统管理 |
| **工具集合** | `services/tools/` | file_tools, web_tools, mcp_tools 等 |

---

## 🎯 附加模块架构设计

### 原则
1. **OpenClaw 核心零修改** - 不碰 ~/.clawith/ 核心文件
2. **附加模块独立** - 新建一个目录存放移植的代码
3. **通过技能集成** - 用 OpenClaw 的 SKILL.md 机制加载新功能
4. **渐进式启用** - 可以单独启用/禁用各个功能

### 目录结构
```
/home/xxh/
├── .clawith/              # OpenClaw 核心（保持不变）
├── .openclaw/             # OpenClaw 数据（保持不变）
├── Clawith/               # Clawith 源码（参考）
└── Clawith-Addon/         # ← 新建：附加模块
    ├── README.md
    ├── requirements.txt
    ├── setup.py
    ├── clawith_addon/     # Python 包
    │   ├── __init__.py
    │   ├── compression/   # 三层压缩（移植自 Clawith + Claude Code）
    │   ├── tasks/         # Task V2 系统（移植自 Clawith）
    │   ├── tools/         # 增强工具（移植自 Clawith）
    │   ├── summarizer/    # 摘要器（复用 Clawith）
    │   └── token_tracker/ # Token 追踪（复用 Clawith）
    └── skills/            # OpenClaw 技能包
        ├── clawith-compression/
        │   └── SKILL.md
        ├── clawith-tasks/
        │   └── SKILL.md
        └── clawith-tools/
            └── SKILL.md
```

---

## 📋 分阶段实施计划

### Phase 1: 基础移植（1-2天）- 复用 Clawith 现有代码

#### Task 1.1: 项目结构搭建
- [ ] 创建 `~/Clawith-Addon/` 目录
- [ ] 复制关键文件从 Clawith
- [ ] 创建 `requirements.txt`
- [ ] 测试基础导入

**关键文件复制**:
```
Clawith/backend/app/services/token_tracker.py → Clawith-Addon/clawith_addon/token_tracker/
Clawith/backend/app/services/summarizer.py → Clawith-Addon/clawith_addon/summarizer/
```

---

#### Task 1.2: Token 追踪模块集成
**目标**: 让 OpenClaw 能追踪 Token 用量

**实施步骤**:
1. 创建技能 `clawith-token-tracker`
2. 集成 Clawith 的 `token_tracker.py`
3. 创建简单的 JSON 存储（不用数据库）
4. 暴露为 OpenClaw 工具

**SKILL.md 示例**:
```markdown
---
name: clawith-token-tracker
description: Token usage tracking for OpenClaw. Track token consumption per session, per day, per month.
---

# Token Tracker Skill

This skill brings Clawith's token tracking capability to OpenClaw.

## Tools

### track_tokens
Record token usage for the current session.

### get_token_stats
Get token usage statistics (today, this month, total).

## Usage

Call these tools to monitor and track your token consumption.
```

---

#### Task 1.3: 摘要器模块集成
**目标**: 让 OpenClaw 能使用 Clawith 的摘要功能

**实施步骤**:
1. 创建技能 `clawith-summarizer`
2. 集成 Clawith 的 `summarizer.py`
3. 暴露两种摘要器：
   - ExtractiveSummarizer（无模型依赖，快速）
   - TextSummarizer（BART 模型，高质量）

---

### Phase 2: 三层压缩系统（3-5天）- 基于 Claude Code + Clawith

#### Task 2.1: 压缩引擎核心
**目标**: 实现 S06 三层压缩

**文件结构**:
```
Clawith-Addon/clawith_addon/compression/
├── __init__.py
├── core.py              # 主引擎
├── token_counter.py     # Token 计数
├── thresholds.py        # 阈值配置
├── micro_compact.py     # 第一层：微压缩
├── auto_compact.py      # 第二层：自动压缩
├── manual_compact.py    # 第三层：手动压缩
├── storage.py           # 历史存储
└── prompts.py           # 压缩提示词
```

**技能集成**:
```markdown
---
name: clawith-compression
description: Three-tier context compression system for long conversations. Prevents context window overflow with micro-compaction, auto-summarization, and manual compaction tools.
---

# Clawith Compression Skill

This skill brings production-grade context compression from Claude Code and Clawith to OpenClaw.

## Features

1. **Micro-Compaction** (Layer 1): Keeps recent turns full, marks older tool results
2. **Auto-Compaction** (Layer 2): Automatically summarizes when token threshold exceeded
3. **Manual Compaction** (Layer 3): On-demand compression tools

## Tools

### compact_status
Check current token usage and compression status.

### compact_now
Manually trigger conversation compression.

### compact_history
View archived conversation history (nothing is lost!).
```

---

### Phase 3: Task V2 系统（3-5天）- 基于 Clawith

#### Task 3.1: Task 数据模型和存储
**目标**: 实现 S03/S07 Todo V2 + 任务依赖图

**复用 Clawith 的设计思路**，但简化为 OpenClaw 的文件存储：

```
Clawith-Addon/clawith_addon/tasks/
├── __init__.py
├── models.py          # Task 数据模型
├── manager.py         # Task 管理器
├── storage.py         # JSON 文件存储
└── tools/
    ├── task_create.py
    ├── task_update.py
    ├── task_list.py
    └── task_get.py
```

**技能集成**:
```markdown
---
name: clawith-tasks
description: Advanced task management with dependency graphs, persistent storage, and focus tracking.
---

# Clawith Tasks Skill

This skill brings Clawith's Aware focus system and Claude Code's Task V2 to OpenClaw.

## Features

- Task dependency graph (blocks, blockedBy)
- Persistent JSON storage
- Status tracking (pending, in_progress, completed)
- Auto-unlock when dependencies complete

## Tools

### task_create
Create a new task with optional dependencies.

### task_update
Update task status, description, or dependencies.

### task_list
List all tasks with their status and dependencies.

### task_get
Get details of a specific task.
```

---

### Phase 4: 增强工具系统（2-3天）- 基于 Clawith

#### Task 4.1: 工具增强包
**目标**: 将 Clawith 的优质工具带给 OpenClaw

**候选工具**（来自 `Clawith/backend/app/services/tools/`）:
- `file_tools.py` - 增强的文件操作
- `web_tools.py` - Web 抓取工具
- `document_tools.py` - 文档处理
- `mcp_tools.py` - MCP 客户端
- `trigger_tools.py` - 触发器工具

---

## 📦 安装方式

### 方式 1: 作为 OpenClaw 技能安装（推荐）

1. 将 `Clawith-Addon/skills/` 下的技能复制到 OpenClaw 的技能目录
2. 安装 Python 依赖：`pip install -r Clawith-Addon/requirements.txt`
3. 在 OpenClaw 中启用这些技能

### 方式 2: 作为独立 Python 包

1. `cd Clawith-Addon && pip install -e .`
2. 在 OpenClaw 的技能中 import 使用

---

## 🎯 预期成果

| 阶段 | 功能 | 状态 |
|------|------|------|
| Phase 1 | Token 追踪 + 摘要器 | 待开始 |
| Phase 2 | 三层压缩系统 | 待开始 |
| Phase 3 | Task V2 + 依赖图 | 待开始 |
| Phase 4 | 增强工具包 | 待开始 |

---

## 📚 参考文件索引

### Clawith 源码（关键文件）
- `~/Clawith/backend/app/services/token_tracker.py` - Token 追踪
- `~/Clawith/backend/app/services/summarizer.py` - 摘要器
- `~/Clawith/backend/app/services/agent_tools.py` - 工具引擎（333KB）
- `~/Clawith/backend/app/services/task_executor.py` - 任务执行
- `~/Clawith/backend/app/services/autonomy_service.py` - 自主服务
- `~/Clawith/backend/app/services/tools/` - 工具集合

### Claude Code 参考（补充）
- 三层压缩完整实现（20+ 文件）
- Task V2 完整实现

---

**计划版本**: v1.0
**创建时间**: 2026-04-06
**状态**: 计划完成，等待确认
