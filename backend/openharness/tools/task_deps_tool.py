"""Tool for viewing task dependency relationships."""

from __future__ import annotations

from pydantic import BaseModel, Field

from openharness.tasks.dag import TaskDependencyGraph
from openharness.tasks.manager import get_task_manager
from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class TaskDepsToolInput(BaseModel):
    """Arguments for viewing task dependencies."""

    action: str = Field(
        default="list",
        description="Action: list (show all), executable (show ready tasks), blocked (show blocked), visualize (Mermaid graph)",
    )
    task_id: str | None = Field(default=None, description="Task ID for detailed view")


class TaskDepsTool(BaseTool):
    """View and manage task dependencies."""

    name = "task_deps"
    description = (
        "Show task dependency graph, executable tasks, and blocked tasks. "
        "Useful for understanding workflow status."
    )
    input_model = TaskDepsToolInput

    async def execute(
        self, arguments: TaskDepsToolInput, context: ToolExecutionContext
    ) -> ToolResult:
        manager = get_task_manager()
        dag = TaskDependencyGraph(manager)

        if arguments.action == "executable":
            # 显示可执行的任务
            executable = dag.get_executable_tasks()

            if not executable:
                return ToolResult(
                    output="No executable tasks. All tasks are either completed or blocked."
                )

            result = f"## 可执行任务 ({len(executable)})\n\n"
            for task in executable:
                status_icon = "▶️" if task.status == "pending" else "🔄"
                result += f"- {status_icon} **{task.subject or task.description[:40]}** (`{task.id[:8]}`)\n"

            return ToolResult(output=result)

        elif arguments.action == "blocked":
            # 显示被阻塞的任务
            blocked = dag.get_blocked_tasks()

            if not blocked:
                return ToolResult(output="No blocked tasks. All pending tasks are ready to run.")

            result = f"## 被阻塞的任务 ({len(blocked)})\n\n"
            for task in blocked:
                deps_info = ", ".join(f"`{dep_id[:8]}`" for dep_id in task.blocked_by)
                result += f"- 🚫 **{task.subject or task.description[:40]}** (`{task.id[:8]}`) - 等待: {deps_info}\n"

            return ToolResult(output=result)

        elif arguments.action == "visualize":
            # 生成 DAG 可视化
            viz = dag.visualize_dag()

            result = "## 任务依赖图 (DAG)\n\n"
            result += "```mermaid\n"
            result += viz
            result += "\n```\n\n"

            # 添加统计信息
            all_tasks = manager.list_tasks()
            total = len(all_tasks)
            completed = sum(1 for t in all_tasks if t.status == "completed")
            pending = sum(1 for t in all_tasks if t.status == "pending")
            running = sum(1 for t in all_tasks if t.status == "running")

            result += f"**统计**: 总计 {total} | ✅ 已完成 {completed} | ⏳ 待执行 {pending} | 🔄 运行中 {running}\n"

            return ToolResult(output=result)

        else:  # 默认: list
            # 显示所有任务及其依赖关系
            all_tasks = manager.list_tasks()

            if not all_tasks:
                return ToolResult(output="No tasks found.")

            result = f"## 所有任务 ({len(all_tasks)})\n\n"

            for task in all_tasks:
                # 状态图标
                status_icons = {
                    "completed": "✅",
                    "running": "🔄",
                    "pending": "⏳",
                    "failed": "❌",
                    "killed": "⛔",
                }
                icon = status_icons.get(task.status, "❓")

                subject = task.subject or task.description[:50]
                result += f"### {icon} {subject}\n"
                result += f"- **ID**: `{task.id[:12]}`\n"
                result += f"- **状态**: {task.status}\n"

                if task.blocked_by:
                    deps = ", ".join(f"`{d[:8]}`" for d in task.blocked_by)
                    result += f"- **前置依赖**: {deps}\n"

                if task.blocks:
                    blocks = ", ".join(f"`{b[:8]}`" for b in task.blocks)
                    result += f"- **后续阻塞**: {blocks}\n"

                if task.owner:
                    result += f"- **认领者**: `{task.owner}`\n"

                if task.progress is not None:
                    result += f"- **进度**: {task.progress}%\n"

                result += "\n"

            return ToolResult(output=result)
