# Claude Code 源码 - Harness 工程完整分析报告

## 📋 文档信息

- **分析日期**: 2026-04-06
- **源码来源**: /home/xxh/claudecode源码(仅用于学习交流)/claude-code-main/
- **对比基准**: Learn-Claude-Code 12章节 Harness 工程教程
- **目标项目**: OpenClaw (/home/xxh/.clawith/)

---

## 📚 12章节完整对照分析

### S01: 最小智能体循环 ✅ 已完整实现

**Claude Code 实现位置**:
- 核心文件: `src/query.ts` (1700+ 行)
- 上层封装: `src/QueryEngine.ts` (1300+ 行)
- 交互层: `src/screens/REPL.tsx` (5000+ 行)

**核心实现特征**:
```typescript
// query.ts 中的核心循环结构
1. 构建消息列表
2. 调用 Claude API 流式响应
3. 解析工具调用
4. 执行工具 (StreamingToolExecutor)
5. 处理工具结果
6. 循环直到完成
```

**关键技术点**:
- 自动工具调用决策由模型决定，无需硬编码终止条件
- 流式处理，实时响应用户
- 工具权限检查 (permissions.ts)
- Token 预算追踪 (tokenBudget.ts)

---

### S02: 工具箱 + 权限围栏 ✅ 已完整实现

**Claude Code 实现**:

#### 工具注册系统
- 核心接口: `src/Tool.ts` (Tool 类型定义)
- 工具注册表: `src/tools.ts`
- 工具目录: `src/tools/<ToolName>/` (每个工具独立目录)

#### 权限系统 (6300+ 行)
- 权限模式: plan/auto/manual
- YOLO 分类器 (自动判断是否需要确认)
- 路径验证规则
- 沙箱执行 (BashTool, PowerShellTool)

#### 已实现的核心工具 (始终可用)
| 工具 | 文件 | 功能 |
|------|------|------|
| BashTool | `src/tools/BashTool/` | Shell 执行，沙箱 |
| FileReadTool | `src/tools/FileReadTool/` | 文件/PDF/图片读取 |
| FileEditTool | `src/tools/FileEditTool/` | 字符串替换式编辑 |
| FileWriteTool | `src/tools/FileWriteTool/` | 文件创建/覆写 |
| AgentTool | `src/tools/AgentTool/` | 子代理派生 |
| WebFetchTool | `src/tools/WebFetchTool/` | URL 抓取 → Markdown |
| WebSearchTool | `src/tools/WebSearchTool/` | 网页搜索 |
| TodoWriteTool | `src/tools/TodoWriteTool/` | Todo 列表 v1 |
| SkillTool | `src/tools/SkillTool/` | 技能调用 |
| SendMessageTool | `src/tools/SendMessageTool/` | 消息发送 |

---

### S03: Todo 清单 ✅ 已完整实现（V1 + V2）

**Claude Code 实现了两个版本**:

#### TodoWriteTool (V1) - `src/tools/TodoWriteTool/TodoWriteTool.ts`
```typescript
// 数据结构
type Todo = {
  id?: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
}

// 核心逻辑
- 同一时间只能有一个 in_progress
- 全部完成时清空列表
- 3+ 任务完成且无验证步骤时自动提醒
- verificationNudgeNeeded 机制
```

#### Task 工具 (V2) - 条件启用 (isTodoV2Enabled)
| 工具 | 文件 | 功能 |
|------|------|------|
| TaskCreateTool | `src/tools/TaskCreateTool/` | 创建任务 |
| TaskUpdateTool | `src/tools/TaskUpdateTool/` | 更新任务（含依赖）|
| TaskListTool | `src/tools/TaskListTool/` | 列出任务 |
| TaskGetTool | `src/tools/TaskGetTool/` | 获取单个任务 |

**Task V2 核心特性** (TaskUpdateTool.ts):
```typescript
// 支持依赖关系
type Task = {
  id: string;
  subject: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  blocks: string[];     // 此任务阻塞的任务 ID
  blockedBy: string[];  // 阻塞此任务的任务 ID
  owner?: string;       // 任务所有者
  metadata?: Record<string, unknown>;
}

// 关键机制
- blockTask(): 建立阻塞关系
- addBlocks/addBlockedBy: 支持依赖图
- 自动分配所有者 (in_progress 时)
- 邮箱通知任务分配变更
```

---

### S04: 子智能体（上下文隔离）✅ 已完整实现

**Claude Code 实现位置**: `src/tools/AgentTool/`

#### 核心文件
- `AgentTool.tsx`: 主工具实现
- `forkSubagent.ts`: 分叉子代理
- `runAgent.ts`: 运行代理
- `resumeAgent.ts`: 恢复代理
- `agentMemory.ts`: 代理记忆管理

#### 支持的子代理类型
```typescript
// AgentTool 支持的模式
1. fork: 从当前会话分叉独立子代理
2. async: 异步子代理
3. background: 后台子代理
4. remote: 远程子代理
```

#### 上下文隔离机制
- 子代理有独立的 `agentId`
- 独立的记忆空间 (`agentMemory.ts`)
- 独立的 Todo 列表 (todoKey = agentId)
- 子代理工具箱不含 AgentTool（防止无限套娃）
- 最终只返回摘要给父代理

---

### S05: 技能加载（按需加载）✅ 已完整实现

**Claude Code 实现**:

#### 技能系统架构
- **技能目录**: `skills/bundled/` - 内置技能
- **技能工具**: `src/tools/SkillTool/` - 技能调用
- **技能搜索**: `src/services/skillSearch/` - 本地/远程搜索
- **技能预加载**: `src/services/skillSearch/prefetch.ts`

#### 按需加载机制
1. **启动时**: 只注入技能名称和简短描述（几十 token）
2. **使用时**: 调用 SkillTool 才加载完整 SKILL.md 内容
3. **远程技能**: SkillHub API 支持动态下载

#### 技能结构
```
skill-name/
├── SKILL.md          # 技能定义
├── prompt.ts         # 提示词
├── <ToolName>.ts     # 关联工具（可选）
└── references/       # 参考资料（可选）
```

---

### S06: 三层上下文压缩 ✅ 已完整实现（生产级）

**Claude Code 实现位置**: `src/services/compact/` (20+ 文件)

#### 三层压缩机制

| 层级 | 文件 | 功能 |
|------|------|------|
| **第一层** | `microCompact.ts` | 微压缩：最近几轮保持完整，旧的只留印记 |
| **第二层** | `autoCompact.ts` | 自动压缩：Token 超阈值时触发摘要 |
| **第三层** | `compact.ts` | API 压缩：手动调用 `/compact` 命令 |

#### 核心实现细节

**autoCompact.ts - 自动压缩触发逻辑**:
```typescript
// Token 阈值配置
const AUTOCOMPACT_BUFFER_TOKENS = 13_000
const WARNING_THRESHOLD_BUFFER_TOKENS = 20_000
const ERROR_THRESHOLD_BUFFER_TOKENS = 20_000
const MANUAL_COMPACT_BUFFER_TOKENS = 3_000

// 压缩触发条件
function getAutoCompactThreshold(model: string): number {
  const effectiveContextWindow = getEffectiveContextWindowSize(model)
  return effectiveContextWindow - AUTOCOMPACT_BUFFER_TOKENS
}

// Token 警告状态
function calculateTokenWarningState(tokenUsage, model) {
  return {
    percentLeft,
    isAboveWarningThreshold,
    isAboveErrorThreshold,
    isAboveAutoCompactThreshold,
    isAtBlockingLimit
  }
}
```

**compact.ts - 压缩主逻辑**:
```typescript
type CompactionResult = {
  compacted: boolean;
  summaryMessage: Message;
  removedMessages: Message[];
}

// 压缩流程
1. 调用模型生成对话摘要
2. 用摘要替换历史消息
3. 保留最近几轮完整消息
4. 所有历史存入磁盘（不丢失）
```

**microCompact.ts - 微压缩**:
```typescript
// 历史工具返回标记化
[Previous: used read_file on "src/main.ts"]
[Previous: used bash with "ls -la"]
```

#### 额外增强
- `cachedMicrocompact.ts`: 缓存优化
- `reactiveCompact.ts`: 响应式压缩
- `sessionMemoryCompact.ts`: 会话记忆压缩
- `snipCompact.ts`: 历史片段裁剪 (HISTORY_SNIP flag)

---

### S07: 任务依赖图 ✅ 已完整实现（Task V2）

**Claude Code 实现**: Task V2 系统

#### 核心数据结构
```typescript
// src/utils/tasks/types.ts
type Task = {
  id: string;
  subject: string;
  description: string;
  activeForm?: string;  // 进行中显示文本（如 "Running tests"）
  status: 'pending' | 'in_progress' | 'completed';
  blocks: string[];     // 此任务阻塞的任务 ID
  blockedBy: string[];  // 阻塞此任务的任务 ID
  owner?: string;       // 任务所有者（团队协作时）
  metadata?: Record<string, unknown>;
}
```

#### 任务管理工具
| 操作 | 工具 | 功能 |
|------|------|------|
| 创建 | TaskCreateTool | 创建任务，初始 pending |
| 更新 | TaskUpdateTool | 修改状态、依赖、所有者 |
| 查询 | TaskGetTool | 获取单个任务详情 |
| 列表 | TaskListTool | 列出所有任务及状态 |
| 删除 | TaskUpdateTool (status='deleted') | 删除任务 |

#### 依赖解锁逻辑 (TaskUpdateTool.ts)
```typescript
// 当任务 A 完成时
1. 遍历所有 blockedBy 包含 A 的任务
2. 从它们的 blockedBy 中移除 A
3. 如果某个任务的 blockedBy 变为空
   → 自动解锁，可以开始执行
```

#### 持久化存储
- 每个任务独立 JSON 文件
- 关机后任务状态保留
- 支持跨会话恢复

---

### S08: 后台任务线程 ✅ 已完整实现

**Claude Code 实现位置**:

#### 后台任务工具
| 工具 | 文件 | 功能 |
|------|------|------|
| (隐含) | AgentTool (background mode) | 后台子代理 |
| TaskOutputTool | `src/tools/TaskOutputTool/` | 读取后台任务输出 |
| TaskStopTool | `src/tools/TaskStopTool/` | 停止后台任务 |

#### 后台任务执行流程
```typescript
// 1. 后台启动
background_run(command): 立即返回 task_id，不等结果

// 2. 结果进队列
后台命令跑完后 → 存入通知队列

// 3. 每轮自动注入
每次调用模型前 → Harness 检查队列 → 注入完成的任务结果
```

#### BG_SESSIONS Feature Flag
```
ps: 列出后台进程
logs: 查看后台日志
attach: 附着到后台会话
kill: 终止后台进程
--bg: 后台启动新会话
```

---

### S09: 多 Agent 协作 + 收件箱 ✅ 已完整实现

**Claude Code 实现**:

#### 团队管理工具 (isAgentSwarmsEnabled)
| 工具 | 文件 | 功能 |
|------|------|------|
| TeamCreateTool | `src/tools/TeamCreateTool/` | 创建团队 |
| TeamDeleteTool | `src/tools/TeamDeleteTool/` | 删除团队 |
| SendMessageTool | `src/tools/SendMessageTool/` | 发送消息到队友/收件箱 |

#### 收件箱系统
```typescript
// src/utils/teammateMailbox.ts
writeToMailbox(
  recipient: string,
  message: {
    from: string;
    text: string;
    timestamp: string;
    color: string;
  },
  taskListId: string
)

// 消息结构示例
{
  type: 'task_assignment',
  taskId: '123',
  subject: 'Implement login',
  description: '...',
  assignedBy: 'team-lead',
  timestamp: '2026-04-06T...'
}
```

#### 队友管理
```typescript
// src/utils/teammate.ts
getAgentName()      // 获取当前 Agent 名称
getTeamName()       // 获取团队名称
getTeammateColor()  // 获取队友颜色
getAgentId()        // 获取 Agent ID
```

#### 消息注入流程
每次调用大模型前，自动将收件箱内容注入到对应 Agent 的上下文中

---

### S10: 通信协议（请求-响应+ID）⚠️ 部分实现

**Claude Code 实现的通信原语**:

#### 已有的消息 ID 机制
- 每个消息有唯一 `uuid`
- 工具调用有 `tool_use_id`
- 工具结果引用 `tool_use_id`

#### 消息配对示例
```typescript
// AssistantMessage (工具调用)
{
  uuid: 'msg_001',
  message: {
    content: [{
      type: 'tool_use',
      id: 'tool_001',  // 工具调用 ID
      name: 'FileReadTool',
      input: { path: '...' }
    }]
  }
}

// UserMessage (工具结果)
{
  uuid: 'msg_002',
  content: [{
    type: 'tool_result',
    tool_use_id: 'tool_001',  // 引用对应的工具调用
    content: '...'
  }]
}
```

#### 待完善的高级协议
- **关机握手**: 显式的 shutdown_request / shutdown_response
- **审批机制**: proposal / approval / rejection
- 这些在 Feature Flags 后 (KAIROS, AGENT_SWARMS)

---

### S11: 自治认领机制 ⚠️ 部分实现

**Claude Code 实现的基础**:

#### 任务看板基础 (Task V2)
- 任务列表公开可见
- 任务有状态 (pending/in_progress/completed)
- 支持任务所有权 (owner 字段)

#### 待完善的自治特性
这些在 Feature Flags 后:
- **5秒轮询**: 空闲时轮询收件箱和任务看板
- **自动认领**: 发现可认领任务自动领取
- **60秒空闲关机**: 持续无活动自动关机
- **身份信息重新注入**: 防压缩丢失

#### Feature Flags
```
KAIROS: 自主 Agent 模式
PROACTIVE: 主动执行模式
AGENT_SWARMS: 多 Agent 团队协作
```

---

### S12: Worktree 任务隔离 ✅ 已完整实现

**Claude Code 实现位置**: `src/tools/EnterWorktreeTool/`

#### 核心工具
| 工具 | 文件 | 功能 |
|------|------|------|
| EnterWorktreeTool | `src/tools/EnterWorktreeTool/` | 创建并进入隔离 worktree |
| ExitWorktreeTool | `src/tools/ExitWorktreeTool/` | 退出 worktree |

#### EnterWorktreeTool.ts - 核心实现
```typescript
// 关键步骤
1. 验证未在 worktree 中
2. 定位主 Git 仓库根目录
3. createWorktreeForSession(sessionId, slug)
4. 切换 CWD 到 worktree 路径
5. 保存 worktree 状态到 sessionStorage
6. 清除系统提示缓存（重新计算环境信息）

// Git Worktree 集成
每个 worktree:
- 独立的 Git 分支
- 独立的工作目录
- 独立的提交历史
```

#### Worktree 工具函数
```typescript
// src/utils/worktree.ts
createWorktreeForSession(sessionId, slug)  // 创建
getCurrentWorktreeSession()                // 获取当前
validateWorktreeSlug(slug)                  // 验证名称
```

#### 与任务系统绑定
- worktree 通过 `sessionId` 与任务关联
- 任务管"做什么"，worktree 管"在哪做"
- 完成后可独立合并回主分支

---

## 📊 功能完整度总览

| 章节 | 功能 | Claude Code | OpenClaw | 差距 |
|------|------|-------------|----------|------|
| S01 | 最小智能体循环 | ✅ 完整 | ✅ 已有 | 无 |
| S02 | 工具箱 + 围栏 | ✅ 完整 | ✅ 已有 | 无 |
| S03 | Todo 清单 | ✅ 完整（V1+V2） | ⚠️ 基础版 | 中 |
| S04 | 子智能体 | ✅ 完整 | ✅ 已有 | 无 |
| S05 | 技能加载 | ✅ 完整 | ✅ 已有 | 无 |
| S06 | 三层压缩 | ✅ 生产级 | ❌ 缺失 | **大** |
| S07 | 任务依赖图 | ✅ 完整 | ⚠️ 基础版 | 中 |
| S08 | 后台任务 | ✅ 完整 | ❌ 缺失 | 中 |
| S09 | 多 Agent + 收件箱 | ✅ 完整 | ✅ 已有 | 无 |
| S10 | 通信协议 | ⚠️ 基础 | ⚠️ 基础 | 小 |
| S11 | 自治认领 | ⚠️ 部分 | ⚠️ 部分 | 小 |
| S12 | Worktree 隔离 | ✅ 完整 | ❌ 缺失 | 中 |

---

## 🎯 OpenClaw 优化路线图（基于 Claude Code 源码）

### Phase 1: 核心稳定性（P0 - 1-2周）

#### 1.1 实现 S06: 三层上下文压缩
**参考文件**:
- `claude-code-main/src/services/compact/autoCompact.ts`
- `claude-code-main/src/services/compact/compact.ts`
- `claude-code-main/src/services/compact/microCompact.ts`

**实施步骤**:
1. 移植 Token 计数和阈值判断逻辑
2. 实现 microCompact（历史工具返回标记化）
3. 实现 autoCompact（自动摘要触发）
4. 集成到主循环

**验收标准**:
- [ ] 100+ 轮对话不爆炸
- [ ] Token 使用率降低 60%+
- [ ] 历史信息不丢失（磁盘存储）

---

#### 1.2 增强 S03: 结构化 Todo（V2）
**参考文件**:
- `claude-code-main/src/tools/TaskCreateTool/TaskCreateTool.ts`
- `claude-code-main/src/tools/TaskUpdateTool/TaskUpdateTool.ts`
- `claude-code-main/src/utils/tasks/types.ts`

**实施步骤**:
1. 设计 Task JSON Schema
2. 实现 4 个 Task 工具（Create/Update/List/Get）
3. 实现依赖解锁算法
4. 添加持久化存储

**验收标准**:
- [ ] 支持任务依赖图
- [ ] 任务状态持久化
- [ ] 依赖自动解锁

---

### Phase 2: 协作效率提升（P1 - 2-4周）

#### 2.1 实现 S12: Worktree 任务隔离
**参考文件**:
- `claude-code-main/src/tools/EnterWorktreeTool/EnterWorktreeTool.ts`
- `claude-code-main/src/utils/worktree.ts`

**实施步骤**:
1. 集成 Git Worktree API
2. 实现 Enter/ExitWorktree 工具
3. 绑定任务 ID 到 worktree
4. 实现自动合并策略

**验收标准**:
- [ ] 每个任务独立分支
- [ ] 支持干净回滚
- [ ] 多 Agent 无冲突

---

#### 2.2 实现 S08: 后台任务
**参考文件**:
- `claude-code-main/src/tools/TaskOutputTool/TaskOutputTool.tsx`
- `claude-code-main/src/tools/TaskStopTool/TaskStopTool.ts`

**实施步骤**:
1. 实现 BackgroundRunner
2. 设计结果队列
3. 每轮自动注入机制
4. 实现 TaskOutput/TaskStop 工具

**验收标准**:
- [ ] 后台任务不阻塞主循环
- [ ] 结果自动推送
- [ ] 支持任务停止

---

#### 2.3 完善 S10: 通信协议
**参考文件**:
- `claude-code-main/src/utils/messages.ts`
- `claude-code-main/src/tools/SendMessageTool/SendMessageTool.ts`

**实施步骤**:
1. 添加 request_id 到消息结构
2. 实现请求-响应配对算法
3. 设计关机握手流程
4. 实现审批工作流

**验收标准**:
- [ ] 消息可追踪配对
- [ ] 关机安全握手
- [ ] 审批流程标准化

---

### Phase 3: 自治能力（P2 - 4-8周）

#### 3.1 完善 S11: 自治认领机制
**参考文件**:
- `claude-code-main/src/utils/teammate.ts`
- `claude-code-main/src/utils/teammateMailbox.ts`

**实施步骤**:
1. 构建 Task Board 看板
2. 实现 5秒轮询逻辑
3. 添加 60秒空闲关机
4. 实现身份信息防丢失

**验收标准**:
- [ ] Agent 自动认领任务
- [ ] 空闲自动关机
- [ ] 身份不丢失

---

## 📁 关键源码文件索引

### 核心循环
- `src/query.ts` - 主查询循环 (1700+ 行)
- `src/QueryEngine.ts` - 查询引擎 (1300+ 行)

### 工具系统
- `src/Tool.ts` - 工具接口定义
- `src/tools.ts` - 工具注册表
- `src/tools/<ToolName>/` - 各工具实现

### 上下文压缩
- `src/services/compact/autoCompact.ts` - 自动压缩触发
- `src/services/compact/compact.ts` - 压缩主逻辑
- `src/services/compact/microCompact.ts` - 微压缩

### 任务管理
- `src/tools/TaskCreateTool/TaskCreateTool.ts`
- `src/tools/TaskUpdateTool/TaskUpdateTool.ts`
- `src/utils/tasks/` - 任务工具函数

### 子代理
- `src/tools/AgentTool/AgentTool.tsx`
- `src/tools/AgentTool/forkSubagent.ts`
- `src/tools/AgentTool/agentMemory.ts`

### 团队协作
- `src/tools/TeamCreateTool/TeamCreateTool.ts`
- `src/tools/SendMessageTool/SendMessageTool.ts`
- `src/utils/teammateMailbox.ts`

### Worktree
- `src/tools/EnterWorktreeTool/EnterWorktreeTool.ts`
- `src/utils/worktree.ts`

---

## 💡 核心洞察

### Claude Code 的工程化优势

1. **Feature Flag 系统**: 30+ feature flags，灰度发布
2. **Zod 验证**: 所有工具输入输出强类型验证
3. **Analytics 埋点**: GrowthBook + Sentry 完整
4. **Hook 系统**: pre/post tool use hooks 可扩展
5. **Session Memory**: 完整的会话记忆管理
6. **Token Budget**: 精细的 token 预算追踪

### 可直接复用的模块

| 模块 | 复用难度 | 说明 |
|------|---------|------|
| 三层压缩 | 中 | 核心逻辑可直接移植 |
| Task V2 | 低 | 数据结构完整 |
| Worktree | 中 | Git 集成需要适配 |
| 后台任务 | 中 | 队列机制通用 |
| 团队邮箱 | 低 | 消息系统简单 |

---

## 📚 参考资料

- **源码位置**: `/home/xxh/claudecode源码(仅用于学习交流)/claude-code-main/`
- **OpenClaw 项目**: `/home/xxh/.clawith/`
- **Learn-Claude-Code**: https://github.com/shareAI-lab/learn-claude-code
- **原始教程**: https://mp.weixin.qq.com/s/WTD0TEKn0h_vjgNR1WGSxQ

---

**报告版本**: v1.0
**创建时间**: 2026-04-06
**状态**: 分析完成，等待实施
