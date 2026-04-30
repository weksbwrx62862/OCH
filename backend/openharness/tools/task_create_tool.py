"""Tool for creating background tasks with DAG dependency support."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from openharness.tasks.dag import TaskDependencyGraph
from openharness.tasks.manager import get_task_manager
from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class TaskCreateToolInput(BaseModel):
    """Arguments for task creation with dependency support."""

    type: str = Field(default="local_bash", description="Task type: local_bash or local_agent")
    description: str = Field(description="Short task description")

    # 基本参数
    command: str | None = Field(default=None, description="Shell command for local_bash")
    prompt: str | None = Field(default=None, description="Prompt for local_agent")
    model: str | None = Field(default=None)

    # 增强字段
    subject: str = Field(default="", description="Task title (short, optional)")

    # ===== DAG 依赖字段（新增）=====
    blocked_by: list[str] = Field(
        default_factory=list,
        description="Task IDs that must complete before this task can start (前置依赖)",
    )
    blocks: list[str] = Field(
        default_factory=list,
        description="Task IDs that are blocked by this task (后续阻塞)",
    )


class TaskCreateTool(BaseTool):
    """Create a background task with optional dependencies."""

    name = "task_create"
    description = (
        "Create a background shell or local-agent task. "
        "Supports specifying dependencies via blocked_by and blocks parameters."
    )
    input_model = TaskCreateToolInput

    async def execute(
        self, arguments: TaskCreateToolInput, context: ToolExecutionContext
    ) -> ToolResult:
        manager = get_task_manager()

        # 使用 DAG 管理器创建任务（支持依赖关系）
        dag = TaskDependencyGraph(manager)

        try:
            if arguments.type == "local_bash":
                if not arguments.command:
                    return ToolResult(
                        output="command is required for local_bash tasks", is_error=True
                    )

                task = await dag.create_task_with_dependencies(
                    subject=arguments.subject or arguments.description[:50],
                    description=arguments.description,
                    command=arguments.command,
                    cwd=context.cwd,
                    blocked_by=arguments.blocked_by,
                    blocks=arguments.blocks,
                )
            elif arguments.type == "local_agent":
                if not arguments.prompt:
                    return ToolResult(
                        output="prompt is required for local_agent tasks", is_error=True
                    )

                try:
                    task = await dag.create_task_with_dependencies(
                        subject=arguments.subject or arguments.description[:50],
                        description=arguments.description,
                        prompt=arguments.prompt,
                        cwd=context.cwd,
                        model=arguments.model,
                        api_key=os.environ.get("ANTHROPIC_API_KEY"),
                        blocked_by=arguments.blocked_by,
                        blocks=arguments.blocks,
                    )
                except ValueError as exc:
                    return ToolResult(output=str(exc), is_error=True)
            else:
                return ToolResult(output=f"unsupported task type: {arguments.type}", is_error=True)

            # 生成状态消息
            status_parts = [f"Created task {task.id} ({task.type})"]

            if task.is_blocked:
                status_parts.append(f"[BLOCKED by: {', '.join(task.blocked_by)}]")
            elif task.blocked_by and not task.is_blocked:
                status_parts.append("[Dependencies satisfied, ready to run]")

            if task.blocks:
                status_parts.append(f"[Blocks: {', '.join(task.blocks)}]")

            return ToolResult(output=" ".join(status_parts))

        except ValueError as exc:
            return ToolResult(output=str(exc), is_error=True)
