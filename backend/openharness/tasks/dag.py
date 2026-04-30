"""任务依赖图（DAG）管理器

参考实现: Claude Code src/utils/tasks.ts

提供任务依赖关系的创建、查询和自动解锁功能。
支持 DAG（有向无环图）结构的工作流编排。

使用示例:
    >>> dag = TaskDependencyGraph(task_manager)
    >>>
    >>> # 创建编译任务（无依赖）
    >>> compile_task = await dag.create_task_with_dependencies(
    ...     subject="编译项目",
    ...     description="运行 make build",
    ... )
    >>>
    >>> # 创建测试任务（依赖编译完成）
    >>> test_task = await dag.create_task_with_dependencies(
    ...     subject="运行测试",
    ...     description="执行测试套件",
    ...     blocked_by=[compile_task.id],
    ... )
    >>>
    >>> # 编译完成后，自动解锁测试任务
    >>> unlocked = await dag.complete_task(compile_task.id)
    >>> print(unlocked)  # [test_task.id]
"""

from __future__ import annotations

import logging
import time

from openharness.tasks.types import TaskRecord

log = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """循环依赖错误"""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"检测到循环依赖: {' -> '.join(cycle)}")


class TaskDependencyGraph:
    """任务依赖图管理器

    管理 task 之间的依赖关系，支持:
    - 创建带依赖的任务
    - 自动解锁（完成任务时解除后续任务的阻塞）
    - 查询可执行任务
    - DAG 可视化
    """

    def __init__(self, task_manager) -> None:
        """
        初始化 DAG 管理器

        Args:
            task_manager: BackgroundTaskManager 实例
        """
        self._task_manager = task_manager

    async def create_task_with_dependencies(
        self,
        subject: str,
        description: str,
        blocked_by: list[str] | None = None,
        blocks: list[str] | None = None,
        **kwargs,
    ) -> TaskRecord:
        """创建带依赖关系的任务

        Args:
            subject: 任务标题（简短）
            description: 详细描述
            blocked_by: 前置依赖任务 ID 列表（必须先完成这些任务）
            blocks: 后续被阻塞任务 ID 列表

        Returns:
            新创建的 TaskRecord

        Raises:
            ValueError: 依赖的任务不存在
            CircularDependencyError: 检测到循环依赖
        """
        # 验证前置依赖存在
        if blocked_by:
            for dep_id in blocked_by:
                dep_task = self._task_manager.get_task(dep_id)
                if dep_task is None:
                    raise ValueError(f"依赖任务不存在: {dep_id}")

            # 检测循环依赖
            self._check_circular_dependency(new_task_id=None, blocked_by=blocked_by)

        # 创建基础任务（通过 task_manager）
        if "command" in kwargs:
            task = await self._task_manager.create_shell_task(
                command=kwargs["command"],
                description=description or subject,
                cwd=kwargs.get("cwd", "."),
            )
        elif "prompt" in kwargs:
            task = await self._task_manager.create_agent_task(
                prompt=kwargs["prompt"],
                description=description or subject,
                cwd=kwargs.get("cwd", "."),
                model=kwargs.get("model"),
            )
        else:
            raise ValueError("必须提供 command 或 prompt 参数")

        # 设置增强字段
        task.subject = subject
        task.blocked_by = blocked_by or []
        task.blocks = blocks or []

        # 如果有未完成的前置依赖，状态保持 pending
        if task.blocked_by:
            has_unfinished_deps = any(
                self._is_task_unfinished(dep_id) for dep_id in task.blocked_by
            )
            if has_unfinished_deps:
                log.info(
                    "任务 %s (%s) 被阻塞，等待: %s",
                    task.id,
                    subject,
                    ", ".join(task.blocked_by),
                )

        return task

    async def complete_task(self, task_id: str) -> tuple[TaskRecord, list[str]]:
        """完成任务并自动解锁后续任务

        参考 Claude Code tasks.ts 的自动解锁机制:
        当一个任务完成时，系统会:
        1. 在所有其他任务的 blockedBy 列表中查找此任务 ID
        2. 找到后删除该 ID
        3. 如果某任务的 blockedBy 变空 → 任务自动解锁

        Args:
            task_id: 要完成的任务 ID

        Returns:
            (completed_task, unlocked_task_ids) 元组

        Raises:
            ValueError: 任务不存在
        """
        task = self._require_task(task_id)

        # 更新状态为完成
        task.status = "completed"
        task.ended_at = time.time()
        if task.progress is None:
            task.progress = 100

        log.info("任务 %s (%s) 已完成", task_id, task.subject)

        # 自动解锁被此任务阻塞的其他任务
        unlocked_tasks = []
        all_tasks = self._task_manager.list_tasks()

        for t in all_tasks:
            if task_id in t.blocked_by:
                # 移除已完成的依赖
                was_blocked = t.remove_dependency(task_id)

                if was_blocked and t.status == "pending":
                    unlocked_tasks.append(t.id)
                    log.info(
                        "任务 %s (%s) 已解锁（依赖 %s 完成）",
                        t.id,
                        t.subject or t.description,
                        task_id,
                    )

        return task, unlocked_tasks

    def get_executable_tasks(self) -> list[TaskRecord]:
        """获取当前可执行的任务列表

        条件:
        - status 为 pending 或 in_progress
        - 所有前置依赖都已完成（blockedBy 为空或都已完成）

        Returns:
            可执行的任务列表
        """
        executable = []

        for task in self._task_manager.list_tasks():
            if task.status not in ("pending", "running"):
                continue

            # 检查依赖是否都已完成
            deps_met = (
                all(self._is_task_finished(dep_id) for dep_id in task.blocked_by)
                if task.blocked_by
                else True
            )

            if deps_met:
                executable.append(task)

        return executable

    def get_blocked_tasks(self) -> list[TaskRecord]:
        """获取被阻塞的任务列表"""
        return [task for task in self._task_manager.list_tasks() if task.is_blocked]

    def visualize_dag(self) -> str:
        """生成 DAG 的文本可视化（Mermaid 格式）

        Returns:
            Mermaid graph 语法的字符串
        """
        lines = ["graph LR"]
        tasks = self._task_manager.list_tasks()

        for task in tasks:
            # 显示节点
            label = task.subject or task.description[:30]
            node_id = task.id[:8]  # 截断显示
            lines.append(f'  {node_id}["{label}"]')

            # 显示依赖边
            for dep_id in task.blocked_by:
                dep_short = dep_id[:8]
                lines.append(f"  {dep_short} --> {node_id}")

        return "\n".join(lines)

    def get_task_chain(self, task_id: str) -> list[str]:
        """获取任务的完整依赖链（从根到当前任务）

        Args:
            task_id: 目标任务 ID

        Returns:
            依赖链（从最早的前置依赖到目标任务）
        """
        chain = []
        visited = set()
        current_id = task_id

        while current_id and current_id not in visited:
            visited.add(current_id)
            chain.append(current_id)

            task = self._task_manager.get_task(current_id)
            if task and task.blocked_by:
                # 取第一个依赖作为上游
                current_id = task.blocked_by[0]
            else:
                break

        chain.reverse()  # 从根到叶
        return chain

    def _check_circular_dependency(
        self,
        new_task_id: str | None,
        blocked_by: list[str],
        visiting: set[str] | None = None,
        depth: int = 0,
        max_depth: int = 1000,
    ) -> None:
        """检测循环依赖（DFS）

        Raises:
            CircularDependencyError: 如果检测到环或依赖链过深
        """
        if depth > max_depth:
            raise CircularDependencyError([f"...(depth>{max_depth})"])

        if visiting is None:
            visiting = set()

        for dep_id in blocked_by:
            if dep_id == new_task_id:
                raise CircularDependencyError([new_task_id, dep_id])

            if dep_id in visiting:
                continue

            visiting.add(dep_id)
            dep_task = self._task_manager.get_task(dep_id)
            if dep_task and dep_task.blocked_by:
                self._check_circular_dependency(new_task_id, dep_task.blocked_by, visiting, depth + 1, max_depth)
            visiting.discard(dep_id)

    def _require_task(self, task_id: str) -> TaskRecord:
        """获取任务，不存在则抛出异常"""
        task = self._task_manager.get_task(task_id)
        if task is None:
            raise ValueError(f"任务不存在: {task_id}")
        return task

    def _is_task_finished(self, task_id: str) -> bool:
        """检查任务是否已完成"""
        task = self._task_manager.get_task(task_id)
        return task is not None and task.status == "completed"

    def _is_task_unfinished(self, task_id: str) -> bool:
        task = self._task_manager.get_task(task_id)
        return task is not None and task.status != "completed"
