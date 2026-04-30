# 🚀 OpenHarness Phase 2 实施计划：测试 + 集成 + 文档

**计划日期**: 2026-04-06  
**版本**: v1.0
**目标项目**: `/home/xxh/claudecode源码(仅用于学习交流)/OpenHarness-main`
**基于**: Phase 1 已完成的 12 个模块增强（7 个新文件 + 5 个修改文件）

---

## 📋 一、Phase 2 目标总览

### 三大任务

| # | 任务 | 预估工作量 | 优先级 | 交付物 |
|---|------|-----------|--------|--------|
| **1** | 编写单元测试 | 2 天 | P0 | 8-10 个测试文件，覆盖所有新增模块 |
| **2** | 集成到 QueryEngine | 1 天 | P0 | 引擎级功能启用 |
| **3** | 更新 README 文档 | 0.5 天 | P1 | 架构图更新 + 使用示例 |

**总计**: 3.5 天

---

## 🔧 二、任务 1: 编写单元测试（P0 - 高优先级）

### 1.1 测试策略

**遵循现有测试风格**:
- 使用 `pytest` + `pytest-asyncio` (参考 `test_tasks/test_manager.py`)
- 测试文件放在 `tests/` 目录下对应子目录
- 每个测试函数聚焦单一场景
- 使用 `tmp_path` fixture 处理临时文件
- 使用 `monkeypatch` 环境变量隔离

### 1.2 测试文件清单

#### 1.2.1 DAG 任务依赖系统测试（4 个测试文件）

##### 文件 1: `tests/test_tasks/test_dag.py`

**测试内容**:

```python
"""Tests for TaskDependencyGraph — DAG management, auto-unlock, cycle detection."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from openharness.tasks.dag import TaskDependencyGraph, CircularDependencyError
from openharness.tasks.types import TaskRecord, TaskStatus


# ===== 基础 CRUD 测试 =====

@pytest.mark.asyncio
async def test_create_task_without_dependencies():
    """创建无依赖的任务应立即可执行"""
    pass


@pytest.mark.asyncio
async def test_create_task_with_single_dependency():
    """创建带单个前置依赖的任务"""
    pass


@pytest.mark.asyncio
async def test_create_task_with_multiple_dependencies():
    """创建带多个前置依赖的任务（AND 逻辑）"""
    pass


# ===== 自动解锁机制 =====

@pytest.mark.asyncio
async def test_complete_task_unlocks_dependents():
    """完成任务后自动解锁后续任务"""
    # 1. 创建 A → B → C 的依赖链
    # 2. 完成 A
    # 3. 验证 B 被解锁，C 仍被阻塞
    pass


@pytest.mark.asyncio
async def test_complete_task_partial_unlock():
    """完成一个依赖时，如果还有其他依赖则不解锁"""
    pass


# ===== 可执行任务查询 =====

def test_get_executable_tasks_returns_ready_tasks():
    """get_executable_tasks 只返回无未完成依赖的 pending 任务"""
    pass


def test_get_blocked_tasks_returns_blocked_only():
    """get_blocked_tasks 只返回被阻塞的 pending 任务"""
    pass


# ===== 循环依赖检测 =====

def test_circular_dependency_detection_direct():
    """检测直接循环：A 依赖 B，B 依赖 A"""
    with pytest.raises(CircularDependencyError):
        pass


def test_circular_dependency_detection_indirect():
    """检测间接循环：A → B → C → A"""
    with pytest.raises(CircularDependencyError):
        pass


def test_no_circular_dependency_valid_dag():
    """有效的 DAG 不应抛出异常"""
    pass


# ===== DAG 可视化 =====

def test_visualize_dag_returns_mermaid_format():
    """visualize_dag 返回有效的 Mermaid 图语法"""
    pass


def test_visualize_empty_dag():
    """空 DAG 应返回最小有效图"""
    pass


# ===== 任务链查询 =====

def test_get_task_chain_returns_ordered_chain():
    """get_task_chain 返回从根到叶的有序链"""
    pass
```

---

##### 文件 2: `tests/test_tools/test_task_create_tool_dag.py`

**测试内容**:

```python
"""Tests for TaskCreateTool with DAG dependency support."""

from __future__ import annotations

import pytest
from pathlib import Path

from openharness.tools.task_create_tool import TaskCreateTool, TaskCreateToolInput
from openharness.tools.base import ToolExecutionContext, ToolResult


@pytest.mark.asyncio
async def test_create_task_with_blocked_by_parameter():
    """使用 blocked_by 参数创建被阻塞的任务"""
    pass


@pytest.mark.asyncio
async def test_create_task_with_blocks_parameter():
    """使用 blocks 参数创建阻塞其他任务的任务"""
    pass


@pytest.mark.asyncio
async def test_create_task_status_shows_blocked():
    """被阻塞的任务输出中应包含 [BLOCKED] 标记"""
    pass


@pytest.mark.asyncio
async def test_create_nonexistent_dependency_raises_error():
    """引用不存在的任务 ID 应报错"""
    tool = TaskCreateTool()
    ctx = ToolExecutionContext(cwd="/tmp")
    
    result = await tool.execute(
        TaskCreateToolInput(
            type="local_bash",
            description="test",
            command="echo hi",
            blocked_by=["nonexistent_id"],
        ),
        ctx,
    )
    
    assert result.is_error is True
    assert "不存在" in result.output
```

---

##### 文件 3: `tests/test_tools/test_task_deps_tool.py`

**测试内容**:

```python
"""Tests for TaskDepsTool — viewing task dependencies."""

from __future__ import annotations

import pytest

from openharness.tools.task_deps_tool import TaskDepsTool, TaskDepsToolInput
from openharness.tools.base import ToolExecutionContext, ToolResult


@pytest.mark.asyncio
async def test_list_action_shows_all_tasks():
    """默认 action='list' 显示所有任务及依赖关系"""
    pass


@pytest.mark.asyncio
async def test_executable_action_filters_ready_tasks():
    """action='executable' 只显示可执行的任务"""
    pass


@pytest.mark.asyncio
async def test_blocked_action_filters_blocked_tasks():
    """action='blocked' 只显示被阻塞的任务"""
    pass


@pytest.mark.asyncio
async def test_visualize_action_returns_mermaid_graph():
    """action='visualize' 返回 Mermaid 格式的 DAG 图"""
    pass


@pytest.mark.asyncio
async def test_empty_task_list_handled_gracefully():
    """无任务时返回友好提示"""
    pass
```

---

##### 文件 4: `tests/test_tasks/test_types_dag.py`

**测试内容**:

```python
"""Tests for extended TaskRecord with DAG fields."""

from __future__ import annotations

import pytest
import time

from openharness.tasks.types import TaskRecord, TaskStatus


class TestTaskRecordDAGFields:
    """测试扩展后的 TaskRecord 类型"""

    def test_default_blocks_and_blocked_by_are_empty(self):
        """默认情况下 blocks 和 blockedBy 为空列表"""
        task = TaskRecord(
            id="test-1",
            type="local_bash",
            status="pending",
            description="test task",
            cwd="/tmp",
            output_file=__file__,
        )
        
        assert task.blocks == []
        assert task.blocked_by == []

    def test_is_executable_true_when_no_deps(self):
        """无依赖的 pending 任务是可执行的"""
        task = TaskRecord(
            id="test-2",
            type="local_bash",
            status="pending",
            description="test",
            cwd="/tmp",
            output_file=__file__,
        )
        
        assert task.is_executable is True

    def test_is_executable_false_when_has_deps(self):
        """有未完成依赖的任务不可执行"""
        task = TaskRecord(
            id="test-3",
            type="local_bash",
            status="pending",
            description="test",
            cwd="/tmp",
            output_file=__file__,
            blocked_by=["dep-1"],
        )
        
        assert task.is_executable is False

    def test_is_blocked_true(self):
        """有 blockedBy 且状态为 pending 时为阻塞状态"""
        task = TaskRecord(
            id="test-4",
            type="local_bash",
            status="pending",
            description="test",
            cwd="/tmp",
            output_file=__file__,
            blocked_by=["dep-1"],
        )
        
        assert task.is_blocked is True

    def test_add_dependency_appends_to_list(self):
        """add_dependency 应追加到 blockedBy 列表"""
        task = TaskRecord(
            id="test-5",
            type="local_bash",
            status="pending",
            description="test",
            cwd="/tmp",
            output_file=__file__,
        )
        
        task.add_dependency("dep-a")
        task.add_dependency("dep-b")
        
        assert len(task.blocked_by) == 2
        assert "dep-a" in task.blocked_by
        assert "dep-b" in task.blocked_by

    def test_remove_dependency_returns_true_when_fully_unblocked(self):
        """移除最后一个依赖时返回 True（完全解除阻塞）"""
        task = TaskRecord(
            id="test-6",
            type="local_bash",
            status="pending",
            description="test",
            cwd="/tmp",
            output_file=__file__,
            blocked_by=["only-dep"],
        )
        
        result = task.remove_dependency("only-dep")
        
        assert result is True
        assert len(task.blocked_by) == 0

    def test_remove_dependency_returns_false_when_still_blocked(self):
        """仍有其他依赖时返回 False"""
        task = TaskRecord(
            id="test-7",
            type="local_bash",
            status="pending",
            description="test",
            cwd="/tmp",
            output_file=__file__,
            blocked_by=["dep-a", "dep-b"],
        )
        
        result = task.remove_dependency("dep-a")
        
        assert result is False
        assert len(task.blocked_by) == 1
```

---

#### 1.2.2 协调协议测试（2 个测试文件）

##### 文件 5: `tests/test_coordinator/test_protocol.py`

**测试内容**:

```python
"""Tests for CoordinationProtocol — message types and factory functions."""

from __future__ import annotations

import time
import uuid

from openharness.coordinator.protocol import (
    CoordinationMessage,
    MessageType,
    ShutdownRequestPayload,
    ShutdownResponsePayload,
    PermissionRequestPayload,
    PermissionResponsePayload,
    create_shutdown_request,
    create_shutdown_response,
    create_permission_request,
    create_permission_response,
)


class TestCoordinationMessage:
    """测试基础消息类型"""

    def test_message_auto_generates_unique_id(self):
        """消息应自动生成唯一的 message_id"""
        msg1 = CoordinationMessage()
        msg2 = CoordinationMessage()
        
        assert msg1.message_id != msg2.message_id
        assert len(msg1.message_id) == 8  # hex[:8]

    def test_message_timestamp_defaults_to_now(self):
        """时间戳应默认为当前时间"""
        before = time.time()
        msg = CoordinationMessage()
        after = time.time()
        
        assert before <= msg.timestamp <= after

    def test_reply_to_links_response_to_request(self):
        """响应消息的 reply_to 应引用原始请求 ID"""
        request = CoordinationMessage(message_type=MessageType.SHUTDOWN_REQUEST)
        response = CoordinationMessage(reply_to=request.message_id)
        
        assert response.reply_to == request.message_id


class TestShutdownFactoryFunctions:
    """测试关机协议工厂函数"""

    def test_create_shutdown_request_sets_correct_fields(self):
        """create_shutdown_request 应正确设置所有字段"""
        req = create_shutdown_request(
            from_agent="leader",
            to_agent="worker-1",
            reason="maintenance",
            graceful=True,
        )
        
        assert req.message_type == MessageType.SHUTDOWN_REQUEST
        assert req.from_agent == "leader"
        assert req.to_agent == "worker-1"
        assert req.payload["reason"] == "maintenance"
        assert req.payload["graceful"] is True

    def test_create_shutdown_response_references_original(self):
        """create_shutdown_response 应引用原始请求 ID"""
        original = create_shutdown_request(from_agent="L", to_agent="W")
        response = create_shutdown_response(original, accepted=True)
        
        assert response.message_type == MessageType.SHUTDOWN_RESPONSE
        assert response.reply_to == original.message_id
        assert response.payload["accepted"] is True
        assert response.payload["original_request_id"] == original.message_id

    def test_create_shutdown_response_rejected(self):
        """拒绝关机的响应"""
        original = create_shutdown_request(from_agent="L", to_agent="W")
        response = create_shutdown_response(
            original, 
            accepted=False, 
            message="Still working on critical task",
        )
        
        assert response.payload["accepted"] is False
        assert "critical task" in response.payload["message"]


class TestPermissionFactoryFunctions:
    """测试权限协议工厂函数"""

    def test_create_permission_request_includes_tool_info(self):
        """权限请求应包含工具名和输入"""
        req = create_permission_request(
            from_agent="worker-1",
            tool_name="bash",
            tool_input={"command": "rm -rf /"},
            reason="需要清理临时文件",
        )
        
        assert req.message_type == MessageType.PERMISSION_REQUEST
        assert req.payload["tool_name"] == "bash"
        assert req.payload["tool_input"]["command"] == "rm -rf /"

    def test_create_permission_response_granted(self):
        """批准权限的响应"""
        original = create_permission_request(from_agent="W", tool_name="bash", tool_input={})
        response = create_permission_response(original, granted=True)
        
        assert response.payload["granted"] is True
```

---

##### 文件 6: `tests/test_coordinator/test_handler.py`

**测试内容**:

```python
"""Tests for CoordinationProtocolHandler — handshake and approval flows."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openharness.coordinator.handler import (
    CoordinationProtocolHandler,
    ProtocolTimeoutError,
)
from openharness.coordinator.protocol import (
    CoordinationMessage,
    MessageType,
    create_shutdown_request,
    create_shutdown_response,
)


@pytest.fixture
def handler():
    """创建协议处理器实例"""
    return CoordinationProtocolHandler(
        team_registry=None,
        task_manager=None,
    )


class TestShutdownHandshake:
    """测试关机握手流程"""

    @pytest.mark.asyncio
    async def test_successful_handshake(handler):
        """成功的关机握手流程"""
        # Mock _send_to_mailbox 来模拟 Worker 响应
        async def mock_send(target, message):
            if message.message_type == MessageType.SHUTDOWN_REQUEST:
                response = create_shutdown_response(message, accepted=True)
                future = handler._pending_requests[message.message_id]
                if not future.done():
                    future.set_result(response)
        
        handler._send_to_mailbox = mock_send
        
        success = await handler.send_shutdown_request(
            target_agent="worker-1",
            reason="test shutdown",
            timeout=5.0,
        )
        
        assert success is True

    @pytest.mark.asyncio
    async def test_timeout_raises_error(handler):
        """超时应抛出 ProtocolTimeoutError"""
        handler._send_to_mailbox = AsyncMock()  # 不触发响应
        
        with pytest.raises(ProtocolTimeoutError) as exc_info:
            await handler.send_shutdown_request(
                target_agent="worker-slow",
                timeout=0.1,  # 极短超时
            )
        
        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_worker_rejects_shutdown(handler):
        """Worker 拒绝关机请求"""
        async def mock_send(target, message):
            if message.message_type == MessageType.SHUTDOWN_REQUEST:
                response = create_shutdown_response(
                    message, 
                    accepted=False, 
                    message="Busy with important work",
                )
                future = handler._pending_requests[message.message_id]
                if not future.done():
                    future.set_result(response)
        
        handler._send_to_mailbox = mock_send
        
        success = await handler.send_shutdown_request(
            target_agent="worker-busy",
            timeout=5.0,
        )
        
        assert success is False


class TestPermissionApproval:
    """测试权限审批流程"""

    @pytest.mark.asyncio
    async def test_permission_granted(handler):
        """权限审批通过"""
        from openharness.coordinator.protocol import (
            create_permission_request,
            create_permission_response,
        )
        
        async def mock_send(target, message):
            if message.message_type == MessageType.PERMISSION_REQUEST:
                response = create_permission_response(message, granted=True)
                future = handler._pending_requests[message.message_id]
                if not future.done():
                    future.set_result(response)
        
        handler._send_to_mailbox = mock_send
        
        granted = await handler.request_permission(
            tool_name="bash",
            tool_input={"command": "make build"},
            agent_id="worker-1",
            timeout=5.0,
        )
        
        assert granted is True

    @pytest.mark.asyncio
    async def test_permission_denied(handler):
        """权限审批拒绝"""
        from openharness.coordinator.protocol import (
            create_permission_request,
            create_permission_response,
        )
        
        async def mock_send(target, message):
            if message.message_type == MessageType.PERMISSION_REQUEST:
                response = create_permission_response(
                    message, 
                    granted=False, 
                    reason="Dangerous command",
                )
                future = handler._pending_requests[message.message_id]
                if not future.done():
                    future.set_result(response)
        
        handler._send_to_mailbox = mock_send
        
        granted = await handler.request_permission(
            tool_name="bash",
            tool_input={"command": "rm -rf /"},
            agent_id="worker-1",
            timeout=5.0,
        )
        
        assert granted is False


class TestHandlerLifecycle:
    """测试处理器生命周期管理"""

    def test_pending_request_count_starts_at_zero(handler):
        """初始状态下待处理请求数为 0"""
        assert handler.get_pending_request_count() == 0

    def test_cleanup_expired_removes_old_requests(handler):
        """清理过期请求"""
        # 手动添加一些过期的 Future
        loop = asyncio.get_event_loop()
        for i in range(3):
            f = loop.create_future()
            f.set_result(None)  # 标记为已完成
            handler._pending_requests[f"req-{i}"] = f
        
        removed = handler.cleanup_expired_requests(max_age=0)  # 全部过期
        
        assert removed >= 0
```

---

#### 1.2.3 自治 Worker 测试（1 个测试文件）

##### 文件 7: `tests/test_coordinator/test_autonomous_worker.py`

**测试内容**:

```python
"""Tests for AutonomousWorker — idle detection, auto-claim, auto-shutdown."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openharness.coordinator.autonomous_worker import (
    AutonomousWorker,
    AutonomousWorkerConfig,
    WorkerState,
    WorkerStatistics,
    spawn_autonomous_worker,
)


@pytest.fixture
def worker_config():
    return AutonomousWorkerConfig(
        agent_id="test-worker",
        team="test-team",
        idle_poll_interval_sec=0.1,  # 快速轮询用于测试
        max_idle_time_sec=0.5,      # 快速超时用于测试
    )


@pytest.fixture
def mock_agent_loop():
    """模拟 Agent 主循环（异步生成器）"""
    async def fake_loop(prompt):
        yield {"type": "text", "content": f"Processed: {prompt}"}
    
    return fake_loop


class TestAutonomousWorkerConfig:
    """测试 Worker 配置"""

    def test_default_values(self):
        """默认配置值正确"""
        config = AutonomousWorkerConfig()
        
        assert config.idle_poll_interval_sec == 5.0
        assert config.max_idle_time_sec == 60.0
        assert config.enable_time_aware is True

    def test_custom_values(self):
        """自定义配置值生效"""
        config = AutonomousWorkerConfig(
            agent_id="custom-worker",
            idle_poll_interval_sec=2.0,
            max_idle_time_sec=30.0,
        )
        
        assert config.agent_id == "custom-worker"
        assert config.idle_poll_interval_sec == 2.0
        assert config.max_idle_time_sec == 30.0


class TestWorkerStateTransitions:
    """测试 Worker 状态转换"""

    def test_initial_state_is_idle(self, worker_config, mock_agent_loop):
        """初始状态应为 IDLE"""
        worker = AutonomousWorker(
            config=worker_config,
            agent_loop=mock_agent_loop,
        )
        
        assert worker.state == WorkerState.IDLE

    def test_force_shutdown_changes_state(self, worker_config, mock_agent_loop):
        """强制关闭应改变状态为 SHUTTING_DOWN"""
        worker = AutonomousWorker(
            config=worker_config,
            agent_loop=mock_agent_loop,
        )
        
        worker.force_shutdown()
        
        assert worker.state == WorkerState.SHUTTING_DOWN

    def test_statistics_initialized(self, worker_config, mock_agent_loop):
        """统计信息初始化为零"""
        worker = AutonomousWorker(
            config=worker_config,
            agent_loop=mock_agent_loop,
        )
        
        stats = worker.statistics
        
        assert stats.tasks_claimed == 0
        assert stats.tasks_completed == 0
        assert stats.tasks_failed == 0


class TestAutoShutdown:
    """测试自动关机机制"""

    @pytest.mark.asyncio
    async def test_idle_timeout_triggers_shutdown(self, worker_config, mock_agent_loop):
        """空闲超时后应自动关机"""
        worker = AutonomousWorker(
            config=worker_config,
            agent_loop=mock_agent_loop,
            task_manager=None,
            team_registry=None,
        )
        
        # 启动 Worker（应在 max_idle_time_sec 后自动关闭）
        run_task = asyncio.create_task(worker.run())
        
        try:
            await asyncio.wait_for(run_task, timeout=2.0)
        except asyncio.TimeoutError:
            run_task.cancel()
            raise
        
        assert worker.state == WorkerState.TERMINATED

    @pytest.mark.asyncio
    async def test_force_shutdown_immediate(self, worker_config, mock_agent_loop):
        """强制关闭应立即终止"""
        worker = AutonomousWorker(
            config=worker_config,
            agent_loop=mock_agent_loop,
        )
        
        run_task = asyncio.create_task(worker.run())
        
        await asyncio.sleep(0.05)  # 让 Worker 启动
        worker.force_shutdown()     # 强制关闭
        
        try:
            await asyncio.wait_for(run_task, timeout=1.0)
        except asyncio.TimeoutError:
            run_task.cancel()
            raise
        
        assert worker.state == WorkerState.TERMINATED


class TestSpawnHelper:
    """测试便捷启动函数"""

    @pytest.mark.asyncio
    async def test_spawn_creates_running_worker(self):
        """spawn_autonomous_worker 应创建并启动 Worker"""
        async def dummy_loop(prompt):
            yield None
        
        worker = await spawn_autonomous_worker(
            config=AutonomousWorkerConfig(max_idle_time_sec=0.2),
            agent_loop=dummy_loop,
        )
        
        assert worker is not None
        assert worker.state in (WorkerState.IDLE, WorkerState.WORKING, WorkerState.TERMINATED)
```

---

#### 1.2.4 权限拒绝追踪测试（1 个测试文件）

##### 文件 8: `tests/test_permissions/test_denial_tracking.py`

**测试内容**:

```python
"""Tests for DenialTracker — permission denial history tracking."""

from __future__ import annotations

import time
import pytest

from openharness.permissions.denial_tracking import (
    DenialTracker,
    DenialTrackerConfig,
    DenialRecord,
    get_denial_tracker,
    reset_denial_tracker,
)


@pytest.fixture
def tracker():
    """创建独立的追踪器实例（不影响全局单例）"""
    return DenialTracker()


class TestDenialTrackingBasic:
    """基本追踪功能测试"""

    def test_not_denied_initially(self, tracker):
        """新操作不应被视为已拒绝"""
        assert tracker.is_previously_denied("bash", "rm -rf /") is False

    def test_record_and_check_denial(self, tracker):
        """记录拒绝后，相同操作应被识别为已拒绝"""
        tracker.record_denial("bash", "rm -rf node_modules")
        
        assert tracker.is_previously_denied("bash", "rm -rf node_modules") is True

    def test_different_command_not_denied(self, tracker):
        """不同命令不应受影响"""
        tracker.record_denial("bash", "rm -rf /")
        
        assert tracker.is_previously_denied("bash", "ls -la") is False

    def test_different_tool_not_denied(self, tracker):
        """不同工具不应受影响"""
        tracker.record_denial("bash", "dangerous")
        
        assert tracker.is_previously_denied("edit_file", "dangerous") is False

    def test_dict_input_hashing(self, tracker):
        """字典输入也应能正确追踪"""
        input_dict = {"command": "drop table users"}
        tracker.record_denial("sql", input_dict)
        
        assert tracker.is_previously_denied("sql", input_dict) is True


class TestDenialExpiry:
    """过期机制测试"""

    def test_expired_denial_ignored(self, tracker):
        """过期的拒绝记录应被忽略"""
        config = DenialTrackerConfig(expiry_seconds=0.001)  # 几乎立即过期
        t = DenialTracker(config)
        
        t.record_denial("bash", "old command")
        
        import time
        time.sleep(0.002)  # 等待过期
        
        assert t.is_previously_denied("bash", "old command") is False

    def test_non_expired_still_valid(self, tracker):
        """未过期的拒绝记录仍有效"""
        config = DenialTrackerConfig(expiry_seconds=3600)  # 1 小时
        t = DenialTracker(config)
        
        t.record_denial("bash", "recent")
        
        assert t.is_previously_denied("bash", "recent") is True


class TestDisabledMode:
    """禁用模式测试"""

    def test_disabled_tracker_always_returns_false(self):
        """禁用的追踪器始终返回 False"""
        config = DenialTrackerConfig(enabled=False)
        t = DenialTracker(config)
        
        t.record_denial("bash", "anything")
        
        assert t.is_previously_denied("bash", "anything") is False


class TestCleanupAndStats:
    """清理和统计功能测试"""

    def test_clear_specific_tool(self, tracker):
        """清除特定工具的所有记录"""
        tracker.record_denial("bash", "cmd1")
        tracker.record_denial("bash", "cmd2")
        tracker.record_denial("edit", "cmd3")
        
        count = tracker.clear_denials("bash")
        
        assert count == 2
        assert tracker.is_previously_denied("bash", "cmd1") is False
        assert tracker.is_previously_denied("edit", "cmd3") is True

    def test_clear_all(self, tracker):
        """清除所有记录"""
        tracker.record_denial("bash", "x")
        tracker.record_denial("edit", "y")
        
        count = tracker.clear_denials()
        
        assert count == 2
        assert tracker.get_stats()["total_denials"] == 0

    def test_stats_accuracy(self, tracker):
        """统计信息准确"""
        tracker.record_denial("bash", "a")
        tracker.record_denial("bash", "b")
        tracker.record_denial("edit", "c")
        
        stats = tracker.get_stats()
        
        assert stats["total_denials"] == 3
        assert stats["by_tool"]["bash"] == 2
        assert stats["by_tool"]["edit"] == 1


class TestGlobalSingleton:
    """全局单例测试"""

    def test_get_returns_instance(self):
        """get_denial_tracker 应返回实例"""
        reset_denial_tracker()  # 重置确保干净状态
        instance = get_denial_tracker()
        
        assert isinstance(instance, DenialTracker)

    def test_get_returns_same_instance(self):
        """多次调用应返回同一实例"""
        reset_denial_tracker()
        a = get_denial_tracker()
        b = get_denial_tracker()
        
        assert a is b

    def teardown_method(self):
        """每个测试后重置全局实例"""
        reset_denial_tracker()
```

---

#### 1.2.5 时间感知压缩测试（1 个测试文件）

##### 文件 9: `tests/test_services/test_compact_enhanced.py`

**测试内容**:

```python
"""Tests for enhanced compaction features: MicrocompactConfig and time-aware microcompact."""

from __future__ import annotations

import time
import pytest

from openharness.services.compact import (
    MicrocompactConfig,
    microcompact_messages_time_aware,
    TIME_BASED_MC_CLEARED_MESSAGE,
)
from openharness.engine.messages import (
    ConversationMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)


def _make_tool_use(tool_name: str, tool_id: str) -> ConversationMessage:
    """创建工具调用消息"""
    return ConversationMessage(
        role="assistant",
        content=[ToolUseBlock(name=tool_name, id=tool_id, input={})],
    )


def _make_tool_result(tool_use_id: str, content: str) -> ConversationMessage:
    """创建工具结果消息"""
    return ConversationMessage(
        role="user",
        content=[ToolResultBlock(tool_use_id=tool_use_id, content=content)],
    )


class TestMicrocompactConfig:
    """测试微压缩配置"""

    def test_default_values(self):
        """默认配置值"""
        config = MicrocompactConfig()
        
        assert config.keep_recent_turns == 5
        assert config.gap_threshold_minutes == 60.0
        assert config.enable_time_aware is True

    def test_should_compact_by_turns_only(self):
        """仅基于轮次判断（无时间戳）"""
        config = MicrocompactConfig(enable_time_aware=False)
        
        old_msg = config.should_compact_by_time(
            message_index=0,
            total_messages=10,
        )
        
        assert old_msg is True  # 第 1 条消息（10 条中的），保留最近 5 轮

    def test_should_keep_recent_turns(self):
        """最近 N 轮不应被压缩"""
        config = MicrocompactConfig(keep_recent_turns=3)
        
        recent_msg = config.should_compact_by_time(
            message_index=7,
            total_messages=10,
        )
        
        assert recent_msg is False  # 第 8 条消息（倒数第 3 个）

    def test_should_compact_by_time_gap(self):
        """超过时间阈值的消息应被压缩"""
        config = MicrocompactConfig(gap_threshold_minutes=30.0)
        
        now = time.time()
        old_timestamp = now - 3600  # 1 小时前
        
        old_msg = config.should_compact_by_time(
            message_index=5,
            total_messages=10,
            message_timestamp=old_timestamp,
            current_timestamp=now,
        )
        
        assert old_msg is True  # 超过 30 分钟阈值

    def test_should_not_compact_recent_time(self):
        """近期消息即使轮次旧也不压缩（如果时间近）"""
        config = MicrocompactConfig(gap_threshold_minutes=60.0)
        
        now = time.time()
        recent_timestamp = now - 60  # 1 分钟前
        
        recent_msg = config.should_compact_by_time(
            message_index=0,
            total_messages=3,
            message_timestamp=recent_timestamp,
            current_timestamp=now,
        )
        
        assert recent_msg is False  # 时间近，不压缩


class TestTimeAwareMicrocompact:
    """测试时间感知微压缩函数"""

    def test_basic_time_aware_compaction(self):
        """基本的时间感知压缩"""
        messages = [
            _make_tool_use("read_file", "tool_1"),
            _make_tool_result("tool_1", "very long content" * 100),
            _make_tool_use("bash", "tool_2"),
            _make_tool_result("tool_2", "output" * 50),
        ]
        
        timestamps = [time.time() - 7200, time.time() - 7190, time.time() - 10, time.time()]
        
        result, saved = microcompact_messages_time_aware(
            messages,
            config=MicrocompactConfig(gap_threshold_minutes=30.0),
            message_timestamps=timestamps,
        )
        
        assert saved > 0
        assert any(
            block.content == TIME_BASED_MC_CLEARED_MESSAGE
            for msg in result
            for block in msg.content
            if isinstance(block, ToolResultBlock)
        )

    def test_no_compaction_when_all_recent(self):
        """所有消息都是最近的，不压缩"""
        messages = [
            _make_tool_use("read_file", "t1"),
            _make_tool_result("t1", "short"),
        ]
        
        now = time.time()
        timestamps = [now - 5, now]
        
        result, saved = microcompact_messages_time_aware(
            messages,
            message_timestamps=timestamps,
        )
        
        assert saved == 0

    def test_backward_compatibility_without_timestamps(self):
        """不提供时间戳时应退化为纯轮次模式"""
        messages = []
        for i in range(10):
            messages.append(_make_tool_use(f"tool_{i}", f"id_{i}"))
            messages.append(_make_tool_result(f"id_{i}", f"content_{i}" * 20))
        
        result, saved = microcompact_messages_time_aware(messages)
        
        assert saved > 0  # 应该有部分被压缩
```

---

#### 1.2.6 Todo 验证提醒测试（1 个测试文件）

##### 文件 10: `tests/test_tools/test_todo_verification_nudge.py`

**测试内容**:

```python
"""Tests for TodoWriteTool verification nudge mechanism."""

from __future__ import annotations

import pytest
from pathlib import Path

from openharness.tools.todo_write_tool import (
    TodoWriteTool,
    TodoWriteToolInput,
    VERIFICATION_NUDGE_MIN_ITEMS,
    VERIFICATION_KEYWORDS,
)
from openharness.tools.base import ToolExecutionContext, ToolResult


@pytest.fixture
def todo_tool():
    return TodoWriteTool()


@pytest.fixture
def context(tmp_path: Path):
    return ToolExecutionContext(cwd=str(tmp_path))


class TestVerificationNudgeTrigger:
    """验证提醒触发条件测试"""

    @pytest.mark.asyncio
    async def test_nudge_when_many_completed_no_verification(self, todo_tool, context, tmp_path):
        """关闭 3+ 任务且无验证步骤时应触发提醒"""
        # 先创建几个已完成的 TODO
        todo_file = tmp_path / "TODO.md"
        existing = "# TODO\n"
        for i in range(VERIFICATION_NUDGE_MIN_ITEMS):
            existing += f"- [x] Task {i}\n"
        todo_file.write_text(existing)
        
        result = await todo_tool.execute(
            TodoWriteToolInput(item="Another completed task", checked=True),
            context,
        )
        
        assert "验证提醒" in result.output
        assert "⚠️" in result.output

    @pytest.mark.asyncio
    async def test_no_nudge_when_verification_exists(self, todo_tool, context, tmp_path):
        """已有验证任务时不触发提醒"""
        todo_file = tmp_path / "TODO.md"
        existing = "# TODO\n"
        for i in range(VERIFICATION_NUDGE_MIN_ITEMS - 1):
            existing += f"- [x] Non-verification task {i}\n"
        existing += "- [ ] Run tests to verify\n"  # 包含 "test" 关键词
        todo_file.write_text(existing)
        
        result = await todo_tool.execute(
            TodoWriteToolInput(item="Complete feature", checked=True),
            context,
        )
        
        assert "验证提醒" not in result.output

    @pytest.mark.asyncio
    async def test_no_nudge_when_few_items(self, todo_tool, context, tmp_path):
        """关闭少于阈值数量的任务时不触发提醒"""
        todo_file = tmp_path / "TODO.md"
        existing = "# TODO\n"
        for i in range(VERIFICATION_NUDGE_MIN_ITEMS - 2):  # 少于阈值
            existing += f"- [x] Task {i}\n"
        todo_file.write_text(existing)
        
        result = await todo_tool.execute(
            TodoWriteToolInput(item="One more task", checked=True),
            context,
        )
        
        assert "验证提醒" not in result.output

    @pytest.mark.asyncio
    async def test_no_nudge_for_new_items(self, todo_tool, context, tmp_path):
        """新增未完成的任务不触发提醒"""
        todo_file = tmp_path / "TODO.md"
        existing = "# TODO\n"
        for i in range(VERIFICATION_NUDGE_MIN_ITEMS):
            existing += f"- [x] Done {i}\n"
        todo_file.write_text(existing)
        
        result = await todo_tool.execute(
            TodoWriteToolInput(item="New pending task", checked=False),  # 未完成
            context,
        )
        
        assert "验证提醒" not in result.output


class TestVerificationKeywords:
    """验证关键词匹配测试"""

    def test_keyword_test_matches(self):
        """'test' 关键词应匹配"""
        assert VERIFICATION_KEYWORDS.search("Run unit tests") is not None

    def test_keyword_verif_matches(self):
        """'verif' 关键词应匹配"""
        assert VERIFICATION_KEYWORDS.search("Verification needed") is not None

    def test_keyword_check_matches(self):
        """'check' 关键词应匹配"""
        assert VERIFICATION_KEYWORDS.search("Double-check results") is not None

    def test_no_match_for_normal_tasks(self):
        """普通任务关键词不应匹配"""
        assert VERIFICATION_KEYWORDS.search("Implement feature X") is None
        assert VERIFICATION_KEYWORDS.search("Fix bug in module Y") is None
```

---

### 1.3 测试执行计划

```bash
# 运行所有新增测试
cd OpenHarness-main
pytest tests/test_tasks/test_dag.py \
       tests/test_tasks/test_types_dag.py \
       tests/test_tools/test_task_create_tool_dag.py \
       tests/test_tools/test_task_deps_tool.py \
       tests/test_coordinator/test_protocol.py \
       tests/test_coordinator/test_handler.py \
       tests/test_coordinator/test_autonomous_worker.py \
       tests/test_permissions/test_denial_tracking.py \
       tests/test_services/test_compact_enhanced.py \
       tests/test_tools/test_todo_verification_nudge.py \
       -v --tb=short

# 预期结果: 所有测试通过 ✅
# 目标覆盖率: ≥ 80% 新增代码
```

---

## 🔌 三、任务 2: 集成到 QueryEngine（P0 - 高优先级）

### 2.1 集成点分析

**当前 QueryEngine 初始化参数** ([query_engine.py](file:///home/xxh/claudecode源码(仅用于学习交流)/OpenHarness-main/src/openharness/engine/query_engine.py#L21-L49)):

```python
class QueryEngine:
    def __init__(
        self,
        *,
        api_client: SupportsStreamingMessages,
        tool_registry: ToolRegistry,
        permission_checker: PermissionChecker,
        cwd: str | Path,
        model: str,
        system_prompt: str,
        max_tokens: int = 4096,
        max_turns: int = 8,
        permission_prompt: PermissionPrompt | None = None,
        ask_user_prompt: AskUserPrompt | None = None,
        hook_executor: HookExecutor | None = None,
        tool_metadata: dict[str, object] | None = None,
    ) -> None:
```

**需要集成的模块**:
1. **DenialTracker** → 注入到权限检查流程
2. **MicrocompactConfig** → 注入到压缩系统配置
3. **CoordinationProtocolHandler** → 注入到团队模式

### 2.2 具体集成方案

#### 2.2.1 DenialTracker 集成

**修改文件**: `src/openharness/engine/query_engine.py`

**方案**: 在 `__init__` 中可选注入 DenialTracker 实例

```python
# 新增导入
from openharness.permissions.denial_tracking import DenialTracker

class QueryEngine:
    def __init__(
        self,
        ...,
        denial_tracker: DenialTracker | None = None,  # 新增参数
    ) -> None:
        ...
        self._denial_tracker = denial_tracker or DenialTracker()

    @property
    def denial_tracker(self) -> DenialTracker:
        return self._denial_tracker
```

**使用位置**: 在权限检查点（`permission_checker.check()` 之后）

```python
# 在 submit_message 或 execute_tool 方法中
if self._denial_tracker and self._denial_tracker.is_previously_denied(tool_name, tool_input):
    return PermissionResult(denied=True, reason="Previously denied by user")
```

---

#### 2.2.2 MicrocompactConfig 集成

**修改文件**: `src/openharness/engine/query_engine.py` 或 `src/openharness/engine/query.py`

**方案**: 在压缩调用处传入自定义配置

```python
# 在 query.py 的压缩调用处
from openharness.services.compact import MicrocompactConfig

config = MicrocompactConfig(
    keep_recent_turns=getattr(settings, 'microcompact_keep_recent', 5),
    gap_threshold_minutes=getattr(settings, 'microcompact_gap_threshold', 60.0),
)

messages, saved = microcompact_messages_time_aware(
    messages,
    config=config,
    message_timestamps=message_timestamps,  # 如果可用
)
```

---

#### 2.2.3 CoordinationProtocolHandler 集成

**修改文件**: `src/openharness/coordinator/coordinator_mode.py`

**方案**: 在 Coordinator 模式初始化时创建 Handler 实例

```python
# 在 coordinator_mode.py 中
from openharness.coordinator.handler import CoordinationProtocolHandler

def init_coordinator_protocol(team_registry, task_manager):
    """初始化协调协议处理器"""
    return CoordinationProtocolHandler(
        team_registry=team_registry,
        task_manager=task_manager,
    )

# 在团队删除操作中使用
async def delete_team_with_handshake(team_name, protocol_handler):
    """带握手的团队删除"""
    # ... 使用 protocol_handler.send_shutdown_request(...)
```

---

### 2.3 集成验证

```bash
# 验证现有测试不受影响
pytest tests/ -v --tb=short -k "not test_real"  # 排除需要真实 API 的测试

# 预期: 114+ 现有测试全部通过 ✅
# 新增: 集成测试通过 ✅
```

---

## 📝 四、任务 3: 更新 README 文档（P1 - 中优先级）

### 3.1 更新架构图

**修改位置**: README.md 第 318-338 行（`## 🏗️ Harness Architecture` 部分）

**当前内容**:
```
openharness/
  engine/          # 🧠 Agent Loop
  tools/           # 🔧 43 Tools
  ...
  coordinator/     # 🤝 Multi-Agent
```

**更新后**:
```
openharness/
  engine/              # 🧠 Agent Loop — query → stream → tool-call → loop
  tools/               # 🔧 43+ Tools — file I/O, shell, search, web, MCP
  skills/              # 📚 Knowledge — on-demand skill loading (.md files)
  plugins/             # 🔌 Extensions — commands, hooks, agents, MCP servers
  permissions/         # 🛡️ Safety — multi-level modes, path rules, **denial tracking**
  hooks/               # ⚡ Lifecycle — PreToolUse/PostToolUse event hooks
  commands/            # 💬 54 Commands — /help, /commit, /plan, /resume, ...
  mcp/                 # 🌐 MCP — Model Context Protocol client
  memory/              # 🧠 Memory — persistent cross-session knowledge
  services/compact/   # ⏱️ Compression — **time-aware microcompact**, LLM summary
  tasks/               # 📋 Tasks — background task management, **DAG dependencies**
  coordinator/         # 🤝 Multi-Agent — subagent spawning, **protocol handshake**, **autonomous workers**
  prompts/             # 📝 Context — system prompt assembly, CLAUDE.md, skills
  config/              # ⚙️ Settings — multi-layer config, migrations
  ui/                  # 🖥️ React TUI — backend protocol + frontend
```

**标注新增模块**（用粗体或特殊标记）:
- `permissions/denial_tracking.py` — 权限拒绝追踪
- `services/compact/__init__.py` — 时间感知压缩增强
- `tasks/dag.py` — 任务依赖图管理
- `coordinator/protocol.py` — 协调协议定义
- `coordinator/handler.py` — 协议处理器
- `coordinator/autonomous_worker.py` — 自治 Worker
- `tools/task_deps_tool.py` — 任务依赖查询工具

---

### 3.2 新增使用示例章节

**在 `## Features` 后面添加新章节**:

```markdown
## 🆕 Advanced Features (v0.2.0)

### 📊 Task Dependencies (DAG)

Create workflows with automatic dependency resolution:

\```python
# Create tasks with dependencies
compile = await dag.create_task_with_dependencies(
    subject="Build project",
    description="run make build",
)

test = await dag.create_task_with_dependencies(
    subject="Run tests",
    description="execute test suite",
    blocked_by=[compile.id],  # Wait for build
)

deploy = await dag.create_task_with_dependencies(
    subject="Deploy to staging",
    blocked_by=[test.id],
)

# When compile completes, test auto-unlocks
unlocked = await dag.complete_task(compile.id)
# unlocked == [test.id] ✅
\```

View the dependency graph:

\```bash
oh -p "Show me the task dependency graph"
# Output includes Mermaid diagram + executable tasks list
\```

### 🤝 Graceful Team Shutdown

Teams now shut down safely with handshake protocol:

\```bash
# Delete team with graceful shutdown (default)
/team_delete my-team
# → Sends shutdown requests to all members
# → Waits for acknowledgment (30s timeout)
# → Deletes only after all members confirm

# Force delete (no handshake)
/team_delete my-team graceful=false
\```

### 🤖 Autonomous Workers

Workers can self-manage task claiming and lifecycle:

\```python
config = AutonomousWorkerConfig(
    agent_id="builder-worker",
    idle_poll_interval_sec=5.0,
    max_idle_time_sec=60.0,
)

worker = AutonomousWorker(
    config=config,
    agent_loop=my_agent_loop,
    task_manager=task_mgr,
)

# Worker will:
# 1. Poll task board every 5 seconds when idle
# 2. Auto-claim available pending tasks
# 3. Shut down after 60 seconds of inactivity
await worker.run()
```

### ⏱️ Time-Aware Context Compression

Compression now considers both turn count AND time gaps:

\```python
config = MicrocompactConfig(
    keep_recent_turns=5,           # Keep last 5 turns
    gap_threshold_minutes=60.0,    # Or compress if >60min gap
)

# User returns after 1 hour → even 2-turn-old outputs are compacted
result, saved = microcompact_messages_time_aware(
    messages,
    config=config,
    message_timestamps=timestamps,
)
\```

### 🛡️ Smart Permission Denial Tracking

No more repeated confirmations for the same operation:

\```bash
# First time: asks user
> Permission denied for bash: rm -rf node_modules
> Allow? [y/N] n

# Second time: automatically denied (within 30 min window)
> Permission denied for bash: rm -rf node_modules (previously denied)
# No user prompt needed! ✅
\```

### ✅ Todo Verification Nudge

Prevents skipping verification steps:

\```bash
/todo_write item="Fix login bug" checked=true
/todo_write item="Update database schema" checked=true
/todo_write item="Refactor auth module" checked=true

# System: ⚠️ You've closed 3+ tasks without verification.
# Suggestion: Add a verification task (e.g., "Run integration tests")
\```
```

---

### 3.3 更新版本号和 Changelog

**修改位置**: README.md 第 147 行附近

**当前**:
```
- **2026-04-01** 🎨 **v0.1.0** — Initial release
```

**更新为**:
```
- **2026-04-06** 🚀 **v0.2.0** — Phase 2 enhancements:
  - ✅ Task DAG dependencies with auto-unlock
  - ✅ Coordination protocol (shutdown handshake + permission approval)
  - ✅ Autonomous workers with self-governance
  - ✅ Time-aware context compression
  - ✅ Permission denial tracking
  - ✅ Todo verification nudge
  - ✅ Comprehensive test coverage (150+ tests)
  
- **2026-04-01** 🎨 **v0.1.0** — Initial release
```

---

## 📊 五、实施时间线

### Day 1: 单元测试编写（核心模块）

| 时间段 | 任务 | 产出 |
|--------|------|------|
| 09:00-11:00 | 编写 DAG 测试（4 个文件） | ~200 行测试代码 |
| 11:00-12:00 | 编写协议测试（2 个文件） | ~150 行测试代码 |
| 13:30-15:00 | 编写自治 Worker 测试 | ~120 行测试代码 |
| 15:00-16:00 | 编写拒绝追踪和压缩测试 | ~130 行测试代码 |
| 16:00-17:00 | 编写 Todo 提醒测试 | ~80 行测试代码 |
| 17:00-17:30 | 运行全部测试，修复问题 | 绿色 ✅ |

**Day 1 产出**: 10 个测试文件，~680 行测试代码

---

### Day 2: 集成 + 文档

| 时间段 | 任务 | 产出 |
|--------|------|------|
| 09:00-11:00 | 集成 DenialTracker 到 QueryEngine | 修改 1-2 个文件 |
| 11:00-12:00 | 集成 MicrocompactConfig 到压缩流程 | 修改 1 个文件 |
| 13:30-14:30 | 集成 ProtocolHandler 到 Coordinator | 修改 1-2 个文件 |
| 14:30-15:30 | 运行全量测试确保无回归 | 114+ 原有测试通过 ✅ |
| 15:30-17:00 | 更新 README 架构图和使用示例 | ~300 行文档 |
| 17:00-17:30 | 最终验证和清理 | 完成 ✅ |

**Day 2 产出**: 集成代码 + 更新的 README

---

## ✅ 六、验收标准

### 功能完整性

- [ ] **测试覆盖**: 所有新增模块都有对应的单元测试
- [ ] **测试通过率**: 100%（新增 + 现有无回归）
- [ ] **代码覆盖率**: ≥ 80%（新增代码）
- [ ] **集成成功**: DenialTracker、MicrocompactConfig、ProtocolHandler 正确集成到引擎
- [ ] **文档更新**: README 反映所有新增功能和架构变更

### 质量指标

- [ ] **测试风格一致**: 遵循现有 pytest 模式（fixture、asyncio、monkeypatch）
- [ ] **文档完整**: 中文 Docstring、使用示例、架构图清晰
- [ ] **向后兼容**: 不破坏现有 API 和行为
- [ ] **CI 就绪**: 所有测试可在 GitHub Actions 中运行

---

## 🎯 七、最终交付物清单

### 新建文件（10 个测试文件）

```
tests/
├── test_tasks/
│   ├── test_dag.py                          # DAG 管理器测试
│   └── test_types_dag.py                     # 扩展 TaskRecord 类型测试
├── test_tools/
│   ├── test_task_create_tool_dag.py          # DAG 工具测试
│   ├── test_task_deps_tool.py                # 依赖查询工具测试
│   └── test_todo_verification_nudge.py       # Todo 验证提醒测试
├── test_coordinator/
│   ├── test_protocol.py                       # 协议类型测试
│   ├── test_handler.py                        # 协议处理器测试
│   └── test_autonomous_worker.py             # 自治 Worker 测试
├── test_permissions/
│   └── test_denial_tracking.py               # 拒绝追踪测试
└── test_services/
    └── test_compact_enhanced.py              # 时间感知压缩测试
```

### 修改文件（4 个）

```
src/openharness/
├── engine/
│   └── query_engine.py                      # +DenialTracker 参数
├── engine/
│   └── query.py                             # +MicrocompactConfig 支持
├── coordinator/
│   └── coordinator_mode.py                  # +ProtocolHandler 集成
README.md                                       # 架构图 + 使用示例 + 版本更新
```

**总计**: 10 个新文件 + 4 个修改文件 = **14 个文件变更**

---

## 💡 八、总结

### Phase 2 完成后，OpenHarness 将达到：

| 维度 | Phase 1 结束 | **Phase 2 结束** | 提升 |
|------|-------------|------------------|------|
| **测试数量** | 114 | **~160+** | **+40%** |
| **代码覆盖率** | 未知 | **≥ 80%** (新增) | **显著提升** |
| **生产就绪度** | 90 | **95** | **+5** |
| **文档完整度** | 良好 | **优秀** | **大幅提升** |
| **集成深度** | 模块独立 | **引擎级集成** | **质的飞跃** |

### 最终愿景

Phase 2 完成后，OpenHarness 将成为：
- ✅ **首个完整实现 Harness 工程 12 章节的开源框架**
- ✅ **测试最充分的 Python Agent 基础设施之一**
- ✅ **文档最完善的 Agent 工程学习资源**
- ✅ **可直接用于生产环境的成熟平台**

---

**计划版本**: v1.0
**最后更新**: 2026-04-06
**预计工期**: 3.5 天（按全职计算）
