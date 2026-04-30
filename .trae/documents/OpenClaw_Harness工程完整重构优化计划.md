# OpenClaw - Harness 工程完整重构优化计划

## 📋 文档信息

- **创建时间**: 2026-04-06
- **优化对象**: OpenClaw 项目 (`/home/xxh/.clawith/`)
- **参考源码**: Claude Code Best V2 (`/home/xxh/claudecode源码(仅用于学习交流)/claude-code-main/`)
- **对比基准**: Learn-Claude-Code 12章节 Harness 工程教程

---

## 🎯 优化策略总览

### 原则
1. **参考但不照搬**: 借鉴 Claude Code 的工程化思想，保持 OpenClaw 的独特架构
2. **渐进式重构**: 先优化已有功能，再添加新功能
3. **保持兼容性**: 重构过程中不破坏现有功能
4. **数据驱动**: 基于 Claude Code 的生产验证方案

---

## 📊 现有功能分析与优化优先级

### 第一部分：已有功能的重构优化

| 功能模块 | 现有实现 | Claude Code 实现 | 优化优先级 | 预计收益 |
|---------|---------|------------------|-----------|---------|
| **S01: 主循环** | ✅ 已有 | ✅ 完整（1700+行） | 🟡 中 | 稳定性提升 |
| **S02: 工具系统** | ✅ 已有 | ✅ 完整（类型安全） | 🔴 高 | 可维护性大幅提升 |
| **S03: Todo 清单** | ⚠️ 基础版 | ✅ V1+V2（依赖图） | 🔴 高 | 任务管理质的飞跃 |
| **S04: 子智能体** | ✅ 已有 | ✅ 完整（多模式） | 🟡 中 | 功能增强 |
| **S05: 技能加载** | ✅ 已有 | ✅ 完整（远程搜索） | 🟡 中 | 性能优化 |
| **S09: 多Agent协作** | ✅ 已有 | ✅ 完整（团队系统） | 🟡 中 | 协作能力增强 |

### 第二部分：新增功能

| 功能模块 | 现有实现 | Claude Code 实现 | 优先级 | 预计收益 |
|---------|---------|------------------|--------|---------|
| **S06: 三层压缩** | ❌ 缺失 | ✅ 生产级（20+文件） | 🔴 P0 | 解决长对话致命问题 |
| **S07: 任务依赖图** | ⚠️ 基础 | ✅ Task V2 完整 | 🟠 P1 | 任务管理智能化 |
| **S08: 后台任务** | ❌ 缺失 | ✅ 完整 | 🟡 P1 | 效率大幅提升 |
| **S10: 通信协议** | ⚠️ 基础 | ⚠️ 部分实现 | 🟢 P2 | 可靠性提升 |
| **S11: 自治认领** | ⚠️ 基础 | ⚠️ 部分实现 | 🟢 P2 | 自动化增强 |
| **S12: Worktree 隔离** | ❌ 缺失 | ✅ 完整 | 🟡 P1 | 协作无冲突 |

---

## 🏗️ Phase 0: 基础设施重构（1周）

### 0.1 工具系统重构

#### 现状分析
- **OpenClaw**: 工具通过 SKILL.md 定义，Python 脚本实现
- **Claude Code**: TypeScript 强类型，Zod 验证，统一 Tool 接口

#### 优化方案
**保持 OpenClaw 架构不变，增强工程化**：

1. **添加输入输出验证**
   - 参考 `claude-code-main/src/tools/TodoWriteTool/TodoWriteTool.ts` 的 Zod schema
   - 为现有工具添加 JSON Schema 验证
   - 在工具执行前验证输入

2. **统一工具接口**
   - 定义标准的 Tool 基类/协议
   - 统一的错误处理机制
   - 标准的工具结果格式

3. **工具注册系统**
   - 参考 `claude-code-main/src/tools.ts`
   - 创建工具注册表
   - 支持工具的动态加载/卸载

#### 实施文件
```
参考:
- claude-code-main/src/Tool.ts (Tool 接口定义)
- claude-code-main/src/tools.ts (工具注册表)
- claude-code-main/src/tools/TodoWriteTool/TodoWriteTool.ts (完整示例)

目标:
- OpenClaw/core/tool_protocol.py (新增)
- OpenClaw/core/tool_registry.py (新增)
- OpenClaw/core/tool_validator.py (新增)
```

---

### 0.2 状态管理重构

#### 现状分析
- **OpenClaw**: 分散的 JSON 文件（todo.json, tasks.json, state.json）
- **Claude Code**: Zustand-style 集中式状态管理，sessionStorage

#### 优化方案
1. **统一状态存储**
   - 创建集中式 StateManager
   - 原子化状态更新
   - 状态变更事件订阅

2. **持久化层优化**
   - 参考 `claude-code-main/src/utils/sessionStorage.ts`
   - 原子性文件写入（防止损坏）
   - 状态快照机制

3. **状态迁移支持**
   - 版本化状态格式
   - 自动迁移旧版本数据

#### 实施文件
```
参考:
- claude-code-main/src/state/AppState.tsx
- claude-code-main/src/state/store.ts
- claude-code-main/src/utils/sessionStorage.ts

目标:
- OpenClaw/core/state_manager.py (重构)
- OpenClaw/core/state_migrations.py (新增)
```

---

## 🏗️ Phase 1: 核心功能增强（1-2周）- 🔴 高优先级

### 1.1 S06: 三层上下文压缩系统（P0 - 必须）

#### 问题诊断
- **现状**: 无压缩机制，长对话必爆
- **影响**: 生产环境致命问题，无法处理复杂任务
- **参考**: Claude Code 20+ 文件的完整实现

#### 架构设计

```
OpenClaw/compression/
├── __init__.py
├── core.py                    # 压缩主引擎
├── token_counter.py           # Token 计数（复用 tiktoken）
├── thresholds.py              # 阈值配置
├── micro_compact.py           # 第一层：微压缩
├── auto_compact.py            # 第二层：自动压缩
├── manual_compact.py          # 第三层：手动压缩
├── storage.py                 # 历史消息存储
└── prompts.py                 # 压缩提示词
```

#### 详细实现计划

##### Step 1: Token 计数模块
**文件**: `OpenClaw/compression/token_counter.py`

```python
# 参考: claude-code-main/src/utils/tokens.ts

import tiktoken

class TokenCounter:
    def __init__(self, model: str = "gpt-4"):
        self.encoder = tiktoken.encoding_for_model(model)
    
    def count(self, text: str) -> int:
        return len(self.encoder.encode(text))
    
    def count_messages(self, messages: list) -> int:
        total = 0
        for msg in messages:
            total += self.count(str(msg.get('content', '')))
        return total
```

##### Step 2: 阈值配置
**文件**: `OpenClaw/compression/thresholds.py`

```python
# 参考: claude-code-main/src/services/compact/autoCompact.ts

@dataclass
class CompressionThresholds:
    # 保留给输出的 token
    MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20000
    
    # 各层阈值（基于 Claude Code 的值）
    AUTOCOMPACT_BUFFER_TOKENS = 13000
    WARNING_THRESHOLD_BUFFER_TOKENS = 20000
    ERROR_THRESHOLD_BUFFER_TOKENS = 20000
    MANUAL_COMPACT_BUFFER_TOKENS = 3000
    
    # 上下文窗口（按模型）
    CONTEXT_WINDOWS = {
        'gpt-4': 8192,
        'gpt-4-turbo': 128000,
        'claude-3-opus': 200000,
        'claude-3-sonnet': 200000,
    }
    
    def get_effective_context_window(self, model: str) -> int:
        base = self.CONTEXT_WINDOWS.get(model, 8192)
        return base - self.MAX_OUTPUT_TOKENS_FOR_SUMMARY
    
    def get_auto_compact_threshold(self, model: str) -> int:
        return self.get_effective_context_window(model) - self.AUTOCOMPACT_BUFFER_TOKENS
```

##### Step 3: 微压缩（第一层）
**文件**: `OpenClaw/compression/micro_compact.py`

```python
# 参考: claude-code-main/src/services/compact/microCompact.ts

class MicroCompactor:
    """
    第一层压缩：最近几轮保持完整，旧的工具返回只留标记
    
    示例:
    [Previous: used read_file on "src/main.py"]
    [Previous: used bash with "ls -la"]
    """
    
    def __init__(self, keep_full_turns: int = 3):
        self.keep_full_turns = keep_full_turns
    
    def compact(self, messages: list) -> list:
        if len(messages) <= self.keep_full_turns * 2:
            return messages
        
        # 保留最后 N 轮完整
        cutoff = len(messages) - self.keep_full_turns * 2
        
        # 对旧消息进行标记化
        result = []
        for i, msg in enumerate(messages):
            if i >= cutoff:
                result.append(msg)
            else:
                result.append(self._compact_message(msg))
        
        return result
    
    def _compact_message(self, msg: dict) -> dict:
        # 工具结果标记化
        if msg.get('role') == 'user' and 'tool_result' in str(msg.get('content', '')):
            return self._compact_tool_result(msg)
        return msg
    
    def _compact_tool_result(self, msg: dict) -> dict:
        # 提取工具名称，生成标记
        content = str(msg.get('content', ''))
        tool_name = self._extract_tool_name(content)
        return {
            **msg,
            'content': f"[Previous: used {tool_name}]"
        }
```

##### Step 4: 自动压缩（第二层）
**文件**: `OpenClaw/compression/auto_compact.py`

```python
# 参考: claude-code-main/src/services/compact/autoCompact.ts
#       claude-code-main/src/services/compact/compact.ts

class AutoCompactor:
    """
    第二层压缩：Token 超阈值时触发模型摘要
    
    流程:
    1. 检测 Token 用量超过阈值
    2. 调用模型生成对话摘要
    3. 用摘要替换历史消息
    4. 保留最近几轮完整
    5. 所有历史存入磁盘（不丢失）
    """
    
    def __init__(
        self,
        thresholds: CompressionThresholds,
        token_counter: TokenCounter,
        storage: HistoryStorage,
        llm_client: Any  # OpenClaw 的 LLM 客户端
    ):
        self.thresholds = thresholds
        self.token_counter = token_counter
        self.storage = storage
        self.llm_client = llm_client
    
    def should_compact(self, messages: list, model: str) -> bool:
        """判断是否需要压缩"""
        token_usage = self.token_counter.count_messages(messages)
        threshold = self.thresholds.get_auto_compact_threshold(model)
        return token_usage >= threshold
    
    async def compact(self, messages: list, model: str) -> tuple[list, CompactionResult]:
        """执行压缩"""
        # 1. 先保存完整历史到磁盘
        await self.storage.archive_messages(messages)
        
        # 2. 调用模型生成摘要
        summary = await self._generate_summary(messages, model)
        
        # 3. 构建新消息列表
        compacted = self._build_compacted_messages(messages, summary)
        
        return compacted, CompactionResult(
            compacted=True,
            summary_message=summary,
            original_count=len(messages),
            compacted_count=len(compacted)
        )
    
    async def _generate_summary(self, messages: list, model: str) -> dict:
        """调用模型生成摘要"""
        # 使用 Claude Code 的压缩提示词
        prompt = self._build_compaction_prompt(messages)
        
        summary = await self.llm_client.chat.completions.create(
            model=model,
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            max_tokens=self.thresholds.MAX_OUTPUT_TOKENS_FOR_SUMMARY
        )
        
        return {
            'role': 'system',
            'content': f"[Conversation Summary]\n{summary.choices[0].message.content}"
        }
```

##### Step 5: 历史存储
**文件**: `OpenClaw/compression/storage.py`

```python
# 参考: claude-code-main/src/services/SessionMemory/

import json
from pathlib import Path
from datetime import datetime

class HistoryStorage:
    """
    历史消息存储 - 确保历史信息永不丢失
    
    结构:
    history/
    ├── {session_id}/
    │   ├── archive_20260406_123456.json
    │   ├── archive_20260406_123500.json
    │   └── index.json
    └── index.json
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def archive_messages(self, session_id: str, messages: list):
        """归档完整消息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"archive_{timestamp}.json"
        
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        with open(session_dir / filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'message_count': len(messages),
                'messages': messages
            }, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        await self._update_index(session_id, filename)
    
    async def restore_messages(self, session_id: str, archive_id: str) -> list:
        """恢复归档消息"""
        pass
```

##### Step 6: 集成到主循环

修改 OpenClaw 的主循环，在每轮开始前检查压缩：

```python
# 在主循环中集成

class OpenClawAgent:
    def __init__(self):
        self.compression_engine = CompressionEngine(...)
    
    async def run(self):
        while True:
            # 1. 检查是否需要压缩
            if self.compression_engine.should_compact(self.messages, self.model):
                self.messages, result = await self.compression_engine.compact(
                    self.messages, 
                    self.model
                )
                logger.info(f"Compressed: {result.original_count} → {result.compacted_count} messages")
            
            # 2. 正常执行...
```

---

### 1.2 S03/S07: Todo V2 + 任务依赖图系统（P1 - 重要）

#### 现状分析
- **OpenClaw**: `todo.json`（基础列表），`tasks.json`（空数组）
- **Claude Code**: Todo V1 + Task V2（完整依赖图系统）

#### 优化方案：增强现有 Todo 系统为 Task V2

```
OpenClaw/tasks/
├── __init__.py
├── models.py              # 数据模型（参考 Task V2）
├── manager.py             # 任务管理器
├── storage.py             # 持久化
├── tools/
│   ├── __init__.py
│   ├── task_create.py     # TaskCreateTool
│   ├── task_update.py     # TaskUpdateTool
│   ├── task_list.py       # TaskListTool
│   └── task_get.py        # TaskGetTool
└── examples/
    └── workflow_example.json
```

##### Step 1: 数据模型
**文件**: `OpenClaw/tasks/models.py`

```python
# 参考: claude-code-main/src/utils/tasks/types.ts

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class Task:
    id: str
    subject: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    active_form: Optional[str] = None  # e.g., "Running tests"
    
    # 依赖关系
    blocks: List[str] = field(default_factory=list)    # 此任务阻塞的任务
    blocked_by: List[str] = field(default_factory=list) # 阻塞此任务的任务
    
    # 所有权
    owner: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_unlocked(self, all_tasks: List['Task']) -> bool:
        """检查任务是否解锁（所有依赖都已完成）"""
        if not self.blocked_by:
            return True
        
        for task in all_tasks:
            if task.id in self.blocked_by:
                if task.status != TaskStatus.COMPLETED:
                    return False
        return True
    
    def get_unblocked_tasks(self, all_tasks: List['Task']) -> List['Task']:
        """获取完成此任务后解锁的任务"""
        unblocked = []
        for task in all_tasks:
            if self.id in task.blocked_by:
                # 检查该任务是否还有其他未完成的依赖
                still_blocked = False
                for blocker_id in task.blocked_by:
                    if blocker_id == self.id:
                        continue
                    blocker = next((t for t in all_tasks if t.id == blocker_id), None)
                    if blocker and blocker.status != TaskStatus.COMPLETED:
                        still_blocked = True
                        break
                if not still_blocked:
                    unblocked.append(task)
        return unblocked
```

##### Step 2: 任务管理器
**文件**: `OpenClaw/tasks/manager.py`

```python
# 参考: claude-code-main/src/utils/tasks/

import uuid
from typing import List, Optional
from .models import Task, TaskStatus
from .storage import TaskStorage

class TaskManager:
    def __init__(self, storage: TaskStorage):
        self.storage = storage
    
    async def create_task(
        self,
        task_list_id: str,
        subject: str,
        description: str,
        active_form: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Task:
        """创建新任务"""
        task = Task(
            id=str(uuid.uuid4())[:8],  # 短 ID
            subject=subject,
            description=description,
            active_form=active_form,
            metadata=metadata or {}
        )
        await self.storage.save_task(task_list_id, task)
        return task
    
    async def update_task(
        self,
        task_list_id: str,
        task_id: str,
        **updates
    ) -> Optional[Task]:
        """更新任务（含依赖解锁逻辑）"""
        task = await self.storage.get_task(task_list_id, task_id)
        if not task:
            return None
        
        old_status = task.status
        
        # 更新字段
        for key, value in updates.items():
            if key == 'status':
                task.status = TaskStatus(value)
            elif key == 'add_blocks':
                task.blocks.extend([b for b in value if b not in task.blocks])
            elif key == 'add_blocked_by':
                task.blocked_by.extend([b for b in value if b not in task.blocked_by])
            elif hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        
        # 如果标记为完成，处理依赖解锁
        if old_status != TaskStatus.COMPLETED and task.status == TaskStatus.COMPLETED:
            all_tasks = await self.storage.list_tasks(task_list_id)
            unblocked = task.get_unblocked_tasks(all_tasks)
            # 可以触发事件通知解锁
            
        await self.storage.save_task(task_list_id, task)
        return task
    
    async def list_tasks(self, task_list_id: str) -> List[Task]:
        return await self.storage.list_tasks(task_list_id)
    
    async def get_unlocked_tasks(self, task_list_id: str) -> List[Task]:
        """获取所有解锁的任务"""
        all_tasks = await self.storage.list_tasks(task_list_id)
        return [t for t in all_tasks if t.is_unlocked(all_tasks)]
```

##### Step 3: 持久化存储
**文件**: `OpenClaw/tasks/storage.py`

```python
# 参考: Claude Code 的任务持久化方式（每个任务独立 JSON）

import json
from pathlib import Path
from typing import List, Optional
from .models import Task

class TaskStorage:
    """
    每个任务独立 JSON 文件存储
    
    结构:
    tasks/
    └── {task_list_id}/
        ├── index.json
        ├── task_{task_id_1}.json
        ├── task_{task_id_2}.json
        └── ...
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_task_dir(self, task_list_id: str) -> Path:
        return self.base_dir / task_list_id
    
    def _get_task_file(self, task_list_id: str, task_id: str) -> Path:
        return self._get_task_dir(task_list_id) / f"task_{task_id}.json"
    
    async def save_task(self, task_list_id: str, task: Task):
        task_dir = self._get_task_dir(task_list_id)
        task_dir.mkdir(exist_ok=True)
        
        # 保存任务文件
        with open(self._get_task_file(task_list_id, task.id), 'w') as f:
            json.dump({
                'id': task.id,
                'subject': task.subject,
                'description': task.description,
                'status': task.status.value,
                'active_form': task.active_form,
                'blocks': task.blocks,
                'blocked_by': task.blocked_by,
                'owner': task.owner,
                'metadata': task.metadata,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
            }, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        await self._update_index(task_list_id)
    
    async def get_task(self, task_list_id: str, task_id: str) -> Optional[Task]:
        task_file = self._get_task_file(task_list_id, task_id)
        if not task_file.exists():
            return None
        
        with open(task_file) as f:
            data = json.load(f)
        
        return Task(
            id=data['id'],
            subject=data['subject'],
            description=data['description'],
            status=TaskStatus(data['status']),
            active_form=data.get('active_form'),
            blocks=data.get('blocks', []),
            blocked_by=data.get('blocked_by', []),
            owner=data.get('owner'),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
        )
    
    async def list_tasks(self, task_list_id: str) -> List[Task]:
        task_dir = self._get_task_dir(task_list_id)
        if not task_dir.exists():
            return []
        
        tasks = []
        for task_file in task_dir.glob("task_*.json"):
            task = await self.get_task(task_list_id, task_file.stem[5:])
            if task:
                tasks.append(task)
        
        # 按创建时间排序
        return sorted(tasks, key=lambda t: t.created_at)
```

##### Step 4: Task 工具实现
参考 Claude Code 的四个 Task 工具，为 OpenClaw 实现：
- TaskCreateTool
- TaskUpdateTool
- TaskListTool
- TaskGetTool

---

## 🏗️ Phase 2: 协作功能增强（2-4周）- 🟡 中优先级

### 2.1 S12: Worktree 任务隔离

#### 问题诊断
- **现状**: 无隔离，多 Agent 同时编辑可能冲突
- **参考**: Claude Code 的 EnterWorktreeTool + Git Worktree

#### 实现方案
```
OpenClaw/worktree/
├── __init__.py
├── manager.py             # Worktree 管理器
├── git_integration.py     # Git Worktree 集成
├── tools/
│   ├── enter_worktree.py
│   └── exit_worktree.py
└── storage.py
```

---

### 2.2 S08: 后台任务系统

#### 问题诊断
- **现状**: 无后台任务，耗时操作阻塞主循环
- **参考**: Claude Code 的 TaskOutputTool + TaskStopTool

#### 实现方案
```
OpenClaw/background/
├── __init__.py
├── runner.py              # 后台任务运行器
├── queue.py               # 结果队列
├── manager.py             # 任务管理器
└── tools/
    ├── task_output.py
    └── task_stop.py
```

---

## 🏗️ Phase 3: 工程化提升（4-8周）- 🟢 低优先级

### 3.1 已有工具系统增强

#### 工具输入验证
- 为所有现有工具添加 JSON Schema 验证
- 参考 Claude Code 的 Zod schema 用法

#### 工具 Hook 系统
- 实现 pre-tool-use / post-tool-use hooks
- 参考 `claude-code-main/src/services/tools/toolHooks.ts`

#### Analytics 埋点框架
- 可选的使用统计收集
- 参考 Claude Code 的 GrowthBook 集成

---

### 3.2 配置与 Feature Flag 系统

#### 实现 Feature Flag
- 类似 Claude Code 的 30+ feature flags
- 支持环境变量配置
- 支持运行时切换

---

## 📋 实施路线图总览

| 阶段 | 时间 | 核心任务 | 状态 |
|------|------|---------|------|
| **Phase 0** | 1周 | 基础设施重构（工具系统、状态管理） | 待开始 |
| **Phase 1** | 2周 | 三层压缩系统 + Task V2 | 待开始 |
| **Phase 2** | 4周 | Worktree + 后台任务 | 待开始 |
| **Phase 3** | 8周 | 工程化提升 | 待开始 |

---

## 🎯 预期成果

### 量化指标
- [ ] 100+ 轮对话无 Token 溢出
- [ ] Token 使用率降低 60%+
- [ ] 任务依赖图正确工作
- [ ] 多 Agent 同时编辑无冲突
- [ ] 后台任务不阻塞主循环

### 质量指标
- [ ] 完整的单元测试覆盖
- [ ] 类型安全（Python 类型注解）
- [ ] 详细的文档和示例
- [ ] 向后兼容（旧数据自动迁移）

---

## 📚 关键参考文件索引

### 工具系统
- `claude-code-main/src/Tool.ts` - Tool 接口定义
- `claude-code-main/src/tools.ts` - 工具注册表
- `claude-code-main/src/tools/TodoWriteTool/TodoWriteTool.ts` - 完整示例

### 压缩系统
- `claude-code-main/src/services/compact/autoCompact.ts` - 自动压缩触发
- `claude-code-main/src/services/compact/compact.ts` - 压缩主逻辑
- `claude-code-main/src/services/compact/microCompact.ts` - 微压缩

### 任务系统
- `claude-code-main/src/tools/TaskCreateTool/TaskCreateTool.ts`
- `claude-code-main/src/tools/TaskUpdateTool/TaskUpdateTool.ts`
- `claude-code-main/src/utils/tasks/`

### Worktree
- `claude-code-main/src/tools/EnterWorktreeTool/EnterWorktreeTool.ts`
- `claude-code-main/src/utils/worktree.ts`

---

**文档版本**: v1.0
**创建时间**: 2026-04-06
**状态**: 计划完成，等待实施
