# DeerFlow ↔ OpenHarness 双向特性增强实施指南

## 📋 文档概述

本文档提供**两个顶级 AI Agent Harness 框架**之间的**双向特性增强方案**：
- **方案 A**: 在 **DeerFlow 2.0** 基础上集成 **OpenHarness v0.2.0** 的独特特性
- **方案 B**: 在 **OpenHarness v0.2.0** 基础上集成 **DeerFlow 2.0** 的独特特性

每个方案都包含：**具体实现步骤、代码示例、架构图、风险评估和测试策略**。

---

## 🎯 增强目标总览

### OpenHarness 独特特性（可移植到 DeerFlow）

| 特性 | 优先级 | 复杂度 | 预期收益 |
|------|--------|--------|----------|
| ✅ **多级权限系统** (PermissionChecker) | P0 | 中 | 开箱即用的安全防护 |
| ✅ **任务 DAG 依赖图** (TaskDependencyGraph) | P0 | 高 | 复杂工作流编排能力 |
| ✅ **Hook 事件系统** (PreToolUse/PostToolUse) | P0 | 低 | 极高的扩展灵活性 |
| ✅ **自治 Worker** (AutonomousWorker) | P1 | 中 | 资源优化的多 Agent 协调 |
| ✅ **时间感知上下文压缩** (Microcompact) | P1 | 低 | 更智能的 Token 管理 |
| ✅ **权限拒绝追踪** (DenialTracker) | P1 | 低 | 改善用户体验 |
| ✅ **定时任务工具** (CronCreate) | P2 | 低 | 自动化能力增强 |
| ✅ **43+ 工具集** (Tools) | P2 | 中 | 功能丰富度提升 |

### DeerFlow 独特特性（可移植到 OpenHarness）

| 特性 | 优先级 | 复杂度 | 预期收益 |
|------|--------|--------|----------|
| ✅ **Docker 沙箱隔离** (Sandbox System) | P0 | 高 | 生产级安全执行环境 |
| ✅ **结构化记忆系统** (Memory with Facts) | P0 | 中 | 更强大的长期记忆能力 |
| ✅ **IM 渠道集成** (Feishu/Slack/Telegram) | P1 | 高 | 多平台触达能力 |
| ✅ **12 个中间件链** (Middleware Chain) | P1 | 中 | 可组合的 Agent 行为控制 |
| ✅ **Web UI** (Next.js Frontend) | P1 | 高 | 更好的用户体验 |
| ✅ **MCP Server 集成** (Multi-Server MCP) | P2 | 中 | 工具生态扩展 |
| ✅ **22 个内置技能** (Skills) | P2 | 低 | 即用型工作流模板 |

---

# 🚀 方案 A: DeerFlow + OpenHarness 特性增强

## A.1 架构设计

### 增强后的 DeerFlow 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Enhanced DeerFlow 2.0+                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Nginx (2026)                              │   │
│  └──────────┬──────────────────────────┬────────────────────────┘   │
│             │                          │                            │
│             ▼                          ▼                            │
│  ┌──────────────────┐    ┌──────────────────────────┐            │
│  │ LangGraph Server │    │     Gateway API          │            │
│  │   (端口 2024)    │◄───│      (端口 8001)         │            │
│  └────────┬─────────┘    └────────────┬─────────────┘            │
│           │                         │                           │
│           └──────────┬──────────────┘                           │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Enhanced Agent System                       │    │
│  │                                                          │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │    │
│  │  │ Lead Agent  │  │ Sub-Agents   │  │ Autonomous     │  │    │
│  │  │ + Hook系统  │  │ + DAG编排    │  │ Workers        │  │    │
│  │  └─────────────┘  └──────────────┘  │ (来自OH)       │  │    │
│  │                                    └────────────────┘  │    │
│  │                                                          │    │
│  │  ┌────────────────────────────────────────────────────┐ │    │
│  │  │              Enhanced Middleware Chain               │ │    │
│  │  │                                                    │ │    │
│  │  │ 1. ThreadDataMiddleware                            │ │    │
│  │  │ 2. UploadsMiddleware                               │ │    │
│  │  │ 3. SandboxMiddleware                               │ │    │
│  │  │ 4. DanglingToolCallMiddleware                      │ │    │
│  │  │ 5. ⭐ PermissionCheckerMiddleware (新增 - 来自 OH) │ │    │
│  │  │ 6. GuardrailMiddleware                             │ │    │
│  │  │ 7. SummarizationMiddleware                         │ │    │
│  │  │ 8. TodoListMiddleware                              │ │    │
│  │  │ 9. TitleMiddleware                                 │ │    │
│  │  │ 10. MemoryMiddleware                               │ │    │
│  │  │ 11. ViewImageMiddleware                            │ │    │
│  │  │ 12. SubagentLimitMiddleware                        │ │    │
│  │  │ 13. ClarificationMiddleware                        │ │    │
│  │  │ 14. ⭐ DenialTrackerMiddleware (新增 - 来自 OH)    │ │    │
│  │  └────────────────────────────────────────────────────┘ │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    New Components (from OpenHarness)        │   │
│  │                                                              │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                   │   │
│  │  │ PermissionSystem│  │ TaskDAGSystem   │                   │   │
│  │  │ (3级权限模式)   │  │ (依赖图编排)    │                   │   │
│  │  └─────────────────┘  └─────────────────┘                   │   │
│  │                                                              │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                   │   │
│  │  │ HookExecutor    │  │ CronScheduler   │                   │   │
│  │  │ (事件驱动扩展)   │  │ (定时任务)      │                   │   │
│  │  └─────────────────┘  └─────────────────┘                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## A.2 详细实施步骤

### 步骤 1: 集成 OpenHarness 权限系统 (P0 - 高优先级)

#### 目标
将 OpenHarness 的 `PermissionChecker` 和多级权限模式集成到 DeerFlow 的中间件链中。

#### 实施细节

##### 1.1 创建权限模块

**文件位置**: `backend/packages/harness/deerflow/permissions/`

```python
"""
DeerFlow 增强权限系统（基于 OpenHarness PermissionChecker）
支持三种权限模式：Default/Auto/Plan
"""

from __future__ import annotations

import fnmatch
import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

log = logging.getLogger(__name__)


class PermissionMode(str, Enum):
    """权限模式枚举"""
    DEFAULT = "default"      # 默认模式：写操作需确认
    FULL_AUTO = "auto"       # 全自动模式：允许所有操作
    PLAN = "plan"            # 计划模式：阻止所有写操作


@dataclass(frozen=True)
class PermissionDecision:
    """权限决策结果"""
    allowed: bool
    requires_confirmation: bool = False
    reason: str = ""


@dataclass
class PathRule:
    """路径级权限规则"""
    pattern: str
    allow: bool  # True=允许, False=拒绝


@dataclass
class PermissionSettings:
    """权限配置"""
    mode: PermissionMode = PermissionMode.DEFAULT
    
    # 工具级别控制
    denied_tools: set[str] = field(default_factory=set)
    allowed_tools: set[str] = field(default_factory=set)
    
    # 路径级规则
    path_rules: list[PathRule] = field(default_factory=list)
    
    # 命令黑名单
    denied_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /*",
        "rm -rf /",
        "DROP TABLE",
        "FORMAT",
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/sda",      # 磁盘覆盖
        "chmod -R 777 /",  # 权限滥用
    ])
    
    # 拒绝追踪配置
    denial_tracking_enabled: bool = True
    denial_cache_ttl_seconds: float = 1800.0  # 30分钟


class DenialTracker:
    """
    权限拒绝追踪器（防止重复提示）
    
    来自 OpenHarness permissions/denial_tracking.py
    使用 SHA256 操作指纹 + 时间戳缓存
    """
    
    def __init__(self, ttl_seconds: float = 1800.0):
        self._cache: dict[str, float] = {}
        self._ttl = ttl_seconds
    
    def _compute_fingerprint(self, tool_name: str, args: dict) -> str:
        """计算操作的 SHA256 指纹"""
        content = f"{tool_name}:{sorted(args.items())}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def is_denied_recently(self, tool_name: str, args: dict) -> bool:
        """检查是否最近已拒绝过相同操作"""
        fp = self._compute_fingerprint(tool_name, args)
        if fp in self._cache:
            elapsed = time.time() - self._cache[fp]
            if elapsed < self._ttl:
                return True
            else:
                del self._cache[fp]
        return False
    
    def record_denial(self, tool_name: str, args: dict) -> None:
        """记录一次拒绝"""
        fp = self._compute_fingerprint(tool_name, args)
        self._cache[fp] = time.time()
    
    def cleanup(self) -> int:
        """清理过期条目，返回清理数量"""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v > self._ttl]
        for k in expired:
            del self._cache[k]
        return len(expired)


class EnhancedPermissionChecker:
    """
    增强版权限检查器（整合 OpenHarness PermissionChecker）
    
    特性：
    - 三种权限模式 (Default/Auto/Plan)
    - 路径级规则匹配 (glob 模式)
    - 命令黑名单过滤
    - 拒绝追踪 (防重复提示)
    - 与 DeerFlow GuardrailMiddleware 兼容
    """
    
    def __init__(self, settings: PermissionSettings):
        self._settings = settings
        self._denial_tracker = DenialTracker(
            ttl_seconds=settings.denial_cache_ttl_seconds
        ) if settings.denial_tracking_enabled else None
        
        # 解析路径规则
        self._path_rules: list[PathRule] = []
        for rule in settings.path_rules:
            if isinstance(rule, dict):
                pattern = rule.get("pattern", "")
                allow = rule.get("allow", True)
            else:
                pattern = getattr(rule, "pattern", "")
                allow = getattr(rule, "allow", True)
            
            if isinstance(pattern, str) and pattern.strip():
                self._path_rules.append(PathRule(
                    pattern=pattern.strip(),
                    allow=allow
                ))
    
    @property
    def denial_tracker(self) -> Optional[DenialTracker]:
        return self._denial_tracker
    
    def evaluate(
        self,
        tool_name: str,
        *,
        is_read_only: bool = False,
        file_path: str | None = None,
        command: str | None = None,
        arguments: dict | None = None,
    ) -> PermissionDecision:
        """
        评估工具调用是否被允许
        
        Args:
            tool_name: 工具名称
            is_read_only: 是否只读操作
            file_path: 涉及的文件路径
            command: shell 命令内容
            arguments: 工具参数字典
        
        Returns:
            PermissionDecision 权限决策
        """
        
        # 1. 显式工具拒绝列表
        if tool_name in self._settings.denied_tools:
            return PermissionDecision(
                allowed=False,
                reason=f"工具 '{tool_name}' 已被显式拒绝"
            )
        
        # 2. 显式工具允许列表
        if tool_name in self._settings.allowed_tools:
            return PermissionDecision(
                allowed=True,
                reason=f"工具 '{tool_name}' 已被显式允许"
            )
        
        # 3. 路径级规则检查
        if file_path and self._path_rules:
            for rule in self._path_rules:
                if fnmatch.fnmatch(file_path, rule.pattern):
                    if not rule.allow:
                        return PermissionDecision(
                            allowed=False,
                            reason=f"路径 '{file_path}' 匹配拒绝规则: {rule.pattern}"
                        )
        
        # 4. 命令黑名单检查
        if command:
            for pattern in self._settings.denied_commands:
                if isinstance(pattern, str) and fnmatch.fnmatch(command, pattern):
                    # 检查是否最近已拒绝过（防重复提示）
                    if self._denial_tracker and arguments:
                        if self._denial_tracker.is_denied_recently(
                            tool_name, arguments or {}
                        ):
                            return PermissionDecision(
                                allowed=False,
                                reason=f"[静默] 命令匹配黑名单: {pattern}"
                            )
                        
                        # 记录本次拒绝
                        self._denial_tracker.record_denial(
                            tool_name, arguments or {}
                        )
                    
                    return PermissionDecision(
                        allowed=False,
                        reason=f"命令匹配安全黑名单: {pattern}"
                    )
        
        # 5. 全自动模式：允许所有操作
        if self._settings.mode == PermissionMode.FULL_AUTO:
            return PermissionDecision(
                allowed=True,
                reason="全自动模式允许所有工具调用"
            )
        
        # 6. 只读工具始终允许
        if is_read_only:
            return PermissionDecision(
                allowed=True,
                reason="只读工具默认允许"
            )
        
        # 7. 计划模式：阻止所有变异操作
        if self._settings.mode == PermissionMode.PLAN:
            return PermissionDecision(
                allowed=False,
                reason="计划模式已启用：所有写操作将被阻止，直到退出计划模式"
            )
        
        # 8. 默认模式：需要用户确认
        return PermissionDecision(
            allowed=False,
            requires_confirmation=True,
            reason="变异操作需要用户确认（默认模式）"
        )
```

##### 1.2 创建权限中间件

**文件位置**: `backend/packages/harness/deerflow/agents/middlewares/permission_checker_middleware.py`

```python
"""
权限检查中间件（集成到 DeerFlow 中间件链）
位置：在 GuardrailMiddleware 之后执行（索引 5）
"""

from __future__ import annotations

from typing import Any

from deerflow.agents.middlewares.base import BaseMiddleware
from deerflow.permissions.checker import (
    EnhancedPermissionChecker,
    PermissionDecision,
    PermissionSettings,
)


class PermissionCheckerMiddleware(BaseMiddleware):
    """
    权限检查中间件
    
    在工具执行前进行细粒度的权限校验，
    整合了 OpenHarness 的多级权限系统和拒绝追踪机制。
    """
    
    name = "permission_checker"
    
    def __init__(
        self,
        permission_settings: PermissionSettings | None = None,
    ):
        super().__init__()
        self._checker = EnhancedPermissionChecker(
            permission_settings or PermissionSettings()
        )
    
    @property
    def checker(self) -> EnhancedPermissionChecker:
        return self._checker
    
    async def before_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        state: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        在工具调用前执行权限检查
        
        Returns:
            (should_continue, error_message)
            - True, None: 允许执行
            - False, msg: 拒绝执行，返回错误消息
        """
        # 从参数中提取关键信息
        file_path = tool_args.get("file_path") or tool_args.get("path")
        command = tool_args.get("command") or tool_args.get("cmd")
        
        # 判断是否为只读工具
        read_only_tools = {
            "read_file", "list_dir", "glob", "grep",
            "view_image", "present_files", "ask_clarification",
            "get_task_status", "list_tasks",
        }
        is_read_only = tool_name in read_only_tools
        
        # 执行权限评估
        decision: PermissionDecision = self._checker.evaluate(
            tool_name,
            is_read_only=is_read_only,
            file_path=file_path,
            command=command,
            arguments=tool_args,
        )
        
        if decision.allowed:
            return True, None
        
        if decision.requires_confirmation:
            # 需要用户确认 → 返回特殊标记，由上层处理交互
            state["_pending_permission_confirmation"] = {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "reason": decision.reason,
            }
            return False, f"⚠️ 需要确认: {decision.reason}"
        
        # 直接拒绝
        log.warning(
            "权限拒绝: tool=%s, reason=%s",
            tool_name,
            decision.reason,
        )
        return False, f"🚫 权限不足: {decision.reason}"
```

##### 1.3 注册到中间件链

修改 [agent.py](file:///home/xxh/claudecode源码(仅用于学习交流)/deer-flow-main/backend/packages/harness/deerflow/agents/lead_agent/agent.py):

```python
# 在 make_lead_agent 函数中添加：

from deerflow.agents.middlewares.permission_checker_middleware import (
    PermissionCheckerMiddleware,
)

def make_lead_agent(config: RunnableConfig) -> CompiledGraph:
    # ... 现有代码 ...
    
    middlewares = [
        ThreadDataMiddleware(),
        UploadsMiddleware(),
        SandboxMiddleware(),
        DanglingToolCallMiddleware(),
        # ⭐ 新增：OpenHarness 风格的权限检查
        PermissionCheckerMiddleware(permission_settings=config.permission_settings),
        GuardrailMiddleware(),  # 原有的护栏中间件保留，作为第二道防线
        SummarizationMiddleware(),
        TodoListMiddleware(),
        TitleMiddleware(),
        MemoryMiddleware(),
        ViewImageMiddleware(),
        SubagentLimitMiddleware(),
        ClarificationMiddleware(),
        # ⭐ 新增：拒绝追踪中间件（可选）
        # DenialTrackerMiddleware(),
    ]
```

#### 配置示例 (`config.yaml`)

```yaml
# 新增 permission 配置节
permission:
  # 权限模式: default | auto | plan
  mode: default
  
  # 显式拒绝的工具列表
  denied_tools:
    - dangerous_command
    - system_modify
  
  # 显式允许的工具列表（白名单模式时使用）
  allowed_tools: []
  
  # 路径级规则
  path_rules:
    - pattern: "/etc/*"
      allow: false
    - pattern: "/usr/bin/*"
      allow: false
    - pattern: "/root/*"
      allow: false
    - pattern: "./**"
      allow: true
  
  # 命令黑名单（追加到默认列表）
  denied_commands:
    - "sudo rm -rf"
    - "chmod 777"
  
  # 拒绝追踪设置
  denial_tracking_enabled: true
  denial_cache_ttl_seconds: 1800  # 30分钟
```

---

### 步骤 2: 集成任务 DAG 依赖图 (P0 - 高优先级)

#### 目标
引入 OpenHarness 的 `TaskDependencyGraph`，为 DeerFlow 的子代理系统增加复杂工作流编排能力。

#### 实施细节

##### 2.1 创建 DAG 模块

**文件位置**: `backend/packages/harness/deerflow/subagents/dag.py`

```python
"""
子代理任务依赖图管理（基于 OpenHarness TaskDependencyGraph）

为 DeerFlow 子代理系统增加 DAG 编排能力：
- 任务间依赖关系定义
- 自动解锁机制
- 循环依赖检测
- Mermaid 格式可视化
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

log = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"        # 等待中（可能有未完成的前置依赖）
    BLOCKED = "blocked"        # 被阻塞（有未完成的前置依赖）
    READY = "ready"            # 就绪（前置依赖已完成）
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消
    TIMED_OUT = "timed_out"    # 超时


@dataclass
class TaskNode:
    """DAG 中的任务节点"""
    id: str
    subject: str              # 简短标题
    description: str          # 详细描述
    status: TaskStatus = TaskStatus.PENDING
    
    # 依赖关系
    blocked_by: list[str] = field(default_factory=list)  # 前置任务 ID
    blocks: list[str] = field(default_factory=list)      # 后续被阻塞的任务 ID
    
    # 元数据
    agent_type: str = "general-purpose"  # 子代理类型
    prompt: str | None = None            # Agent 提示词
    max_turns: int = 10                  # 最大轮次
    timeout_seconds: float = 900.0       # 超时时间（15分钟）
    
    # 结果
    result: str | None = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None


class CircularDependencyError(Exception):
    """循环依赖异常"""
    
    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"检测到循环依赖: {' → '.join(cycle)}")


class SubAgentTaskDAG:
    """
    子代理任务依赖图管理器
    
    功能：
    1. 创建带依赖关系的任务
    2. 自动状态转换（完成前置任务 → 解锁后续任务）
    3. 循环依赖检测（DFS 算法）
    4. 可执行任务查询
    5. Mermaid 格式可视化输出
    """
    
    def __init__(self):
        self._tasks: dict[str, TaskNode] = {}
        self._adjacency: dict[str, list[str]] = {}  # 邻接表
    
    def create_task(
        self,
        subject: str,
        description: str,
        *,
        blocked_by: list[str] | None = None,
        agent_type: str = "general-purpose",
        prompt: str | None = None,
        max_turns: int = 10,
        timeout_seconds: float = 900.0,
    ) -> TaskNode:
        """
        创建新任务
        
        Args:
            subject: 任务标题
            description: 详细描述
            blocked_by: 前置依赖任务 ID 列表
            agent_type: 子代理类型
            prompt: Agent 提示词
            max_turns: 最大轮次
            timeout_seconds: 超时时间
        
        Returns:
            新创建的 TaskNode
        
        Raises:
            CircularDependencyError: 检测到循环依赖
            ValueError: 前置依赖任务不存在
        """
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # 验证前置依赖存在
        if blocked_by:
            for dep_id in blocked_by:
                if dep_id not in self._tasks:
                    raise ValueError(f"前置依赖任务不存在: {dep_id}")
            
            # 检测循环依赖
            self._check_circular_dependency(task_id, blocked_by or [])
        
        # 创建节点
        task = TaskNode(
            id=task_id,
            subject=subject,
            description=description,
            blocked_by=blocked_by or [],
            agent_type=agent_type,
            prompt=prompt,
            max_turns=max_turns,
            timeout_seconds=timeout_seconds,
        )
        
        # 初始状态判断
        if task.blocked_by:
            has_unfinished = any(
                self._tasks[dep_id].status not in (
                    TaskStatus.COMPLETED, TaskStatus.CANCELLED
                )
                for dep_id in task.blocked_by
                if dep_id in self._tasks
            )
            task.status = TaskStatus.BLOCKED if has_unfinished else TaskStatus.READY
        else:
            task.status = TaskStatus.READY
        
        # 注册任务
        self._tasks[task_id] = task
        self._adjacency[task_id] = task.blocked_by.copy()
        
        # 更新后续任务的 blocks 列表
        for dep_id in task.blocked_by:
            if dep_id in self._tasks:
                self._tasks[dep_id].blocks.append(task_id)
        
        log.info(
            "创建任务 %s (%s), 状态=%s, 依赖=%s",
            task_id, subject, task.status.value, task.blocked_by
        )
        
        return task
    
    def complete_task(self, task_id: str, result: str | None = None) -> list[str]:
        """
        标记任务完成并自动解锁后续任务
        
        Args:
            task_id: 完成的任务 ID
            result: 任务结果
        
        Returns:
            被解锁的任务 ID 列表
        """
        if task_id not in self._tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self._tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        
        import time
        task.completed_at = time.time()
        
        # 查找并解锁后续任务
        unlocked_ids = []
        for successor_id in task.blocks:
            if successor_id not in self._tasks:
                continue
            
            successor = self._tasks[successor_id]
            
            # 从 blocked_by 中移除已完成的任务
            if task_id in successor.blocked_by:
                successor.blocked_by.remove(task_id)
            
            # 检查是否所有前置依赖都已完成
            if not successor.blocked_ids:
                all_deps_done = all(
                    self._tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in successor.blocked_by
                    if dep_id in self._tasks
                )
                
                if all_deps_done and successor.status == TaskStatus.BLOCKED:
                    successor.status = TaskStatus.READY
                    unlocked_ids.append(successor_id)
                    log.info(
                        "任务 %s (%s) 已解锁",
                        successor_id, successor.subject
                    )
        
        log.info(
            "任务 %s (%s) 完成, 解锁 %d 个后续任务",
            task_id, task.subject, len(unlocked_ids)
        )
        
        return unlocked_ids
    
    def get_executable_tasks(self) -> list[TaskNode]:
        """获取当前可执行的任务（状态为 READY）"""
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.READY
        ]
    
    def get_blocked_tasks(self) -> list[TaskNode]:
        """获取当前被阻塞的任务"""
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.BLOCKED
        ]
    
    def _check_circular_dependency(
        self,
        new_node_id: str,
        blocked_by: list[str],
    ) -> None:
        """
        使用 DFS 检测循环依赖
        
        Args:
            new_node_id: 新任务 ID
            blocked_by: 前置依赖列表
        
        Raises:
            CircularDependencyError: 发现循环
        """
        visited = set()
        path = []
        
        def dfs(node_id: str) -> bool:
            if node_id in path:
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                raise CircularDependencyError(cycle)
            
            if node_id in visited:
                return False
            
            visited.add(node_id)
            path.append(node_id)
            
            # 遍历该节点的依赖
            for dep_id in (self._tasks.get(node_id, TaskNode(id=node_id)).blocked_by):
                if dep_id == new_node_id:
                    # 发现回到新节点的路径
                    path.append(new_node_id)
                    raise CircularDependencyError(path[path.index(new_node_id):])
                dfs(dep_id)
            
            path.pop()
            return False
        
        # 从新节点开始 DFS
        for dep_id in blocked_by:
            dfs(dep_id)
    
    def to_mermaid(self) -> str:
        """
        生成 Mermaid 格式的 DAG 可视化
        
        Returns:
            Mermaid 图表代码
        """
        lines = ["graph TD"]
        
        # 节点定义
        for task_id, task in self._tasks.items():
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.BLOCKED: "🔒",
                TaskStatus.READY: "✅",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
            }.get(task.status, "❓")
            
            label = f"{status_emoji} {task.subject}"
            lines.append(f'    {task_id}["{label}"]')
        
        # 边定义（依赖关系）
        for task_id, task in self._tasks.items():
            for dep_id in task.blocked_by:
                lines.append(f'    {dep_id} --> {task_id}')
        
        return "\n".join(lines)
    
    def get_statistics(self) -> dict:
        """获取 DAG 统计信息"""
        from collections import Counter
        status_counts = Counter(task.status.value for task in self._tasks.values())
        
        return {
            "total_tasks": len(self._tasks),
            "status_breakdown": dict(status_counts),
            "executable_count": len(self.get_executable_tasks()),
            "blocked_count": len(self.get_blocked_tasks()),
            "max_depth": self._calculate_max_depth(),
        }
    
    def _calculate_max_depth(self) -> int:
        """计算 DAG 的最大深度"""
        def get_depth(task_id: str, memo: dict[str, int]) -> int:
            if task_id in memo:
                return memo[task_id]
            
            task = self._tasks.get(task_id)
            if not task or not task.blocked_by:
                memo[task_id] = 0
                return 0
            
            max_dep_depth = max(
                get_depth(dep_id, memo) for dep_id in task.blocked_by
                if dep_id in self._tasks
            )
            memo[task_id] = max_dep_depth + 1
            return memo[task_id]
        
        memo = {}
        for task_id in self._tasks:
            get_depth(task_id, memo)
        
        return max(memo.values()) if memo else 0
```

##### 2.2 创建 DAG 工具

**文件位置**: `backend/packages/harness/deerflow/tools/dag_tool.py`

```python
"""
任务依赖图工具（供 Lead Agent 调用）
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from deerflow.tools.base import BaseTool, ToolExecutionContext, ToolResult
from deerflow.subagents.dag import SubAgentTaskDAG, TaskStatus


class CreateDAGTaskInput(BaseModel):
    subject: str = Field(description="任务简短标题")
    description: str = Field(description="详细描述")
    blocked_by: list[str] = Field(
        default=[],
        description="前置依赖任务 ID 列表"
    )
    agent_type: str = Field(
        default="general-purpose",
        description="子代理类型: general-purpose | bash"
    )
    prompt: str | None = Field(
        default=None,
        description="自定义 Agent 提示词"
    )


class CompleteDAGTaskInput(BaseModel):
    task_id: str = Field(description="要完成的任务 ID")
    result: str | None = Field(
        default=None,
        description="任务执行结果"
    )


class ViewDAGInput(BaseModel):
    format: str = Field(
        default="mermaid",
        description="输出格式: mermaid | text | json"
    )


class TaskDAGTool(BaseTool):
    """任务依赖图管理工具"""
    
    name = "task_dag"
    description = "创建和管理带依赖关系的子代理任务。支持 DAG 编排、自动解锁、循环检测。"
    input_model = CreateDAGTaskInput
    
    def __init__(self):
        super().__init__()
        self._dag = SubAgentTaskDAG()
    
    async def execute(
        self,
        arguments: CreateDAGTaskInput,
        context: ToolExecutionContext,
    ) -> ToolResult:
        task = self._dag.create_task(
            subject=arguments.subject,
            description=arguments.description,
            blocked_by=arguments.blocked_by,
            agent_type=arguments.agent_type,
            prompt=arguments.prompt,
        )
        
        return ToolResult(output=f"""
✅ 任务创建成功
- ID: {task.id}
- 标题: {task.subject}
- 状态: {task.status.value}
- 前置依赖: {task.blocked_by or '无'}
- 后续任务: {len(task.blocks)} 个
""")


class CompleteDAGTaskTool(BaseTool):
    """完成任务并触发自动解锁"""
    
    name = "complete_dag_task"
    description = "完成任务并自动解锁后续被阻塞的任务。"
    input_model = CompleteDAGTaskInput
    
    def __init__(self, dag: SubAgentTaskDAG):
        super().__init__()
        self._dag = dag
    
    async def execute(
        self,
        arguments: CompleteDAGTaskInput,
        context: ToolExecutionContext,
    ) -> ToolResult:
        try:
            unlocked = self._dag.complete_task(
                arguments.task_id,
                result=arguments.result,
            )
            
            output = f"""
✅ 任务 {arguments.task_id} 已完成
"""
            
            if unlocked:
                output += f"🔓 已解锁 {len(unlocked)} 个后续任务:\n"
                for uid in unlocked:
                    task = self._dag._tasks.get(uid)
                    if task:
                        output += f"  - [{uid}] {task.subject}\n"
            else:
                output += "没有待解锁的后续任务\n"
            
            return ToolResult(output=output)
            
        except ValueError as e:
            return ToolResult(output=f"❌ 错误: {str(e)}")


class ViewDAGTool(BaseTool):
    """查看任务依赖图"""
    
    name = "view_dag"
    description = "查看当前任务依赖图的状态和结构。"
    input_model = ViewDAGInput
    
    def __init__(self, dag: SubAgentTaskDAG):
        super().__init__()
        self._dag = dag
    
    async def execute(
        self,
        arguments: ViewDAGInput,
        context: ToolExecutionContext,
    ) -> ToolResult:
        stats = self._dag.get_statistics()
        
        if arguments.format == "mermaid":
            mermaid_code = self._dag.to_mermaid()
            return ToolResult(output=f"""
## 任务依赖图统计
- 总任务数: {stats['total_tasks']}
- 可执行: {stats['executable_count']}
- 被阻塞: {stats['blocked_count']}
- 最大深度: {stats['max_depth']}

### Mermaid 图表
```mermaid
{mermaid_code}
```
""")
        
        elif arguments.format == "json":
            import json
            return ToolResult(output=json.dumps(stats, indent=2))
        
        else:
            lines = ["## 当前任务状态\n"]
            for task in self._dag._tasks.values():
                emoji = {"ready": "✅", "blocked": "🔒", "running": "🔄",
                        "completed": "✅", "failed": "❌"}.get(
                    task.status.value, "⏳"
                )
                deps = ", ".join(task.blocked_by) if task.blocked_by else "无"
                lines.append(
                    f"- {emoji} **{task.subject}** ({task.id})\n"
                    f"  状态: {task.status.value} | 依赖: {deps}"
                )
            
            return ToolResult(output="\n".join(lines))
```

---

### 步骤 3: 集成 Hook 事件系统 (P0 - 高优先级)

#### 目标
引入 OpenHarness 的 `HookExecutor`，为 DeerFlow 提供**事件驱动的扩展机制**。

#### 实施细节

##### 3.1 创建 Hook 系统

**文件位置**: `backend/packages/harness/deerflow/hooks/`

```python
"""
DeerFlow Hook 事件系统（基于 OpenHarness Hook Executor）

提供 PreToolUse / PostToolUse 生命周期钩子，
使第三方可以无侵入地扩展 Agent 行为。
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

log = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """Hook 事件类型"""
    PRE_TOOL_USE = "pre_tool_use"      # 工具调用前
    POST_TOOL_USE = "post_tool_use"    # 工具调用后
    PRE_SUBAGENT_SPAWN = "pre_subagent_spawn"   # 子代理生成前
    POST_SUBAGENT_COMPLETE = "post_subagent_complete"  # 子代理完成后
    ON_MEMORY_UPDATE = "on_memory_update"  # 记忆更新时
    ON_CONTEXT_COMPACT = "on_context_compact"  # 上下文压缩时


@dataclass
class HookContext:
    """Hook 执行上下文"""
    event: HookEvent
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_result: Any = None
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 控制标志
    cancel: bool = False
    cancel_reason: str = ""
    modified_args: dict[str, Any] | None = None
    modified_result: Any = None


@dataclass
class HookResult:
    """单个 Hook 的执行结果"""
    hook_name: str
    success: bool
    duration_ms: float = 0.0
    error: str | None = None
    context_modifications: dict[str, Any] = field(default_factory=dict)


@dataclass 
class AggregatedHookResult:
    """聚合的 Hook 执行结果"""
    results: list[HookResult] = field(default_factory=list)
    cancelled: bool = False
    cancellation_reason: str = ""
    
    @property
    def total_duration_ms(self) -> float:
        return sum(r.duration_ms for r in self.results)
    
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def failure_count(self) -> int:
        return len(self.results) - self.success_count


class BaseHook(ABC):
    """Hook 基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Hook 唯一名称"""
        pass
    
    @property
    def events(self) -> list[HookEvent]:
        """监听的事件类型"""
        return []
    
    @abstractmethod
    async def execute(self, ctx: HookContext) -> HookContext | None:
        """
        执行 Hook 逻辑
        
        Returns:
            修改后的上下文（或 None 表示无修改）
        """
        pass


class HookExecutor:
    """
    Hook 执行器
    
    负责：
    1. 注册和管理 Hook
    2. 在适当时机触发 Hook
    3. 聚合执行结果
    4. 支持 Hook 取消工具调用
    """
    
    def __init__(self):
        self._hooks: dict[HookEvent, list[BaseHook]] = {}
        self._enabled: bool = True
    
    def register_hook(self, hook: BaseHook) -> None:
        """注册一个 Hook"""
        for event in hook.events:
            if event not in self._hooks:
                self._hooks[event] = []
            self._hooks[event].append(hook)
            log.debug("注册 Hook: %s → %s", hook.name, event.value)
    
    def unregister_hook(self, hook_name: str) -> None:
        """注销指定 Hook"""
        for event_hooks in self._hooks.values():
            self._hooks[event_hooks] = [
                h for h in event_hooks if h.name != hook_name
            ]
    
    async def trigger(
        self,
        event: HookEvent,
        context: HookContext,
    ) -> AggregatedHookResult:
        """
        触发指定事件的所有 Hook
        
        Args:
            event: 事件类型
            context: 执行上下文
        
        Returns:
            聚合结果
        """
        result = AggregatedHookResult()
        
        if not self._enabled:
            return result
        
        hooks = self._hooks.get(event, [])
        if not hooks:
            return result
        
        log.debug(
            "触发 Hook 事件: %s, Hook 数量: %d",
            event.value, len(hooks)
        )
        
        for hook in hooks:
            import time
            start = time.monotonic()
            
            try:
                modified_ctx = await hook.execute(context)
                
                duration = (time.monotonic() - start) * 1000
                
                if modified_ctx and modified_ctx.cancel:
                    result.cancelled = True
                    result.cancellation_reason = modified_ctx.cancel_reason
                    result.results.append(HookResult(
                        hook_name=hook.name,
                        success=True,
                        duration_ms=duration,
                        context_modifications={"cancelled": True},
                    ))
                    log.info(
                        "Hook %s 取消了操作: %s",
                        hook.name, modified_ctx.cancel_reason
                    )
                    break  # 一个 Hook 取消即停止
                
                result.results.append(HookResult(
                    hook_name=hook.name,
                    success=True,
                    duration_ms=duration,
                ))
                
                # 应用上下文修改
                if modified_ctx:
                    if modified_ctx.modified_args:
                        context.tool_args.update(modified_ctx.modified_args)
                    if modified_ctx.modified_result is not None:
                        context.modified_result = modified_ctx.modified_result
                        
            except Exception as e:
                duration = (time.monotonic() - start) * 1000
                log.error("Hook %s 执行失败: %s", hook.name, e, exc_info=True)
                result.results.append(HookResult(
                    hook_name=hook.name,
                    success=False,
                    duration_ms=duration,
                    error=str(e),
                ))
        
        return result
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value


# 内置 Hook 示例

class LoggingHook(BaseHook):
    """日志记录 Hook（内置）"""
    
    @property
    def name(self) -> str:
        return "logging"
    
    @property
    def events(self) -> list[HookEvent]:
        return [HookEvent.PRE_TOOL_USE, HookEvent.POST_TOOL_USE]
    
    async def execute(self, ctx: HookContext) -> HookContext | None:
        if ctx.event == HookEvent.PRE_TOOL_USE:
            log.info(
                "[Hook:Logging] 工具调用前: %s(args=%s)",
                ctx.tool_name,
                list(ctx.tool_args.keys()) if ctx.tool_args else {},
            )
        elif ctx.event == HookEvent.POST_TOOL_USE:
            log.info(
                "[Hook:Logging] 工具调用后: %s (耗时待统计)",
                ctx.tool_name,
            )
        return None


class SecurityAuditHook(BaseHook):
    """安全审计 Hook（内置）"""
    
    def __init__(self, sensitive_patterns: list[str] | None = None):
        self._patterns = sensitive_patterns or [
            "password", "secret", "api_key", "token",
            "credential", "private_key",
        ]
    
    @property
    def name(self) -> str:
        return "security_audit"
    
    @property
    def events(self) -> list[HookEvent]:
        return [HookEvent.PRE_TOOL_USE]
    
    async def execute(self, ctx: HookContext) -> HookContext | None:
        if not ctx.tool_args:
            return None
        
        # 检查敏感信息泄露
        args_str = str(ctx.tool_args).lower()
        for pattern in self._patterns:
            if pattern in args_str:
                log.warning(
                    "[Hook:SecurityAudit] ⚠️ 检测到可能的敏感信息: "
                    "tool=%s, pattern=%s",
                    ctx.tool_name, pattern
                )
        
        return None
```

##### 3.2 集成到中间件链

在现有中间件中添加 Hook 触发点：

```python
# 在相关中间件的 before_tool_call / after_tool_call 方法中：

async def before_tool_call(self, tool_name, tool_args, state):
    # ... 现有逻辑 ...
    
    # ⭐ 触发 PreToolUse Hooks
    hook_executor: HookExecutor = state.get("_hook_executor")
    if hook_executor:
        ctx = HookContext(
            event=HookEvent.PRE_TOOL_USE,
            tool_name=tool_name,
            tool_args=tool_args,
        )
        result = await hook_executor.trigger(HookEvent.PRE_TOOL_USE, ctx)
        
        if result.cancelled:
            return False, f"Hook 取消: {result.cancellation_reason}"
        
        # 应用 Hook 修改后的参数
        if ctx.modified_args:
            tool_args.update(ctx.modified_args)
    
    # ... 继续原有逻辑 ...

async def after_tool_call(self, tool_name, tool_args, result, state):
    # ... 现有逻辑 ...
    
    # ⭐ 触发 PostToolUse Hooks
    hook_executor: HookExecutor = state.get("_hook_executor")
    if hook_executor:
        ctx = HookContext(
            event=HookEvent.POST_TOOL_USE,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=result,
        )
        await hook_executor.trigger(HookEvent.POST_TOOL_USE, ctx)
```

---

### 步骤 4: 集成自治 Worker (P1 - 中优先级)

#### 目标
引入 OpenHarness 的 `AutonomousWorker`，优化 DeerFlow 子代理的资源利用率。

#### 核心代码片段

```python
"""
自治 Worker（基于 OpenHarness autonomous_worker.py）

为 DeerFlow 子代理系统增加自主任务认领能力，
替代现有的被动调度模式。
"""

class DeerFlowAutonomousWorker:
    """
    自治 Worker：主动认领任务、自动管理生命周期
    
    状态机：
        idle → working (认领到任务)
        working → idle (任务完成)
        idle → shutting_down (超时无任务)
        shutting_down → terminated
    """
    
    def __init__(
        self,
        config: AutonomousWorkerConfig,
        dag: SubAgentTaskDAG,
        agent_loop: Callable,  # Agent 主循环函数
    ):
        self._config = config
        self._dag = dag
        self._agent_loop = agent_loop
        self._state = WorkerState.IDLE
        self._statistics = WorkerStatistics()
        self._shutdown_event = asyncio.Event()
    
    async def run(self) -> None:
        """Worker 主循环"""
        log.info(
            "自治 Worker 启动: id=%s, team=%s",
            self._config.agent_id, self._config.team
        )
        
        start_time = time.time()
        last_activity_time = time.time()
        
        while not self._shutdown_event.is_set():
            try:
                if self._state == WorkerState.IDLE:
                    # 空闲轮询：尝试认领任务
                    executable = self._dag.get_executable_tasks()
                    
                    if executable:
                        task = executable[0]  # 认领第一个可执行任务
                        await self._execute_task(task)
                        last_activity_time = time.time()
                    else:
                        # 检查空闲超时
                        idle_time = time.time() - last_activity_time
                        if idle_time > self._config.max_idle_time_sec:
                            log.info(
                                "Worker 空闲超时 (%.1fs)，准备关机",
                                idle_time
                            )
                            self._state = WorkerState.SHUTTING_DOWN
                            break
                        
                        # 等待后重试
                        await asyncio.sleep(
                            self._config.idle_poll_interval_sec
                        )
                
                elif self._state == WorkerState.WORKING:
                    # 工作状态：等待当前任务完成
                    await asyncio.sleep(
                        self._config.work_check_interval_sec
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Worker 异常: %s", e, exc_info=True)
                self._state = WorkerState.IDLE
        
        # 关机流程
        self._state = WorkerState.TERMINATED
        self._statistics.total_uptime_sec = time.time() - start_time
        log.info("Worker 已终止, 统计: %s", self._statistics)
    
    async def _execute_task(self, task: TaskNode) -> None:
        """执行单个任务"""
        self._state = WorkerState.WORKING
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self._statistics.tasks_claimed += 1
        
        try:
            log.info("开始执行任务: %s (%s)", task.id, task.subject)
            
            # 调用 Agent 主循环
            async for event in self._agent_loop(
                prompt=task.prompt or task.description,
                max_turns=task.max_turns,
            ):
                # 处理流式事件...
                pass
            
            # 标记完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            self._statistics.tasks_completed += 1
            
            # 触发 DAG 自动解锁
            self._dag.complete_task(task.id)
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMED_OUT
            self._statistics.tasks_failed += 1
            log.error("任务超时: %s", task.id)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._statistics.tasks_failed += 1
            log.error("任务失败: %s, 错误: %s", task.id, e)
        
        finally:
            self._state = WorkerState.IDLE
    
    async def shutdown(self, timeout: float = 30.0) -> None:
        """优雅关机"""
        log.info("请求 Worker 关机...")
        self._shutdown_event.set()
        
        # 等待实际终止或超时
        try:
            await asyncio.wait_for(
                self._wait_for_termination(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            log.warning("Worker 关机超时，强制终止")
    
    async def _wait_for_termination(self) -> None:
        while self._state != WorkerState.TERMINATED:
            await asyncio.sleep(0.1)
```

---

### 步骤 5: 集成其他 OpenHarness 特性 (P1-P2)

#### 5.1 时间感知上下文压缩

```python
"""
时间感知微压缩（基于 OpenHarness MicrocompactConfig）

在 DeerFlow SummarizationMiddleware 中增加时间维度压缩。
"""

@dataclass
class TimeAwareCompactConfig:
    """微压缩配置"""
    keep_recent_turns: int = 5
    gap_threshold_minutes: float = 60.0  # 超过60分钟的消息也压缩
    enable_time_aware: bool = True


def should_compact_message(
    message_index: int,
    total_messages: int,
    message_timestamp: float | None,
    current_timestamp: float | None,
    config: TimeAwareCompactConfig,
) -> bool:
    """判断消息是否应该被压缩"""
    # 基于轮次
    by_turns = (total_messages - message_index) > config.keep_recent_turns
    
    if not config.enable_time_aware or message_timestamp is None:
        return by_turns
    
    # 基于时间间隔
    if current_timestamp:
        time_gap_minutes = (current_timestamp - message_timestamp) / 60.0
        by_time = time_gap_minutes > config.gap_threshold_minutes
        return by_turns or by_time
    
    return by_turns
```

#### 5.2 定时任务工具

```python
"""
Cron 定时任务工具（基于 OpenHarness CronCreateTool）
"""

class CronCreateTool(BaseTool):
    name = "cron_create"
    description = "创建定时执行的 Agent 任务。支持 cron 表达式。"
    
    async def execute(self, arguments, context) -> ToolResult:
        # 实现 cron 调度逻辑
        # 可以使用 Python croniter 库
        pass
```

---

# 🔧 方案 B: OpenHarness + DeerFlow 特性增强

## B.1 架构设计

### 增强后的 OpenHarness 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Enhanced OpenHarness v0.3+                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    CLI / React TUI                           │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                      │
│                             ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Enhanced QueryEngine                        │   │
│  │                                                              │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────────┐  │   │
│  │  │ Agent Loop │  │ Hook System  │  │ Middleware Chain     │  │   │
│  │  │ (原有)     │  │ (原有)       │  │ ⭐ (新增 - DF风格)   │  │   │
│  │  └────────────┘  └──────────────┘  └─────────────────────┘  │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │              Enhanced Components (from DeerFlow)      │  │   │
│  │  │                                                      │  │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │   │
│  │  │  │ Docker      │  │ Structured  │  │ IM Channels │  │  │   │
│  │  │  │ Sandbox     │  │ Memory      │  │ (Feishu等)  │  │  │   │
│  │  │  │ ⭐ (新增)   │  │ ⭐ (增强)   │  │ ⭐ (新增)   │  │  │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │   │
│  │  │                                                      │  │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │   │
│  │  │  │ Web UI      │  │ MCP Multi- │  │ Skills      │  │  │   │
│  │  │  │ (Next.js)   │  │ Server      │  │ (22个DF技能)│  │  │   │
│  │  │  │ ⭐ (可选)   │  │ ⭐ (增强)   │  │ ⭐ (可选)   │  │  │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## B.2 详细实施步骤

### 步骤 1: 集成 Docker 沙箱系统 (P0 - 高优先级)

#### 目标
将 DeerFlow 的抽象沙箱接口和 Docker 隔离能力引入 OpenHarness。

#### 实施细节

##### 1.1 创建沙箱抽象层

**文件位置**: `src/openharness/sandbox/`

```python
"""
OpenHarness 沙箱系统（基于 DeerFlow Sandbox 抽象类）

提供统一的沙箱接口，支持本地模式和 Docker 模式。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SandboxConfig:
    """沙箱配置"""
    mode: str = "local"  # local | docker | kubernetes
    
    # Docker 配置
    docker_image: str = "python:3.12-slim"
    docker_network: str = "openharness-sandbox"
    container_timeout: int = 3600  # 1小时超时
    
    # 路径映射
    host_workspace: Path = Path(".openharness/workspace")
    container_workspace: Path = Path("/mnt/user-data/workspace")
    
    host_skills: Path = Path(".openharness/skills")
    container_skills: Path = Path("/mnt/skills")


class Sandbox(ABC):
    """沙箱抽象基类"""
    
    def __init__(self, config: SandboxConfig):
        self._config = config
        self._id = self._generate_id()
    
    @staticmethod
    def _generate_id() -> str:
        import uuid
        return f"sandbox-{uuid.uuid4().hex[:8]}"
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def config(self) -> SandboxConfig:
        return self._config
    
    @abstractmethod
    async def execute_command(self, command: str) -> str:
        """在沙箱中执行命令"""
        pass
    
    @abstractmethod
    async def read_file(self, path: str) -> str:
        """读取文件"""
        pass
    
    @abstractmethod
    async def write_file(self, path: str, content: str, append: bool = False) -> None:
        """写入文件"""
        pass
    
    @abstractmethod
    async def list_dir(self, path: str, max_depth: int = 2) -> list[str]:
        """列出目录内容"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理沙箱资源"""
        pass


class LocalSandbox(Sandbox):
    """本地沙箱（直接访问文件系统）"""
    
    async def execute_command(self, command: str) -> str:
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self._config.host_workspace,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"命令执行失败: {result.stderr}")
        return result.stdout
    
    async def read_file(self, path: str) -> str:
        full_path = self._config.host_workspace / path
        return full_path.read_text(encoding="utf-8")
    
    async def write_file(self, path: str, content: str, append: bool = False) -> None:
        full_path = self._config.host_workspace / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        full_path.write_text(content, encoding="utf-8", newline="\n")
    
    async def list_dir(self, path: str, max_depth: int = 2) -> list[str]:
        import os
        full_path = self._config.host_workspace / path
        results = []
        
        for root, dirs, files in os.walk(full_path):
            depth = root.replace(str(full_path, "").count(os.sep)
            if depth >= max_depth:
                dirs[:] = []  # 不再深入
                continue
            
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), full_path)
                results.append(rel_path)
        
        return results
    
    async def cleanup(self) -> None:
        pass  # 本地模式无需清理


class DockerSandbox(Sandbox):
    """Docker 沙箱（容器隔离执行）"""
    
    def __init__(self, config: SandboxConfig):
        super().__init__(config)
        self._container_id: Optional[str] = None
        self._client = None  # docker.DockerClient
    
    async def _ensure_container(self) -> None:
        """确保容器存在且运行中"""
        import docker
        
        if self._client is None:
            self._client = docker.from_env()
        
        if self._container_id is None:
            # 创建并启动容器
            container = self._client.containers.run(
                image=self._config.docker_image,
                command="tail -f /dev/null",  # 保持运行
                detach=True,
                network=self._config.docker_network,
                volumes={
                    str(self._config.host_workspace.absolute()): {
                        "bind": str(self._config.container_workspace),
                        "mode": "rw",
                    },
                    str(self._config.host_skills.absolute()): {
                        "bind": str(self._config.container_skills),
                        "mode": "ro",
                    },
                },
                working_dir=str(self._config.container_workspace),
                mem_limit="512m",  # 内存限制
                cpu_quota=50000,   # CPU 限制 (0.5核)
            )
            self._container_id = container.id
    
    async def execute_command(self, command: str) -> str:
        await self._ensure_container()
        
        container = self._client.containers.get(self._container_id)
        
        # 转换为容器内路径
        container_cmd = self._translate_command(command)
        
        exit_code, output = container.exec_run(
            cmd=["bash", "-c", container_cmd],
            workdir=str(self._config.container_workspace),
        )
        
        if exit_code != 0:
            raise RuntimeError(f"Docker 命令执行失败 (code={exit_code}): {output.decode()}")
        
        return output.decode()
    
    def _translate_command(self, command: str) -> str:
        """将主机路径转换为容器虚拟路径"""
        host_ws = str(self._config.host_workspace)
        container_ws = str(self._config.container_workspace)
        return command.replace(host_ws, container_ws)
    
    async def read_file(self, path: str) -> str:
        await self._ensure_container()
        # 通过 docker cp 或 exec cat 实现
        container = self._client.containers.get(self._container_id)
        container_path = self._config.container_workspace / path
        exit_code, output = container.exec_run(["cat", str(container_path)])
        return output.decode()
    
    async def write_file(self, path: str, content: str, append: bool = False) -> None:
        await self._ensure_container()
        container = self._client.containers.get(self._container_id)
        container_path = self._config.container_workspace / path
        
        # 先创建目录
        container.exec_run(["mkdir", "-p", str(container_path.parent)])
        
        # 写入内容
        cmd = "sh -c 'cat >> {}'".format(container_path) if append else \
              "sh -c 'cat > {}'".format(container_path)
        container.exec_run(cmd, input=content.encode())
    
    async def list_dir(self, path: str, max_depth: int = 2) -> list[str]:
        await self._ensure_container()
        container = self._client.containers.get(self._container_id)
        container_path = self._config.container_workspace / path
        
        exit_code, output = container.exec_run([
            "find", str(container_path),
            "-maxdepth", str(max_depth),
            "-type", "f",
        ])
        
        if exit_code == 0:
            files = output.decode().strip().split("\n")
            # 转换为相对路径
            ws = str(self._config.container_workspace)
            return [f.replace(ws + "/", "") for f in files if f]
        
        return []
    
    async def cleanup(self) -> None:
        if self._container_id and self._client:
            try:
                container = self._client.containers.get(self._container_id)
                container.stop(timeout=10)
                container.remove(force=True)
            except Exception:
                pass
            finally:
                self._container_id = None


class SandboxFactory:
    """沙箱工厂"""
    
    @staticmethod
    def create(config: SandboxConfig) -> Sandbox:
        """根据配置创建沙箱实例"""
        if config.mode == "docker":
            return DockerSandbox(config)
        elif config.mode == "kubernetes":
            # TODO: 实现 K8s 沙箱
            raise NotImplementedError("Kubernetes 模式尚未实现")
        else:
            return LocalSandbox(config)
```

##### 1.2 修改 BashTool 以支持沙箱

```python
"""
增强版 Bash 工具（支持沙箱执行）
"""

class EnhancedBashTool(BashTool):
    """支持沙箱隔离的 Bash 工具"""
    
    def __init__(self, sandbox: Sandbox | None = None):
        super().__init__()
        self._sandbox = sandbox
    
    async def execute(self, arguments, context) -> ToolResult:
        if self._sandbox:
            # 在沙箱中执行
            try:
                output = await self._sandbox.execute_command(arguments.command)
                return ToolResult(output=output)
            except Exception as e:
                return ToolResult(output=f"沙箱执行错误: {e}", success=False)
        else:
            # 原有本地执行逻辑
            return await super().execute(arguments, context)
```

---

### 步骤 2: 增强记忆系统 (P0 - 高优先级)

#### 目标
将 DeerFlow 的**结构化记忆模型**（Facts 表、置信度评分、类别分类）引入 OpenHarness。

#### 实施细节

##### 2.1 创建结构化记忆模块

**文件位置**: `src/openharness/memory/enhanced.py`

```python
"""
增强型记忆系统（基于 DeerFlow Memory Updater）

支持：
- 结构化 Facts 表（ID、内容、类别、置信度、时间戳）
- LLM 自动提取和去重
- 类别分类（preference/knowledge/context/behavior/goal）
- 置信度衰减
- 跨会话持久化
"""

from __future__ import annotations

import json
import logging
import math
import re
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


class FactCategory(str, Enum):
    """事实类别"""
    PREFERENCE = "preference"     # 用户偏好
    KNOWLEDGE = "knowledge"       # 领域知识
    CONTEXT = "context"           # 上下文背景
    BEHAVIOR = "behavior"         # 行为习惯
    GOAL = "goal"                 # 目标意图


@dataclass
class MemoryFact:
    """结构化事实"""
    id: str
    content: str
    category: FactCategory
    confidence: float  # 0.0 - 1.0
    created_at: str   # ISO 8601
    source: str       # manual | extracted | inferred
    times_mentioned: int = 0
    last_accessed: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserContext:
    """用户上下文"""
    work_context: str = ""
    personal_context: str = ""
    top_of_mind: str = ""  # 1-3句话摘要


@dataclass
class HistorySnapshot:
    """历史快照"""
    recent_months: str = ""
    earlier_context: str = ""
    long_term_background: str = ""


@dataclass
class EnhancedMemoryData:
    """完整记忆数据结构"""
    version: int = 1
    user_context: UserContext = field(default_factory=UserContext)
    history: HistorySnapshot = field(default_factory=HistorySnapshot)
    facts: list[MemoryFact] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 配置
    max_facts: int = 100
    confidence_threshold: float = 0.7
    half_life_days: float = 30.0  # 置信度半衰期（天）


class EnhancedMemoryManager:
    """
    增强型记忆管理器
    
    特性：
    1. 结构化存储（JSON）
    2. 事实去重（内容相似度）
    3. 置信度衰减（时间因素）
    4. LLM 辅助提取
    5. 注入式检索（按相关性排序）
    """
    
    def __init__(
        self,
        storage_path: Path = Path(".openharness/memory/enhanced_memory.json"),
        config: EnhancedMemoryData | None = None,
    ):
        self._storage_path = storage_path
        self._config = config or EnhancedMemoryData()
        self._data: EnhancedMemoryData | None = None
        self._dirty = False
    
    @property
    def data(self) -> EnhancedMemoryData:
        if self._data is None:
            self._data = self._load()
        return self._data
    
    def _load(self) -> EnhancedMemoryData:
        """从文件加载记忆数据"""
        if self._storage_path.exists():
            try:
                raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
                # 反序列化为数据类
                return self._deserialize(raw)
            except Exception as e:
                log.error("加载记忆数据失败: %s", e)
        
        return EnhancedMemoryData()
    
    def _deserialize(self, raw: dict) -> EnhancedMemoryData:
        """反序列化 JSON 到数据类"""
        data = EnhancedMemoryData()
        
        # 用户上下文
        uc = raw.get("user_context", {})
        data.user_context = UserContext(
            work_context=uc.get("work_context", ""),
            personal_context=uc.get("personal_context", ""),
            top_of_mind=uc.get("top_of_mind", ""),
        )
        
        # 历史
        hist = raw.get("history", {})
        data.history = HistorySnapshot(
            recent_months=hist.get("recent_months", ""),
            earlier_context=hist.get("earlier_context", ""),
            long_term_background=hist.get("long_term_background", ""),
        )
        
        # 事实列表
        facts_raw = raw.get("facts", [])
        for f in facts_raw:
            try:
                fact = MemoryFact(
                    id=f["id"],
                    content=f["content"],
                    category=FactCategory(f["category"]),
                    confidence=float(f.get("confidence", 0.5)),
                    created_at=f.get("created_at", ""),
                    source=f.get("source", "manual"),
                    times_mentioned=f.get("times_mentioned", 0),
                    last_accessed=f.get("last_accessed"),
                )
                data.facts.append(fact)
            except (KeyError, ValueError) as e:
                log.warning("跳过无效事实: %s", e)
        
        # 元数据和配置
        data.metadata = raw.get("metadata", {})
        data.max_facts = raw.get("max_facts", 100)
        data.confidence_threshold = raw.get("confidence_threshold", 0.7)
        
        return data
    
    def save(self) -> bool:
        """保存记忆数据到文件"""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            raw = self._serialize(self.data)
            self._storage_path.write_text(
                json.dumps(raw, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._dirty = False
            return True
        except Exception as e:
            log.error("保存记忆数据失败: %s", e)
            return False
    
    def _serialize(self, data: EnhancedMemoryData) -> dict:
        """序列化数据类为 JSON 兼容格式"""
        return {
            "version": data.version,
            "user_context": asdict(data.user_context),
            "history": asdict(data.history),
            "facts": [f.to_dict() for f in data.facts],
            "metadata": data.metadata,
            "max_facts": data.max_facts,
            "confidence_threshold": data.confidence_threshold,
        }
    
    def add_fact(
        self,
        content: str,
        category: FactCategory = FactCategory.CONTEXT,
        confidence: float = 0.5,
        source: str = "manual",
    ) -> MemoryFact:
        """
        添加新事实（带去重）
        
        Returns:
            新创建或已存在的 MemoryFact
        """
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("内容不能为空")
        
        # 去重检查（简单的内容相似度）
        existing = self._find_similar_fact(normalized_content)
        if existing:
            # 更新已有事实
            existing.times_mentioned += 1
            existing.last_accessed = datetime.utcnow().isoformat() + "Z"
            # 略微提高置信度
            existing.confidence = min(1.0, existing.confidence + 0.05)
            self._dirty = True
            return existing
        
        # 创建新事实
        fact = MemoryFact(
            id=f"fact_{uuid.uuid4().hex[:8]}",
            content=normalized_content,
            category=category,
            confidence=max(0.0, min(1.0, confidence)),
            created_at=datetime.utcnow().isoformat() + "Z",
            source=source,
            times_mentioned=1,
            last_accessed=datetime.utcnow().isoformat() + "Z",
        )
        
        self.data.facts.append(fact)
        
        # 强制执行最大数量限制
        self._enforce_max_facts()
        
        self._dirty = True
        return fact
    
    def _find_similar_fact(self, content: str, threshold: float = 0.85) -> MemoryFact | None:
        """查找相似的事实（简单的字符串包含检查）"""
        content_lower = content.lower().strip()
        
        for fact in self.data.facts:
            fact_lower = fact.content.lower().strip()
            
            # 完全匹配
            if content_lower == fact_lower:
                return fact
            
            # 包含关系
            if len(content_lower) > 20:
                if content_lower in fact_lower or fact_lower in content_lower:
                    return fact
        
        return None
    
    def _enforce_max_facts(self) -> None:
        """强制执行最大事实数限制（淘汰低置信度旧事实）"""
        while len(self.data.facts) > self.data.max_facts:
            # 找到最低置信度的事实
            worst = min(
                self.data.facts,
                key=lambda f: (
                    f.confidence,
                    f.times_mentioned,  # 次要排序：提及次数少的先淘汰
                ),
            )
            self.data.facts.remove(worst)
            log.debug("淘汰低置信度事实: id=%s, content=%.50s...", worst.id, worst.content)
    
    def get_relevant_facts(
        self,
        query: str = "",
        category: FactCategory | None = None,
        limit: int = 15,
        min_confidence: float | None = None,
    ) -> list[MemoryFact]:
        """
        获取相关事实（按相关性排序）
        
        Args:
            query: 查询关键词
            category: 过滤类别
            limit: 返回数量上限
            min_confidence: 最低置信度阈值
        
        Returns:
            排序后的事实列表
        """
        threshold = min_confidence or self.data.confidence_threshold
        query_lower = query.lower() if query else ""
        
        candidates = [
            f for f in self.data.facts
            if f.confidence >= threshold
            and (category is None or f.category == category)
        ]
        
        if query_lower:
            # 简单的关键词匹配打分
            def relevance_score(fact: MemoryFact) -> float:
                score = fact.confidence * 0.5  # 基础分：置信度权重
                
                content_lower = fact.content.lower()
                
                # 完全匹配加分
                if query_lower in content_lower:
                    score += 0.3
                
                # 词重叠加分
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                overlap = len(query_words & content_words)
                score += overlap * 0.05
                
                # 最近访问加分
                if fact.last_accessed:
                    score += 0.1
                
                return score
            
            candidates.sort(key=relevance_score, reverse=True)
        else:
            # 仅按置信度和时间排序
            candidates.sort(key=lambda f: (-f.confidence, f.created_at), reverse=False)
        
        # 更新访问时间
        for fact in candidates[:limit]:
            fact.last_accessed = datetime.utcnow().isoformat() + "Z"
        
        return candidates[:limit]
    
    def apply_confidence_decay(self) -> int:
        """
        应用置信度衰减（基于时间）
        
        Returns:
            被淘汰的事实数量
        """
        import time
        now = time.time()
        decayed_count = 0
        
        surviving_facts = []
        for fact in self.data.facts:
            # 解析创建时间
            try:
                created = datetime.fromisoformat(
                    fact.created_at.replace("Z", "+00:00")
                ).timestamp()
                age_days = (now - created) / 86400
                
                # 指数衰减
                half_life = self.data.half_life_days
                decay_factor = 0.5 ** (age_days / half_life)
                fact.confidence *= decay_factor
                
                # 淘汰过低置信度的事实
                if fact.confidence < 0.1:
                    decayed_count += 1
                    continue
                    
            except (ValueError, OSError):
                pass
            
            surviving_facts.append(fact)
        
        self.data.facts = surviving_facts
        if decayed_count > 0:
            self._dirty = True
        
        return decayed_count
    
    def generate_memory_prompt(self, max_tokens: int = 2000) -> str:
        """
        生成用于注入 system prompt 的记忆文本
        
        Args:
            max_tokens: 最大 token 数估算（粗略）
        
        Returns:
            格式化的记忆文本
        """
        top_facts = self.get_relevant_facts(limit=15)
        
        sections = ["<memory>"]
        
        # 用户上下文
        uc = self.data.user_context
        if uc.top_of_mind:
            sections.append(f"## 用户概况")
            sections.append(uc.top_of_mind)
        
        # 重要事实
        if top_facts:
            sections.append("\n## 关键知识")
            for i, fact in enumerate(top_facts[:15], 1):
                emoji = {
                    FactCategory.PREFERENCE: "💭",
                    FactCategory.KNOWLEDGE: "📚",
                    FactCategory.CONTEXT: "📍",
                    FactCategory.BEHAVIOR: "🔄",
                    FactCategory.GOAL: "🎯",
                }.get(fact.category, "📝")
                
                conf_pct = int(fact.confidence * 100)
                sections.append(
                    f"{i}. {emoji} [{fact.category.value}] "
                    f"(置信度:{conf_pct}%) {fact.content}"
                )
        
        sections.append("\n</memory>")
        
        result = "\n".join(sections)
        
        # 粗略 token 估算（1 token ≈ 4 字符）
        estimated_tokens = len(result) // 4
        if estimated_tokens > max_tokens:
            # 截断
            result = result[:max_tokens * 4] + "\n</memory>"
        
        return result
    
    def update_from_conversation(
        self,
        messages: list[dict],
        llm_client,  # LLM 客户端（用于提取）
    ) -> int:
        """
        从对话历史中提取记忆更新（LLM 辅助）
        
        Args:
            messages: 对话消息列表
            llm_client: LLM API 客户端
        
        Returns:
            新增的事实数量
        """
        # TODO: 实现 LLM 提取逻辑
        # 参考 DeerFlow memory/updater.py 的 extract_facts 方法
        pass
```

---

### 步骤 3: 集成 IM 渠道 (P1 - 中优先级)

#### 目标
将 DeerFlow 的飞书/Slack/Telegram 渠道适配层引入 OpenHarness。

#### 核心架构

```python
"""
IM 渠道集成框架（简化版 DeerFlow Channels）

支持：
- 消息总线 (MessageBus)
- 会话持久化
- 平台适配器 (Adapter Pattern)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass
class InboundMessage:
    """入站消息"""
    channel: str          # feishu | slack | telegram
    chat_id: str
    user_id: str
    text: str
    message_id: str
    timestamp: float


@dataclass
class OutboundMessage:
    """出站消息"""
    channel: str
    chat_id: str
    text: str
    is_final: bool = True
    reply_to: str | None = None


class MessageBus:
    """消息总线（发布/订阅模式）"""
    
    def __init__(self):
        self._queue: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self._subscribers: list[Callable[[OutboundMessage], Awaitable[None]]] = []
    
    async def publish_inbound(self, msg: InboundMessage) -> None:
        """发布入站消息"""
        await self._queue.put(msg)
    
    async def consume_inbound(self) -> InboundMessage:
        """消费入站消息"""
        return await self._queue.get()
    
    def subscribe_outbound(self, handler: Callable) -> None:
        """订阅出站消息"""
        self._subscribers.append(handler)
    
    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """发布出站消息给所有订阅者"""
        for handler in self._subscribers:
            try:
                await handler(msg)
            except Exception as e:
                log.error("出站消息处理失败: %s", e)


class ChannelAdapter(ABC):
    """IM 渠道适配器基类"""
    
    @abstractmethod
    async def start(self) -> None:
        """启动渠道连接"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止渠道连接"""
        pass
    
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """发送消息"""
        pass


# 具体平台适配器示例

class FeishuChannelAdapter(ChannelAdapter):
    """飞书渠道适配器"""
    
    async def start(self) -> None:
        # 建立 WebSocket 连接
        pass
    
    async def send(self, msg: OutboundMessage) -> None:
        # 调用飞书 API 发送消息
        pass


class SlackChannelAdapter(ChannelAdapter):
    """Slack 渠道适配器"""
    # ...


class TelegramChannelAdapter(ChannelAdapter):
    """Telegram 渠道适配器**
    # ...
```

---

### 步骤 4: 其他 DeerFlow 特性集成 (P1-P2)

#### 4.1 中间件链模式

```python
"""
OpenHarness 中间件链（借鉴 DeerFlow 设计）

提供可组合的 Agent 行为控制机制。
"""

class MiddlewareChain:
    """中间件链"""
    
    def __init__(self):
        self._middlewares: list[BaseMiddleware] = []
    
    def add(self, middleware: BaseMiddleware) -> None:
        self._middlewares.append(middleware)
    
    async def execute_before_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        state: dict,
    ) -> tuple[bool, str | None]:
        """依次执行所有中间件的 before_tool_call"""
        for mw in self._middlewares:
            should_continue, error = await mw.before_tool_call(
                tool_name, tool_args, state
            )
            if not should_continue:
                return False, error
        return True, None
    
    async def execute_after_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        result: Any,
        state: dict,
    ) -> None:
        """依次执行所有中间件的 after_tool_call（反向顺序）"""
        for mw in reversed(self._middlewares):
            await mw.after_tool_call(tool_name, tool_args, result, state)
```

#### 4.2 Web UI（可选）

如果需要 Web UI，可以直接复用 DeerFlow 的 Next.js 前端，只需调整 API 端点即可。

---

# 📊 增强效果对比总结

## 方案 A: DeerFlow + OpenHarness 增强前后对比

| 维度 | 增强 前 | 增强 后 | 提升幅度 |
|------|--------|--------|----------|
| **安全性** | 依赖外部配置 | **开箱即用的三级权限系统** | ⭐⭐⭐⭐⭐ |
| **工作流编排** | 简单子代理委托 | **DAG 依赖图 + 自治 Worker** | ⭐⭐⭐⭐⭐ |
| **扩展性** | 固定中间件链 | **事件驱动 Hook 系统** | ⭐⭐⭐⭐ |
| **Token 管理** | 基于轮次的摘要 | **时间感知双模式压缩** | ⭐⭐⭐ |
| **自动化能力** | 无 | **Cron 定时任务** | ⭐⭐⭐ |
| **工具丰富度** | ~20 个 | **~63 个 (43+ OH)** | ⭐⭐⭐⭐ |
| **用户体验** | 可能重复提示 | **智能拒绝追踪** | ⭐⭐⭐ |

## 方案 B: OpenHarness + DeerFlow 增强前后对比

| 维度 | 增强 前 | 增强 后 | 提升幅度 |
|------|--------|--------|----------|
| **执行隔离** | 本地直接执行 | **Docker/K8s 沙箱隔离** | ⭐⭐⭐⭐⭐ |
| **记忆能力** | Markdown 文本 | **结构化 Facts + 置信度** | ⭐⭐⭐⭐ |
| **平台触达** | 仅 CLI/TUI | **飞书/Slack/Telegram** | ⭐⭐⭐⭐ |
| **行为控制** | Hook 系统 | **Hook + 中间件双模式** | ⭐⭐⭐ |
| **工具生态** | 43+ 工具 | **43+ MCP Server 集成** | ⭐⭐⭐ |
| **技能库** | 40+ (anthropics) | **62+ (含 DF 22)** | ⭐⭐⭐ |
| **用户体验** | 终端界面 | **可选 Web UI** | ⭐⭐⭐ |

---

# ⚠️ 风险评估与缓解措施

## 方案 A 风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 权限系统与现有 Guardrail 冲突 | 中 | 中 | 保留两套系统，权限在前，Guardrail 作为补充 |
| DAG 增加子代理复杂度 | 中 | 中 | 提供简化模式（不使用 DAG 时保持原逻辑） |
| Hook 系统性能开销 | 低 | 低 | 异步执行 + 超时控制 |
| 自治 Worker 资源竞争 | 中 | 低 | 限制并发数 + 资源配额 |

## 方案 B 风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Docker 依赖增加部署复杂度 | 高 | 中 | 沙箱模式可选（默认 local） |
| 结构化记忆迁移成本 | 中 | 低 | 提供导入工具（MEMORY.md → JSON） |
| IM 渠道维护成本 | 中 | 低 | 采用 Adapter 模式，易于插拔 |
| Web UI 开发工作量 | 高 | 高 | 分阶段实施，CLI 优先 |

---

# 🧪 测试策略

## 方案 A 测试计划

### 单元测试
- [ ] `test_permission_checker.py` - 权限决策逻辑（20+ 用例）
- [ ] `test_dag.py` - DAG 创建/完成/解锁/循环检测（30+ 用例）
- [ ] `test_hook_executor.py` - Hook 注册/触发/取消/聚合（25+ 用例）
- [ ] `test_autonomous_worker.py` - Worker 状态机/超时/认领（20+ 用例）
- [ ] `test_denial_tracker.py` - 指纹计算/过期清理（15+ 用例）

### 集成测试
- [ ] `test_permission_middleware_integration.py` - 中间件链集成
- [ ] `test_dag_subagent_integration.py` - DAG 与子代理协作
- [ ] `test_hook_lifecycle.py` - 完整生命周期验证

### E2E 测试
- [ ] `test_full_workflow_with_permissions.py` - 完整工作流 + 权限控制
- [ ] `test_complex_dag_scenario.py` - 复杂 DAG 场景（编译→测试→部署）

## 方案 B 测试计划

### 单元测试
- [ ] `test_sandbox_abstract.py` - 沙箱接口契约
- [ ] `test_local_sandbox.py` - 本地沙箱功能
- [ ] `test_docker_sandbox.py` - Docker 沙箱（需要 Docker 环境）
- [ ] `test_enhanced_memory.py` - 记忆 CRUD/去重/衰减（40+ 用例）
- [ ] `test_memory_prompt_generation.py` - Prompt 注入格式

### 集成测试
- [ ] `test_sandbox_tool_integration.py` - 沙箱与工具系统集成
- [ ] `test_memory_agent_integration.py` - 记忆与 Agent 协作

---

# 📅 实施路线图建议

## 方案 A（DeerFlow 增强）- 4 周

```
第 1 周: 权限系统（P0）
├── Day 1-2: PermissionChecker + DenialTracker 实现
├── Day 3-4: PermissionCheckerMiddleware 集成
└── Day 5: 配置系统 + 单元测试

第 2 周: DAG 系统（P0）
├── Day 1-3: TaskDependencyGraph + TaskNode 实现
├── Day 4: DAG Tools (create/complete/view)
└── Day 5: 与子代理系统集成 + 测试

第 3 周: Hook + Worker（P0-P1）
├── Day 1-2: HookExecutor + 内置 Hooks
├── Day 3-4: AutonomousWorker 实现
└── Day 5: 集成测试 + 文档

第 4 周: 收尾（P1-P2）
├── Day 1-2: 时间感知压缩 + Cron 工具
├── Day 3: E2E 测试 + 性能基准
└── Day 4-5: 文档完善 + Code Review
```

## 方案 B（OpenHarness 增强）- 6 周

```
第 1-2 周: 沙箱系统（P0）
├── Week 1: Sandbox 抽象层 + LocalSandbox
└── Week 2: DockerSandbox + 工具集成

第 3-4 周: 记忆系统（P0）
├── Week 3: EnhancedMemoryManager 核心
└── Week 4: LLM 提取 + Prompt 注入

第 5 周: IM 渠道（P1）
├── MessageBus + ChannelAdapter 框架
└── Feishu/Slack 适配器（选做 1-2 个）

第 6 周: 收尾
├── 中间件链 + Web UI 评估
├── 集成测试 + 文档
└── 发布准备
```

---

# 💡 最佳实践建议

## 对于 DeerFlow 用户

1. **优先集成权限系统** - 安全性是生产环境的基石
2. **渐进式采用 DAG** - 先在特定场景试用（如 CI/CD 流水线）
3. **利用 Hook 做审计** - 记录所有工具调用用于合规
4. **监控自治 Worker** - 设置资源配额防止失控

## 对于 OpenHarness 用户

1. **按需开启沙箱** - 敏感操作才用 Docker
2. **渐进式迁移记忆** - 保留 MEMORY.md 兼容层
3. **选择性接入 IM** - 只接入真正需要的渠道
4. **保持轻量哲学** - 不要过度工程化

---

# 🎯 结论

## 双向增强的价值

通过这两个方案的结合，我们可以获得一个**终极 AI Agent Harness**：

```
终极 Harness = DeerFlow 的生产级基础架构
           + OpenHarness 的灵活性和开发者友好性
           + 双方的最佳实践和安全机制
```

### 核心收益

✅ **安全性**: 三级权限 + 沙箱隔离 + 审计追踪  
✅ **灵活性**: Hook 事件 + 插件系统 + 中间件链  
✅ **智能化**: DAG 编排 + 自治 Worker + 结构化记忆  
✅ **易用性**: CLI/TUI + Web UI + IM 多渠道  
✅ **可扩展**: 63+ 工具 + 62+ 技能 + MCP 生态  

### 最终建议

**短期（1-2 月）**: 选择一个主框架，集成对方的核心特性（P0）  
**中期（3-6 月）**: 完善双向集成，形成统一增强版  
**长期（6月+）**: 考虑提炼公共层，构建 Meta-Harness 框架  

---

*文档版本: v1.0*  
*最后更新: 2026年4月6日*  
*基于 DeerFlow 2.0 + OpenHarness v0.2.0 代码分析*
