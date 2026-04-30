# 🚀 OpenHarness 项目完善计划

**计划日期**: 2026-04-06
**目标项目**: `/home/xxh/claudecode源码(仅用于学习交流)/OpenHarness-main`
**参考资源**:
1. `Harness工程实现分析.md` - Claude Code 官方源码分析文档
2. `claude-code-main/` - Claude Code 官方 TypeScript 源码
3. `architecture-comparison-report.md` - 之前的架构对比分析报告

---

## 📋 一、完善目标总览

基于之前的对比分析，OpenHarness 在以下 **4 个核心模块** 存在显著不足：

| 优先级 | 模块 | 当前状态 | 目标状态 | 参考 |
|--------|------|---------|---------|------|
| **P0** | S06: 上下文压缩系统 | ⚠️ 部分实现（集成在引擎内部） | ✅ 独立完整的三层压缩模块 | Claude Code: `src/services/compact/` |
| **P0** | S07: 任务依赖系统 (DAG) | ⚠️ 部分实现（基础 CRUD，无依赖） | ✅ 完整的 DAG 任务编排 + 自动解锁 | Claude Code: `src/utils/tasks.ts` |
| **P1** | S10: 团队规矩（握手+审批） | ⚠️ 部分实现（基础停止，无握手） | ✅ 请求-响应握手协议 + 审批流 | Claude Code: `src/utils/swarm/teamHelpers.ts` + `permissionSync.ts` |
| **P1** | S11: 自治模式 | ❌ 未实现 | ✅ Worker 自主认领 + 空闲检测 + 自动关机 | Claude Code: `src/utils/swarm/inProcessRunner.ts` |

---

## 🔧 二、详细实施计划

### 模块 1: 上下文压缩系统 (S06) - P0 高优先级

#### 1.1 参考实现分析

**Claude Code 实现** (`src/services/compact/`)：
```
compact/
├── autoCompact.ts        # 自动压缩（token 超阈值触发）
├── microCompact.ts       # 微压缩（快速压缩旧工具输出）
├── compact.ts            # 核心压缩逻辑（LLM 摘要生成）
├── snipCompact.ts        # 历史裁剪（手动删除历史片段）
├── reactiveCompact.ts    # 响应式压缩（错误恢复时）
├── sessionMemoryCompact.ts  # 会话记忆压缩
├── grouping.ts           # 消息分组策略
└── postCompactCleanup.ts # 压缩后清理
```

**关键特性**:
- **多层阈值**: warning (20K) → error (20K) → auto-compact (13K) → blocking (3K)
- **熔断机制**: 连续失败 3 次后停止重试
- **Token 计算**: 基于模型上下文窗口动态调整
- **配置化**: 支持环境变量覆盖阈值

#### 1.2 OpenHarness 实施步骤

##### 步骤 1.1.1: 创建压缩模块目录结构

```bash
mkdir -p src/openharness/memory/compression/
```

**新建文件**:
- [ ] `src/openharness/memory/compression/__init__.py`
- [ ] `src/openharness/memory/compression/types.py` - 压缩类型定义
- [ ] `src/openharness/memory/compression/config.py` - 压缩配置（阈值、策略）
- [ ] `src/openharness/memory/compression/micro_compact.py` - 微压缩实现
- [ ] `src/openharness/memory/compression/auto_compact.py` - 自动压缩实现
- [ ] `src/openharness/memory/compression/snip_compact.py` - 历史裁剪实现
- [ ] `src/openharness/memory/compression/manager.py` - 压缩管理器（统一入口）

##### 步骤 1.1.2: 实现类型定义 (`types.py`)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class CompressionStrategy(Enum):
    MICRO = "micro"           # 快速替换旧工具输出为标记
    AUTO_SUMMARY = "auto"    # LLM 生成摘要替换
    SNIP = "snip"            # 手动裁剪历史片段
    REACTIVE = "reactive"    # 错误恢复时压缩

@dataclass
class CompressionConfig:
    """压缩配置"""
    enabled: bool = True
    
    # 阈值设置（token 数）
    warning_threshold_buffer: int = 20_000
    error_threshold_buffer: int = 20_000
    auto_compact_buffer: int = 13_000
    blocking_limit_buffer: int = 3_000
    
    # 策略控制
    max_consecutive_failures: int = 3  # 熔断阈值
    micro_compact_age_turns: int = 3   # 微压缩：替换超过 N 轮的工具输出
    
    # 摘要配置
    max_summary_tokens: int = 20_000   # LLM 摘要最大 token 数

@dataclass
class CompressionResult:
    """压缩结果"""
    success: bool
    strategy_used: CompressionStrategy
    tokens_before: int
    tokens_after: int
    messages_removed: int
    summary: Optional[str] = None
    error: Optional[str] = None

@dataclass
class CompressionState:
    """压缩状态追踪"""
    is_compacted: bool = False
    turn_counter: int = 0
    consecutive_failures: int = 0
    last_compaction_turn: int = 0
```

##### 步骤 1.1.3: 实现微压缩 (`micro_compact.py`)

**核心逻辑**:
```python
async def micro_compact(messages: list[Message], config: CompressionConfig) -> tuple[list[Message], int]:
    """
    微压缩：将超过 N 轮的工具结果替换为紧凑标记
    
    参考实现: Claude Code src/services/compact/microCompact.ts
    策略:
    1. 保留最近 config.micro_compact_age_turns 轮的消息完整
    2. 将更早轮次的 tool_result 替换为 "[Previous: used {tool_name}]"
    3. 返回压缩后的消息列表和释放的 token 数
    """
    pass
```

##### 步骤 1.1.4: 实现自动压缩 (`auto_compact.py`)

**核心逻辑**:
```python
async def auto_compact(
    messages: list[Message],
    system_prompt: str,
    api_client: ApiClient,
    config: CompressionConfig,
) -> CompressionResult:
    """
    自动压缩：当 token 数超过阈值时，使用 LLM 生成摘要
    
    参考实现: Claude Code src/services/compact/autoCompact.ts
    流程:
    1. 计算当前 token 使用量
    2. 如果超过 auto_compact_threshold:
       a. 将完整对话保存到磁盘（不丢失）
       b. 调用 LLM 生成摘要
       c. 用摘要替换所有历史消息
       d. 返回压缩结果
    3. 更新连续失败计数器（用于熔断）
    """
    pass
```

##### 步骤 1.1.5: 实现压缩管理器 (`manager.py`)

**统一入口**:
```python
class CompressionManager:
    """上下文压缩管理器"""
    
    def __init__(self, config: CompressionConfig):
        self._config = config
        self._state = CompressionState()
    
    async def maybe_compact(
        self,
        messages: list[Message],
        system_prompt: str,
        api_client: ApiClient,
        model: str,
    ) -> tuple[list[Message], CompressionResult]:
        """
        主入口：根据当前状态决定是否需要压缩
        
        执行顺序（参考 Claude Code query.ts 第 401-467 行）:
        1. Snip（如果启用）
        2. Microcompact
        3. Context Collapse（如果启用）
        4. Autocompact
        """
        # 1. Token 计算
        token_count = self._count_tokens(messages, system_prompt)
        
        # 2. 判断是否需要压缩
        threshold_state = self._calculate_threshold_state(token_count, model)
        
        # 3. 按优先级执行压缩策略
        if threshold_state.is_above_auto_compact_threshold:
            return await self._execute_auto_compact(...)
        
        if threshold_state.is_above_warning_threshold:
            return await self._execute_micro_compact(...)
        
        return messages, CompressionResult(success=False, ...)
```

##### 步骤 1.1.6: 集成到 QueryEngine

**修改文件**: `src/openharness/engine/query_engine.py`

```python
# 在 __init__ 中添加
from openharness.memory.compression.manager import CompressionManager

class QueryEngine:
    def __init__(self, ..., compression_config=None):
        ...
        self._compression_manager = CompressionManager(
            compression_config or CompressionConfig()
        )

# 在 submit_message 的循环中添加压缩调用
async def submit_message(self, prompt: str):
    while True:
        # === 新增：上下文压缩 ===
        compressed_messages, compaction_result = await self._compression_manager.maybe_compact(
            self._messages,
            self._system_prompt,
            self._api_client,
            self._model,
        )
        if compaction_result.success:
            self._messages = compressed_messages
        
        # 继续原有循环逻辑
        response = await api.stream(compressed_messages, tools)
        ...
```

---

### 模块 2: 任务依赖系统 (DAG) - P0 高优先级

#### 2.1 参考实现分析

**Claude Code 实现** (`src/utils/tasks.ts`):

**关键类型定义** (第 76-88 行):
```typescript
export const TaskSchema = lazySchema(() =>
  z.object({
    id: z.string(),
    subject: z.string(),
    description: z.string(),
    activeForm: z.string().optional(),     // 进行时形式（如 "Running tests"）
    owner: z.string().optional(),          // Agent ID
    status: TaskStatusSchema(),             // pending | in_progress | completed
    blocks: z.array(z.string()),           // 此任务阻塞的任务 ID 列表
    blockedBy: z.array(z.string()),        // 阻塞此任务的任务 ID 列表
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
)
```

**自动解锁机制**:
当一个任务完成时:
1. 扫描所有其他任务的 `blockedBy` 列表
2. 查找包含已完成任务 ID 的条目
3. 删除该 ID
4. 如果 `blockedBy` 变空 → 任务自动解锁（可执行）

**存储机制**:
- 每个任务一个 JSON 文件: `~/.claude/tasks/{taskListId}/{taskId}.json`
- 文件锁防止并发冲突
- 高水位标记 `.highwatermark` 防止 ID 重用

#### 2.2 OpenHarness 实施步骤

##### 步骤 2.1: 扩展任务类型定义

**修改文件**: `src/openharness/tasks/types.py`

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"

class TaskRecord(BaseModel):
    """扩展后的任务记录（支持 DAG 依赖）"""
    id: str
    type: str  # local_bash, local_agent, etc.
    status: TaskStatus = TaskStatus.PENDING
    
    # 基本信息
    subject: str                    # 任务标题（简短）
    description: str                # 详细描述
    active_form: Optional[str] = None  # 进行时形式（如 "Running tests"）
    
    # 所有者
    owner: Optional[str] = None     # Agent ID
    
    # ===== 新增：DAG 依赖字段 =====
    blocks: list[str] = []          # 此任务阻塞的任务 ID 列表
    blocked_by: list[str] = []      # 阻塞此任务的任务 ID 列表
    
    # 元数据
    metadata: dict[str, object] = {}
    progress: Optional[int] = None  # 0-100
    
    # 时间戳
    created_at: float
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    
    # 执行信息
    command: Optional[str] = None
    prompt: Optional[str] = None
    output_file: Optional[Path] = None
    return_code: Optional[int] = None
```

##### 步骤 2.2: 实现任务 DAG 管理

**新建文件**: `src/openharness/tasks/dag.py`

```python
"""
任务依赖图（DAG）管理

参考实现: Claude Code src/utils/tasks.ts
"""

from typing import Optional
from .types import TaskRecord, TaskStatus

class TaskDependencyGraph:
    """任务依赖图管理器"""
    
    def __init__(self, task_manager):
        self._task_manager = task_manager
    
    async def create_task_with_dependencies(
        self,
        subject: str,
        description: str,
        blocked_by: list[str] = None,  # 前置依赖任务 ID
        blocks: list[str] = None,      # 后续被阻塞任务 ID
        **kwargs
    ) -> TaskRecord:
        """
        创建带依赖关系的任务
        
        示例:
        ```python
        # 创建编译任务（无依赖）
        compile_task = await dag.create_task(
            subject="Compile project",
            description="Run make build",
        )
        
        # 创建测试任务（依赖编译完成）
        test_task = await dag.create_task(
            subject="Run tests",
            description="Execute test suite",
            blocked_by=[compile_task.id],  # 必须等编译完成
        )
        
        # 创建部署任务（依赖测试通过）
        deploy_task = await dag.create_task(
            subject="Deploy to staging",
            blocked_by=[test_task.id],
        )
        ```
        """
        task = await self._task_manager.create_shell_task(
            description=description,
            **kwargs
        )
        
        # 设置依赖关系
        task.blocked_by = blocked_by or []
        task.blocks = blocks or []
        
        # 如果有前置依赖且未完成，状态设为 pending
        if task.blocked_by:
            for dep_id in task.blocked_by:
                dep_task = self._task_manager.get_task(dep_id)
                if dep_task and dep_task.status != TaskStatus.COMPLETED:
                    task.status = TaskStatus.PENDING
        
        return task
    
    async def complete_task(self, task_id: str) -> TaskRecord:
        """
       完成任务并自动解锁后续任务
        
        流程:
        1. 将任务状态设为 completed
        2. 扫描所有任务的 blockedBy 列表
        3. 删除已完成的任务 ID
        4. 如果某任务的 blockedBy 变空 → 自动解锁
        """
        task = self._task_manager.require_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.ended_at = time.time()
        
        # 自动解锁被此任务阻塞的其他任务
        unlocked_tasks = []
        all_tasks = self._task_manager.list_tasks()
        for t in all_tasks:
            if task_id in t.blocked_by:
                t.blocked_by.remove(task_id)
                
                # 如果没有其他依赖了，自动解锁
                if not t.blocked_by and t.status == TaskStatus.PENDING:
                    t.status = TaskStatus.PENDING  # 可改为 READY 或保持 PENDING
                    unlocked_tasks.append(t.id)
        
        return task, unlocked_tasks
    
    def get_executable_tasks(self) -> list[TaskRecord]:
        """
        获取当前可执行的任务（无未完成的依赖）
        
        条件:
        - status == pending (或 in_progress)
        - blockedBy 为空，或所有依赖都已完成
        """
        executable = []
        for task in self._task_manager.list_tasks():
            if task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                # 检查依赖是否都已完成
                deps_met = all(
                    self._task_manager.get_task(dep_id).status == TaskStatus.COMPLETED
                    for dep_id in task.blocked_by
                    if self._task_manager.get_task(dep_id)
                )
                if deps_met and not task.blocked_by:
                    executable.append(task)
        return executable
    
    def visualize_dag(self) -> str:
        """生成 DAG 的文本可视化（类似 Mermaid）"""
        lines = ["graph LR"]
        tasks = self._task_manager.list_tasks()
        for task in tasks:
            for dep_id in task.blocked_by:
                lines.append(f"  {dep_id} --> {task.id}[{task.subject}]")
        return "\n".join(lines)
```

##### 步骤 2.3: 更新任务创建工具

**修改文件**: `src/openharness/tools/task_create_tool.py`

```python
class TaskCreateToolInput(BaseModel):
    type: str = Field(default="local_bash")
    description: str = Field(description="Short task description")
    subject: str = Field(default="", description="Task title (short)")
    command: str | None = Field(default=None)
    prompt: str | None = Field(default=None)
    model: str | None = Field(default=None)
    
    # ===== 新增：依赖字段 =====
    blocked_by: list[str] = Field(
        default_factory=list,
        description="Task IDs that must complete before this task can start"
    )
    blocks: list[str] = Field(
        default_factory=list,
        description="Task IDs that are blocked by this task"
    )

class TaskCreateTool(BaseTool):
    name = "task_create"
    description = "Create a background task with optional dependencies"
    input_model = TaskCreateToolInput
    
    async def execute(self, arguments, context):
        manager = get_task_manager()
        dag = TaskDependencyGraph(manager)
        
        # 使用 DAG 创建任务（支持依赖关系）
        task = await dag.create_task_with_dependencies(
            subject=arguments.subject or arguments.description[:50],
            description=arguments.description,
            blocked_by=arguments.blocked_by,
            blocks=arguments.blocks,
            command=arguments.command,
            prompt=arguments.prompt,
            cwd=context.cwd,
        )
        
        status_msg = f"Created task {task.id}"
        if task.blocked_by:
            status_msg += f" (blocked by: {', '.join(task.blocked_by)})"
        
        return ToolResult(output=status_msg)
```

##### 步骤 2.4: 添加任务依赖查询工具（可选）

**新建文件**: `src/openharness/tools/task_deps_tool.py`

```python
class TaskDepsTool(BaseTool):
    """查看任务的依赖关系"""
    name = "task_deps"
    description = "Show task dependency graph and executable tasks"
    
    async def execute(self, arguments, context):
        manager = get_task_manager()
        dag = TaskDependencyGraph(manager)
        
        # 可执行任务
        executable = dag.get_executable_tasks()
        
        # DAG 可视化
        viz = dag.visualize_dag()
        
        result = f"## Executable Tasks ({len(executable)})\n"
        for task in executable:
            result += f"- [{task.id}] {task.subject}\n"
        
        result += f"\n## Dependency Graph\n```mermaid\n{viz}\n```"
        
        return ToolResult(output=result)
```

---

### 模块 3: 团队规矩（握手+审批）- P1 中优先级

#### 3.1 参考实现分析

**Claude Code 实现**:

**审批流程** (`src/utils/swarm/permissionSync.ts`):
```typescript
// Worker 发送权限请求给 Leader
export async function sendPermissionRequestViaMailbox(
  request: PermissionRequest,
  teammateIdentity: TeammateIdentity,
): Promise<void> {
  const mailboxMsg: TeammateMessage = {
    from: teammateIdentity.agentId,
    text: '',
    timestamp: new Date().toISOString(),
    read: false,
    type: 'permission-request',
    permissionRequest: request,
  }
  await writeToMailbox(getLeaderMailboxPath(), mailboxMsg)
}

// Leader 处理并回复
export function processMailboxPermissionResponse(
  msg: TeammateMessage,
): PermissionResponse | null {
  if (msg.type !== 'permission-response') return null
  return msg.permissionResponse
}
```

**关机握手** (`src/utils/swarm/teamHelpers.ts`):
- Leader 发送 shutdown request（带 request_id）
- Worker 收到后收尾工作，然后回复同意（引用同一个 request_id）
- Leader 收到确认后才真正终止

#### 3.2 OpenHarness 实施步骤

##### 步骤 3.1: 定义请求-响应协议

**新建文件**: `src/openharness/coordinator/protocol.py`

```python
"""
团队协调协议：请求-响应 + 唯一 ID 模式

参考实现: Claude Code src/utils/swarm/teamHelpers.ts + permissionSync.ts
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid

class MessageType(Enum):
    # 通用消息
    TEXT = "text"
    
    # 协调协议
    SHUTDOWN_REQUEST = "shutdown_request"      # 关机请求
    SHUTDOWN_RESPONSE = "shutdown_response"    # 关机响应
    PERMISSION_REQUEST = "permission_request"  # 权限请求
    PERMISSION_RESPONSE = "permission_response"  # 权限响应
    
    # 任务相关
    TASK_CLAIMED = "task_claimed"              # 任务被认领
    TASK_COMPLETED = "task_completed"          # 任务完成

@dataclass
class CoordinationMessage:
    """协调消息（带唯一 ID）"""
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    message_type: MessageType = MessageType.TEXT
    from_agent: str = ""
    to_agent: str = ""  # 空 = 广播
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    # 用于请求-响应匹配
    reply_to: Optional[str] = None  # 引用原始请求的 message_id
    
    # 状态
    read: bool = False

@dataclass
class ShutdownRequest:
    """关机请求"""
    reason: str = "Leader requested shutdown"
    graceful: bool = True  # 是否优雅关闭（允许收尾）

@dataclass
class ShutdownResponse:
    """关机响应"""
    accepted: bool
    task_id: str  # 对应的原始请求 ID
    message: str = ""

@dataclass
class PermissionRequest:
    """权限请求（Worker → Leader）"""
    tool_name: str
    tool_input: dict
    reason: str = ""
    timeout: float = 30.0  # 超时时间（秒）

@dataclass
class PermissionResponse:
    """权限响应（Leader → Worker）"""
    granted: bool
    request_id: str  # 对应的原始请求 ID
    reason: str = ""
```

##### 步骤 3.2: 实现协调协议处理器

**新建文件**: `src/openharness/coordinator/handler.py`

```python
"""
协调协议处理器

实现:
1. 关机握手流程
2. 权限审批流程
"""

class CoordinationProtocolHandler:
    """处理团队协调协议"""
    
    def __init__(self, team_registry, task_manager):
        self._registry = team_registry
        self._tasks = task_manager
        self._pending_requests: dict[str, asyncio.Future] = {}  # request_id → Future
    
    async def send_shutdown_request(
        self, target_agent: str, reason: str = "", timeout: float = 30.0
    ) -> bool:
        """
        发送关机请求（Leader → Worker）
        
        流程:
        1. 创建 ShutdownRequest 带 request_id
        2. 发送到目标 Agent 的收件箱
        3. 等待响应（带超时）
        4. 收到确认后才真正终止
        """
        request = CoordinationMessage(
            message_type=MessageType.SHUTDOWN_REQUEST,
            from_agent="coordinator",
            to_agent=target_agent,
            payload={"reason": reason},
        )
        
        # 创建 Future 等待响应
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request.message_id] = future
        
        # 发送请求
        await self._send_to_mailbox(target_agent, request)
        
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response.payload.get("accepted", False)
        except asyncio.TimeoutError:
            # 超时强制终止
            return False
    
    async def handle_shutdown_request(self, message: CoordinationMessage) -> CoordinationMessage:
        """
        Worker 处理关机请求
        
        流程:
        1. 收到请求
        2. 执行收尾工作（保存状态、清理资源）
        3. 回复确认（引用原始 request_id）
        """
        # TODO: 执行收尾工作
        # 1. 保存当前工作状态
        # 2. 清理临时文件
        # 3. 通知正在处理的任务
        
        response = CoordinationMessage(
            message_type=MessageType.SHUTDOWN_RESPONSE,
            reply_to=message.message_id,
            payload={"accepted": True, "message": "Shutdown acknowledged"},
        )
        
        return response
    
    async def request_permission(
        self, tool_name: str, tool_input: dict, timeout: float = 30.0
    ) -> bool:
        """
        Worker 请求权限（Worker → Leader）
        
        用途: Worker 需要执行危险操作时，向 Leader 申请审批
        """
        request = CoordinationMessage(
            message_type=MessageType.PERMISSION_REQUEST,
            payload={
                "tool_name": tool_name,
                "tool_input": tool_input,
            },
        )
        
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request.message_id] = future
        
        await self._send_to_mailbox("coordinator", request)
        
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response.payload.get("granted", False)
        except asyncio.TimeoutError:
            return False
    
    async def handle_permission_response(self, message: CoordinationMessage):
        """Leader 处理权限响应（实际由 UI 触发）"""
        request_id = message.reply_to
        if request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
            if not future.done():
                future.set_result(message)
```

##### 步骤 3.3: 更新 Team Delete 工具

**修改文件**: `src/openharness/tools/team_delete_tool.py`

```python
class TeamDeleteTool(BaseTool):
    """删除团队（带关机握手）"""
    name = "team_delete"
    description = "Delete a team with graceful shutdown handshake"
    
    async def execute(self, arguments, context):
        protocol = CoordinationProtocolHandler(get_team_registry(), get_task_manager())
        
        team = get_team_registry()._require_team(arguments.name)
        
        # 向每个队友发送关机请求
        shutdown_results = []
        for agent_id in team.agents:
            success = await protocol.send_shutdown_request(
                target_agent=agent_id,
                reason=f"Team {arguments.name} is being deleted",
            )
            shutdown_results.append((agent_id, success))
        
        # 所有队友确认后，删除团队
        get_team_registry().delete_team(arguments.name)
        
        result = f"Team {arguments.name} deleted.\nShutdown results:\n"
        for agent_id, success in shutdown_results:
            status = "✓" if success else "✗ (timeout)"
            result += f"  {agent_id}: {status}\n"
        
        return ToolResult(output=result)
```

---

### 模块 4: 自治模式 (S11) - P1 中优先级

#### 4.1 参考实现分析

**Claude Code 实现** (`src/utils/swarm/inProcessRunner.ts`):

**核心特性**:
1. **空闲检测**:
   - 工作阶段：每轮检查收件箱
   - 空闲阶段：每 5 秒轮询收件箱 + 任务看板
   
2. **自动认领**:
   - 调用 `claimTask()` 认领可用的 pending 任务
   - 认领后进入工作状态

3. **自动关机**:
   - 持续 60 秒无活 → 自动关机
   - 释放资源

4. **身份注入**:
   - 上下文过短时重新注入身份信息
   - 防止忘记自己是谁

**关键代码片段** (第 87-98 行):
```typescript
// 从 tasks.ts 导入
import { claimTask, listTasks, updateTask } from '../tasks.js'

// 从 mailbox 导入
import {
  createIdleNotification,
  readMailbox,
  writeToMailbox,
} from '../teammateMailbox.js'
```

#### 4.2 OpenHarness 实施步骤

##### 步骤 4.1: 创建自治 Worker 模块

**新建文件**: `src/openharness/coordinator/autonomous_worker.py`

```python
"""
自治 Worker 模块

参考实现: Claude Code src/utils/swarm/inProcessRunner.ts

功能:
1. 空闲检测与自动认领任务
2. 定期轮询收件箱和任务看板
3. 超时自动关机
4. 身份信息注入
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass

@dataclass
class AutonomousWorkerConfig:
    """自治 Worker 配置"""
    agent_id: str
    team: str = "default"
    
    # 轮询间隔
    idle_poll_interval_sec: float = 5.0      # 空闲时轮询间隔
    work_check_interval_sec: float = 1.0     # 工作时检查间隔
    
    # 超时设置
    max_idle_time_sec: float = 60.0          # 最大空闲时间（超时自动关机）
    
    # 身份注入
    min_context_length: int = 500           # 最小上下文长度（低于则重新注入身份）

class AutonomousWorker:
    """自治 Worker：可自主认领任务、自动管理生命周期"""
    
    def __init__(
        self,
        config: AutonomousWorkerConfig,
        agent_loop,  # Agent 的主循环函数
        task_manager,
        team_registry,
    ):
        self._config = config
        self._agent_loop = agent_loop
        self._tasks = task_manager
        self._team = team_registry
        
        self._state = "idle"  # idle | working | shutting_down
        self._last_activity_time = time.time()
        self._current_task_id: Optional[str] = None
    
    async def run(self):
        """
        Worker 主循环
        
        状态机:
        idle → working (认领到任务)
        working → idle (任务完成)
        idle → shutting_down (超时无任务)
        shutting_down → terminated
        """
        while self._state != "shutting_down":
            if self._state == "idle":
                await self._idle_loop()
            elif self._state == "working":
                await self._work_loop()
            
            # 检查超时
            idle_duration = time.time() - self._last_activity_time
            if idle_duration > self._config.max_idle_time_sec:
                print(f"[{self._config.agent_id}] Idle timeout, shutting down...")
                self._state = "shutting_down"
        
        # 清理
        await self._cleanup()
    
    async def _idle_loop(self):
        """
        空闲循环：轮询收件箱和任务看板
        
        参考 Claude Code inProcessRunner.ts 的空闲检测逻辑
        """
        while self._state == "idle":
            # 1. 检查收件箱新消息
            mailbox = self._read_mailbox()
            if mailbox:
                self._last_activity_time = time.time()
                self._state = "working"
                return
            
            # 2. 检查任务看板是否有可认领的任务
            claimable = self._get_claimable_tasks()
            if claimable:
                # 自动认领第一个可用任务
                task = await self._claim_task(claimable[0].id)
                if task:
                    self._current_task_id = task.id
                    self._last_activity_time = time.time()
                    self._state = "working"
                    return
            
            # 3. 等待下一轮轮询
            await asyncio.sleep(self._config.idle_poll_interval_sec)
    
    async def _work_loop(self):
        """
        工作循环：执行任务
        """
        task = self._tasks.get_task(self._current_task_id)
        if not task:
            self._state = "idle"
            return
        
        # 更新任务状态
        await self._tasks.update_task(
            self._current_task_id,
            status="in_progress",
            status_note=f"{self._config.agent_id} is working on this",
        )
        
        # 执行任务（调用 Agent 循环）
        try:
            async for event in self._agent_loop(task.prompt or task.description):
                # 处理事件...
                self._last_activity_time = time.time()
            
            # 任务完成
            await self._tasks.update_task(
                self._current_task_id,
                status="completed",
            )
            
            # 触发依赖解锁（如果使用了 DAG）
            # dag.complete_task(self._current_task_id)
            
        except Exception as e:
            await self._tasks.update_task(
                self._current_task_id,
                status="failed",
                status_note=str(e),
            )
        finally:
            self._current_task_id = None
            self._state = "idle"
    
    def _get_claimable_tasks(self) -> list:
        """获取可认领的任务（pending 且无未完成依赖）"""
        all_tasks = self._tasks.list_tasks(status="pending")
        claimable = []
        for task in all_tasks:
            # 检查是否有未完成的依赖
            # （如果实现了 DAG 模块）
            deps_met = True  # TODO: 调用 dag.get_executable_tasks()
            if deps_met and not task.owner:
                claimable.append(task)
        return claimable
    
    async def _claim_task(self, task_id: str):
        """认领任务"""
        task = self._tasks.get_task(task_id)
        if task and not task.owner:
            await self._tasks.update_task(
                task_id,
                # owner=self._config.agent_id,  # 如果 TaskRecord 支持 owner 字段
            )
            return task
        return None
    
    def _read_mailbox(self) -> list:
        """读取收件箱新消息"""
        # TODO: 实现邮箱读取
        return []
    
    async def _cleanup(self):
        """清理资源"""
        print(f"[{self._config.agent_id}] Worker shut down cleanly")
```

##### 步骤 4.2: 集成到 Coordinator

**修改文件**: `src/openharness/coordinator/coordinator_mode.py`

在系统提示中添加自治模式说明：

```python
def get_worker_system_prompt_addendum() -> str:
    """
    Worker 自治行为说明
    
    注入到 Worker 的系统提示中
    """
    return """
## Autonomous Behavior (Self-Governance)

You are an autonomous worker with the following behaviors:

### Task Claiming
- When idle, check the task board every 5 seconds for claimable tasks
- Automatically claim available tasks that match your capabilities
- After claiming, enter working state and execute the task

### Idle Detection
- If no new messages or claimable tasks for 60 seconds, shut down automatically
- This conserves resources when there's no work to do

### Identity Reinforcement
- If your context becomes too short, your identity will be re-injected
- You always know who you are and what team you belong to

### Communication
- Check inbox at the start of each work cycle
- Send completion notifications when done
- Request permission for sensitive operations via the coordination protocol
"""
```

##### 步骤 4.3: 创建 Worker 启动工具（可选）

**新建文件**: `src/openharness/tools/worker_spawn_tool.py`

```python
class WorkerSpawnTool(BaseTool):
    """启动自治 Worker"""
    name = "worker_spawn"
    description = "Spawn an autonomous worker that claims tasks automatically"
    
    async def execute(self, arguments, context):
        config = AutonomousWorkerConfig(
            agent_id=f"worker-{uuid.uuid4().hex[:6]}",
            team=arguments.team or "default",
        )
        
        worker = AutonomousWorker(
            config=config,
            agent_loop=self._create_agent_loop(...),
            task_manager=get_task_manager(),
            team_registry=get_team_registry(),
        )
        
        # 后台启动 Worker
        asyncio.create_task(worker.run())
        
        return ToolResult(
            output=f"Spawned autonomous worker {config.agent_id}"
        )
```

---

## 📊 三、实施优先级和时间估算

### Phase 1: 核心基础设施（P0）- 预计 3-5 天

| 序号 | 任务 | 预估时间 | 依赖 |
|------|------|---------|------|
| 1.1 | 创建压缩模块目录结构 + 类型定义 | 0.5 天 | 无 |
| 1.2 | 实现微压缩 (micro_compact.py) | 0.5 天 | 1.1 |
| 1.3 | 实现自动压缩 (auto_compact.py) | 1 天 | 1.1 |
| 1.4 | 实现压缩管理器 (manager.py) | 0.5 天 | 1.2, 1.3 |
| 1.5 | 集成到 QueryEngine | 0.5 天 | 1.4 |
| 2.1 | 扩展 TaskRecord 类型（添加 DAG 字段） | 0.5 天 | 无 |
| 2.2 | 实现 TaskDependencyGraph | 1 天 | 2.1 |
| 2.3 | 更新 TaskCreateTool | 0.5 天 | 2.2 |
| 2.4 | 添加 TaskDepsTool（可选） | 0.5 天 | 2.2 |

**Phase 1 小计**: ~6 天

### Phase 2: 团队协调增强（P1）- 预计 2-3 天

| 序号 | 任务 | 预估时间 | 依赖 |
|------|------|---------|------|
| 3.1 | 定义协调协议 (protocol.py) | 0.5 天 | 无 |
| 3.2 | 实现协议处理器 (handler.py) | 1 天 | 3.1 |
| 3.3 | 更新 TeamDeleteTool（握手） | 0.5 天 | 3.2 |
| 4.1 | 创建自治 Worker 模块 | 1 天 | 无 |
| 4.2 | 集成到 Coordinator | 0.5 天 | 4.1 |

**Phase 2 小计**: ~3.5 天

### Phase 3: 测试和文档（P2）- 预计 2 天

| 序号 | 任务 | 预估时间 | 依赖 |
|------|------|---------|------|
| 5.1 | 编写单元测试（压缩 + DAG） | 1 天 | Phase 1, 2 |
| 5.2 | 编写 E2E 测试（团队协调场景） | 0.5 天 | Phase 2 |
| 5.3 | 更新 README 和文档 | 0.5 天 | 全部 |

**总计**: ~11.5 天（按全职计算）

---

## 🧪 四、测试计划

### 单元测试

```python
# tests/test_compression/test_micro_compact.py
class TestMicroCompact:
    async def test_replace_old_tool_results(self):
        """验证微压缩能正确替换旧工具输出"""
        pass
    
    async def test_keep_recent_messages_intact(self):
        """验证最近 N 轮消息保持完整"""
        pass
    
    async def test_token_count_decreases(self):
        """验证压缩后 token 数减少"""
        pass

# tests/test_tasks/test_dag.py
class TestTaskDependencyGraph:
    async def test_create_task_with_dependencies(self):
        """验证创建带依赖的任务"""
        pass
    
    async def test_auto_unlock_on_completion(self):
        """验证任务完成后自动解锁后续任务"""
        pass
    
    async def test_get_executable_tasks(self):
        """验证获取可执行任务列表"""
        pass
    
    async def test_circular_dependency_detection(self):
        """验证循环依赖检测（应抛出异常）"""
        pass

# tests/test_coordinator/test_protocol.py
class TestCoordinationProtocol:
    async def test_shutdown_handshake_success(self):
        """验证关机握手成功流程"""
        pass
    
    async def test_shutdown_timeout(self):
        """验证关机超时处理"""
        pass
    
    async def test_permission_request_flow(self):
        """验证权限请求-响应流程"""
        pass

# tests/test_coordinator/test_autonomous_worker.py
class TestAutonomousWorker:
    async def test_auto_claim_task(self):
        """验证 Worker 自动认领任务"""
        pass
    
    async def test_idle_timeout_shutdown(self):
        """验证空闲超时自动关机"""
        pass
    
    async def test_mailbox_triggers_work(self):
        """验证收到消息后从空闲转为工作"""
        pass
```

### E2E 测试场景

```yaml
# scripts/test_harness_enhancements.py

Scenario 1: Context Compression
  Given: A long conversation with 100+ tool calls
  When: Token count exceeds threshold
  Then: Auto-compaction triggers and reduces context size
  And: Conversation continues without error

Scenario 2: Task Dependencies
  Given: Tasks A, B, C where C depends on A and B
  When: A completes
  Then: C remains blocked (still waiting for B)
  When: B completes
  Then: C becomes unblocked and executable

Scenario 3: Graceful Shutdown
  Given: A running worker in a team
  When: Leader sends shutdown request
  Then: Worker finishes current task
  And: Worker responds with acknowledgment
  And: Leader then terminates the worker

Scenario 4: Autonomous Task Claiming
  Given: An idle worker and a pending task
  When: 5 seconds pass (poll interval)
  Then: Worker claims the task automatically
  And: Worker enters working state
```

---

## 📝 五、代码规范要求

### 遵循现有 OpenHarness 风格

1. **类型安全**: 使用 Pydantic 进行输入验证（参考现有 tools）
2. **异步编程**: 全面使用 async/await（参考 BackgroundTaskManager）
3. **单例模式**: Manager 类使用单例（参考 get_task_manager()）
4. **错误处理**: 明确的异常类型和错误消息
5. **日志记录**: 使用 Python logging 模块
6. **配置外部化**: 支持环境变量和配置文件覆盖

### 文档要求

1. **Docstring**: 所有公共类和方法必须有中文 Docstring
2. **类型注解**: 完整的类型提示（Python 3.10+ syntax）
3. **注释**: 关键算法逻辑添加行内注释（中文）
4. **示例**: 复杂用法提供示例代码

---

## ✅ 六、验收标准

### 功能完整性

- [ ] S06: 三层压缩全部实现并通过测试
- [ ] S07: 任务 DAG 依赖 + 自动解锁正常工作
- [ ] S10: 关机握手 + 权限审批流程完整
- [ ] S11: Worker 可自主认领任务并自动管理生命周期

### 质量指标

- [ ] 新增代码测试覆盖率 ≥ 80%
- [ ] 无现有测试回归（114 个测试仍通过）
- [ ] 代码符合 flake8/black/mypy 检查
- [ ] 性能无明显退化（压缩操作 < 100ms）

### 兼容性

- [ ] 向后兼容现有 API（不破坏现有工具）
- [ ] 配置项可选（默认值合理）
- [ ] 新增功能可通过 feature flag 禁用

---

## 🎯 七、成功愿景

完成本计划后，OpenHarness 将成为**首个完整实现文章描述的全部 12 个章节的开源项目**：

| 章节 | 完善前 | 完善后 |
|------|--------|--------|
| S01-S05 | ✅ 已实现 | ✅ 保持不变 |
| **S06** | ⚠️ 部分 | **✅ 完整三层压缩** |
| **S07** | ⚠️ 部分 | **✅ 完整 DAG + 自动解锁** |
| S08-S09 | ✅ 已实现 | ✅ 保持不变 |
| **S10** | ⚠️ 部分 | **✅ 握手 + 审批** |
| **S11** | ❌ 未实现 | **✅ 自治 Worker** |
| S12 | ✅ 已实现 | ✅ 保持不变 |

**最终评分预期**: 90.8 → **96-98 / 100**

---

**计划版本**: v1.0
**最后更新**: 2026-04-06
**负责人**: AI Assistant (based on analysis)
