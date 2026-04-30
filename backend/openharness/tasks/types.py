"""Task data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

TaskType = Literal["local_bash", "local_agent", "remote_agent", "in_process_teammate"]
TaskStatus = Literal["pending", "running", "completed", "failed", "killed"]


@dataclass
class TaskRecord:
    """Runtime representation of a background task with DAG dependency support.

    参考 Claude Code src/utils/tasks.ts 第 76-88 行实现
    新增 blocks/blockedBy 字段支持任务依赖图
    """

    id: str
    type: TaskType
    status: TaskStatus
    description: str
    cwd: str
    output_file: Path
    command: str | None = None
    prompt: str | None = None

    # 基本增强字段
    subject: str = ""  # 任务标题（简短描述）
    active_form: str | None = None  # 进行时形式（如 "Running tests"）
    owner: str | None = None  # Agent ID（认领此任务的 Agent）

    # ===== DAG 依赖字段（新增）=====
    blocks: list[str] = field(default_factory=list)  # 此任务阻塞的任务 ID 列表
    blocked_by: list[str] = field(default_factory=list)  # 阻塞此任务的任务 ID 列表

    # 时间戳
    created_at: float = 0.0
    started_at: float | None = None
    ended_at: float | None = None

    # 执行结果
    return_code: int | None = None

    # 元数据和进度
    metadata: dict[str, str] = field(default_factory=dict)
    progress: int | None = None  # 进度百分比 (0-100)

    @property
    def is_executable(self) -> bool:
        """检查任务是否可执行（无未完成的依赖）"""
        return len(self.blocked_by) == 0 and self.status in ("pending", "running")

    @property
    def is_blocked(self) -> bool:
        """检查任务是否被阻塞"""
        return len(self.blocked_by) > 0 and self.status == "pending"

    def add_dependency(self, task_id: str) -> None:
        """添加前置依赖任务"""
        if task_id not in self.blocked_by:
            self.blocked_by.append(task_id)

    def remove_dependency(self, task_id: str) -> bool:
        """移除已完成的前置依赖，返回是否解除阻塞"""
        if task_id in self.blocked_by:
            self.blocked_by.remove(task_id)
            return len(self.blocked_by) == 0  # 所有依赖都完成了
        return False
