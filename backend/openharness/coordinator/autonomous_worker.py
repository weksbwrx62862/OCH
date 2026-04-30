"""自治 Worker 模块

参考实现: Claude Code src/utils/swarm/inProcessRunner.ts

提供 Worker 的自治能力:
1. 空闲检测与自动认领任务
2. 定期轮询收件箱和任务看板
3. 超时自动关机（节省资源）
4. 身份信息注入（防止上下文压缩后忘记身份）

状态机:
    idle → working (认领到任务或收到消息)
    working → idle (任务完成)
    idle → shutting_down (超时无任务)
    shutting_down → terminated
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Awaitable, Any

log = logging.getLogger(__name__)


class WorkerState(str, Enum):
    """Worker 状态"""

    IDLE = "idle"
    WORKING = "working"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


@dataclass
class AutonomousWorkerConfig:
    """自治 Worker 配置"""

    agent_id: str = field(default_factory=lambda: f"worker-{uuid.uuid4().hex[:6]}")
    team: str = "default"

    # 轮询间隔
    idle_poll_interval_sec: float = 5.0  # 空闲时轮询间隔（秒）
    work_check_interval_sec: float = 1.0  # 工作时检查间隔（秒）

    # 超时设置
    max_idle_time_sec: float = 60.0  # 最大空闲时间（超时自动关机）

    # 身份注入
    min_context_length: int = 500  # 最小上下文长度（低于则重新注入身份）


@dataclass
class WorkerStatistics:
    """Worker 运行统计"""

    tasks_claimed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    messages_processed: int = 0
    total_uptime_sec: float = 0.0
    idle_time_sec: float = 0.0


class AutonomousWorker:
    """自治 Worker：可自主认领任务、自动管理生命周期

    与传统被动 Worker（等待 Leader 分配任务）不同，
    自治 Worker 会主动:
    - 从任务看板认领 pending 任务
    - 处理收件箱消息
    - 在空闲超时后自动关机

    参考 Claude Code inProcessRunner.ts 的空闲检测逻辑
    """

    def __init__(
        self,
        config: AutonomousWorkerConfig,
        agent_loop: Callable[[str], Awaitable[Any]],
        task_manager=None,
        team_registry=None,
        memory=None,
    ):
        """
        初始化自治 Worker

        Args:
            config: Worker 配置
            agent_loop: Agent 主循环函数（接收 prompt，返回异步迭代器）
            task_manager: 任务管理器实例
            team_registry: 团队注册表实例
            memory: Agent 记忆管理器实例（可选，传入后自动在任务执行前后使用记忆）
        """
        self._config = config
        self._agent_loop = agent_loop
        self._tasks = task_manager
        self._team = team_registry
        self.memory = memory

        # 状态
        self._state = WorkerState.IDLE
        self._current_task_id: Optional[str] = None
        self._last_activity_time = time.time()

        # 统计
        self._stats = WorkerStatistics()
        self._start_time = time.time()

    @property
    def state(self) -> WorkerState:
        return self._state

    @property
    def agent_id(self) -> str:
        return self._config.agent_id

    @property
    def statistics(self) -> WorkerStatistics:
        return self._stats

    async def run(self) -> None:
        """
        Worker 主循环

        状态机实现:
        - idle: 轮询任务看板和收件箱
        - working: 执行已认领的任务
        - shutting_down: 清理资源
        """
        log.info(
            "[Worker %s] 启动 (team=%s, poll=%.1fs, timeout=%.1fs)",
            self._config.agent_id,
            self._config.team,
            self._config.idle_poll_interval_sec,
            self._config.max_idle_time_sec,
        )

        try:
            while self._state != WorkerState.SHUTTING_DOWN:
                if self._state == WorkerState.IDLE:
                    await self._idle_loop()
                elif self._state == WorkerState.WORKING:
                    await self._work_loop()

                # 检查空闲超时
                await self._check_idle_timeout()

            # 执行关闭清理
            await self._cleanup()

        except asyncio.CancelledError:
            log.info("[Worker %s] 被外部取消", self._config.agent_id)
            await self._cleanup()
        except Exception as e:
            log.error("[Worker %s] 异常退出: %s", self._config.agent_id, e)
            raise

    async def _idle_loop(self) -> None:
        """
        空闲循环：轮询收件箱和任务看板

        参考 Claude Code inProcessRunner.ts 的空闲检测逻辑:
        - 工作阶段：每轮检查收件箱
        - 空闲阶段：每 5 秒轮询收件箱 + 任务看板
        """
        log.debug("[Worker %s] 进入空闲状态", self._config.agent_id)

        while self._state == WorkerState.IDLE:
            # 1. 检查收件箱新消息
            mailbox_messages = self._read_mailbox()
            if mailbox_messages:
                log.info(
                    "[Worker %s] 收到 %d 条新消息",
                    self._config.agent_id,
                    len(mailbox_messages),
                )
                self._stats.messages_processed += len(mailbox_messages)
                self._last_activity_time = time.time()
                self._state = WorkerState.WORKING
                return

            # 2. 检查任务看板是否有可认领的任务
            claimable = self._get_claimable_tasks()
            if claimable:
                # 自动认领第一个可用任务
                task = await self._claim_task(claimable[0])
                if task:
                    self._current_task_id = task.id
                    self._stats.tasks_claimed += 1
                    self._last_activity_time = time.time()

                    log.info(
                        "[Worker %s] 认领任务 %s (%s)",
                        self._config.agent_id,
                        task.id[:8],
                        task.subject or task.description[:40],
                    )

                    self._state = WorkerState.WORKING
                    return

            # 3. 更新空闲时间统计
            await asyncio.sleep(self._config.idle_poll_interval_sec)
            self._stats.idle_time_sec += self._config.idle_poll_interval_sec

    async def _work_loop(self) -> None:
        """
        工作循环：执行任务或处理消息
        """
        if not self._current_task_id:
            # 如果没有当前任务，可能是由消息触发的
            # Phase 3 待实现: 消息处理逻辑（当前直接返回空闲）
            log.debug("[Worker %s] 收到消息但无当前任务，跳过", self._config.agent_id)
            self._state = WorkerState.IDLE
            return

        task = self._tasks.get_task(self._current_task_id) if self._tasks else None
        if not task:
            log.warning("[Worker %s] 任务 %s 不存在", self._config.agent_id, self._current_task_id)
            self._current_task_id = None
            self._state = WorkerState.IDLE
            return

        log.info(
            "[Worker %s] 开始执行任务 %s",
            self._config.agent_id,
            task.subject or task.description[:40],
        )

        # 更新任务状态
        if self._tasks:
            await self._tasks.update_task(
                self._current_task_id,
                status="running",
                status_note=f"{self._config.agent_id} is {task.active_form or 'working on this'}",
            )

        # 执行任务（调用 Agent 循环）
        try:
            prompt_to_use = task.prompt or task.description

            # 注入身份信息（如果需要）
            prompt_to_use = self._maybe_inject_identity(prompt_to_use)

            # 注入历史记忆作为上下文（如果有记忆系统）
            if self.memory is not None:
                prompt_to_use = await self._recall_memory_context(prompt_to_use, task)

            # 调用 Agent 循环执行任务
            async for event in self._agent_loop(prompt_to_use):
                self._last_activity_time = time.time()
                # Phase 3 待实现: 根据事件类型更新进度、状态等

            # 任务完成
            if self._tasks:
                await self._tasks.update_task(
                    self._current_task_id,
                    status="completed",
                    progress=100,
                )

            self._stats.tasks_completed += 1

            log.info(
                "[Worker %s] 任务 %s 完成",
                self._config.agent_id,
                self._current_task_id[:8] if self._current_task_id else "unknown",
            )

            # 记录任务结果到记忆
            if self.memory is not None:
                await self._remember_task_result(task, success=True)

            # 触发依赖解锁（如果使用了 DAG）
            # dag.complete_task(self._current_task_id)

        except Exception as e:
            log.error(
                "[Worker %s] 任务 %s 失败: %s",
                self._config.agent_id,
                self._current_task_id[:8] if self._current_task_id else "unknown",
                e,
            )

            if self._tasks:
                await self._tasks.update_task(
                    self._current_task_id,
                    status="failed",
                    status_note=str(e),
                )

            self._stats.tasks_failed += 1

            # 记录失败经验到记忆
            if self.memory is not None:
                await self._remember_task_result(task, success=False, error=str(e))

        finally:
            self._current_task_id = None
            self._state = WorkerState.IDLE

    async def _check_idle_timeout(self) -> None:
        """检查是否超过最大空闲时间"""
        idle_duration = time.time() - self._last_activity_time

        if self._state == WorkerState.IDLE and idle_duration > self._config.max_idle_time_sec:
            log.info(
                "[Worker %s] 空闲超时 (%.1fs > %.1fs)，准备关机",
                self._config.agent_id,
                idle_duration,
                self._config.max_idle_time_sec,
            )

            self._state = WorkerState.SHUTTING_DOWN

    def _get_claimable_tasks(self) -> list:
        """获取可认领的任务（pending 且无未完成依赖）"""
        if not self._tasks:
            return []

        all_pending = self._tasks.list_tasks(status="pending")
        claimable = []

        for task in all_pending:
            # 检查是否有未完成的依赖（如果实现了 DAG）
            deps_met = True
            if hasattr(task, "blocked_by") and task.blocked_by:
                deps_met = all(
                (t := self._tasks.get_task(dep_id)) is not None
                and t.status == "completed"
                for dep_id in task.blocked_by
            )

            # 检查是否已被其他 Agent 认领
            not_owned = not hasattr(task, "owner") or not task.owner

            if deps_met and not_owned:
                claimable.append(task)

        return claimable

    async def _claim_task(self, task) -> Any:
        """认领任务"""
        if not self._tasks:
            return task

        # 更新任务的所有者
        try:
            updated = await self._tasks.update_task(
                task.id,
                # owner=self._config.agent_id,  # 如果 TaskRecord 支持 owner 字段
            )
            return updated or task
        except Exception as e:
            log.warning("[Worker %s] 认领任务失败: %s", self._config.agent_id, e)
            return None

    def _read_mailbox(self) -> list:
        """读取收件箱新消息"""
        # Phase 3 待实现: 邮箱系统集成（当前返回空列表）
        return []

    def _maybe_inject_identity(self, prompt: str) -> str:
        """
        身份信息注入

        当上下文过短时（可能因为压缩），重新注入身份信息，
        防止 Worker 忘记自己是谁。

        参考 Claude Code inProcessRunner.ts 的身份注入逻辑
        """
        if len(prompt) < self._config.min_context_length:
            identity_info = (
                f"\n\n[Identity Reminder]\n"
                f"You are worker agent '{self._config.agent_id}' "
                f"in team '{self._config.team}'.\n"
                f"Your role is to execute tasks autonomously."
            )
            return prompt + identity_info
        return prompt

    async def _recall_memory_context(self, prompt: str, task) -> str:
        """从记忆中检索相关经验并追加到 prompt"""
        try:
            query_text = task.subject or task.description or ""
            relevant = await self.memory.recall(
                query_text,
                limit=3,
            )
            if relevant:
                context_lines = []
                for m in relevant:
                    tag_str = f" [{','.join(m.tags)}]" if m.tags else ""
                    context_lines.append(f"- {m.content}{tag_str}")
                memory_hint = (
                    "\n\n[Historical Experience]\n"
                    "Based on past tasks, here are relevant experiences:\n"
                    + "\n".join(context_lines)
                    + "\nUse this experience to improve your approach."
                )
                log.debug("[Worker %s] 注入 %d 条历史记忆", self._config.agent_id, len(relevant))
                return prompt + memory_hint
        except Exception as exc:
            log.warning("[Worker %s] 检索记忆失败: %s", self._config.agent_id, exc)
        return prompt

    async def _remember_task_result(self, task, success: bool, error: str | None = None) -> None:
        """将任务结果记录到记忆中"""
        try:
            subject = task.subject or task.description or "unknown"
            if success:
                content = f"成功完成任务 '{subject}'"
                category = "pattern"
                importance = 7
            else:
                content = f"任务 '{subject}' 失败: {error or '未知错误'}"
                category = "error"
                importance = 4

            tags = [subject.split()[0]] if subject else []
            await self.memory.remember(
                content=content,
                category=category,
                tags=tags,
                importance=importance,
                source_task_id=task.id if hasattr(task, "id") else None,
            )
        except Exception as exc:
            log.warning("[Worker %s] 记录记忆失败: %s", self._config.agent_id, exc)

    async def _cleanup(self) -> None:
        """清理资源"""
        self._state = WorkerState.TERMINATED
        self._stats.total_uptime_sec = time.time() - self._start_time

        log.info(
            "[Worker %s] 已关闭 (运行 %.1fs, 完成 %d 任务, 失败 %d)",
            self._config.agent_id,
            self._stats.total_uptime_sec,
            self._stats.tasks_completed,
            self._stats.tasks_failed,
        )

    def force_shutdown(self) -> None:
        """强制关闭（从外部调用）"""
        log.info("[Worker %s] 收到强制关闭信号", self._config.agent_id)
        self._state = WorkerState.SHUTTING_DOWN


async def spawn_autonomous_worker(
    config: AutonomousWorkerConfig | None = None,
    agent_loop: Callable[[str], Awaitable[Any]] | None = None,
    task_manager=None,
    team_registry=None,
) -> AutonomousWorker:
    """
    便捷函数：启动一个自治 Worker

    Args:
        config: Worker 配置（可选，使用默认值）
        agent_loop: Agent 主循环
        task_manager: 任务管理器
        team_registry: 团队注册表

    Returns:
        已启动的 Worker 实例（在后台运行）
    """
    if config is None:
        config = AutonomousWorkerConfig()

    worker = AutonomousWorker(
        config=config,
        agent_loop=agent_loop or (lambda p: __import__("asyncio").sleep(0)),
        task_manager=task_manager,
        team_registry=team_registry,
    )

    # 后台启动
    asyncio.create_task(worker.run())

    return worker
