"""Tool for maintaining a project TODO file with verification nudge.

参考 Claude Code src/tools/TodoWriteTool/TodoWriteTool.ts
增强功能：当关闭多个任务时自动提醒添加验证步骤
V2 统一集成：底层可选使用 Task 系统作为数据源
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult

log = logging.getLogger(__name__)

# 验证提醒配置
VERIFICATION_NUDGE_MIN_ITEMS = 3  # 最少关闭 N 个任务才触发提醒
VERIFICATION_KEYWORDS = re.compile(
    r"verif|test|check|valid|review|assert",
    re.IGNORECASE,
)


class TodoWriteToolInput(BaseModel):
    """Arguments for TODO writes."""

    item: str = Field(description="TODO item text")
    checked: bool = Field(default=False)
    path: str = Field(default="TODO.md")
    use_task_system: bool = Field(
        default=False,
        description="If True, also create/update a Task in the TaskManager",
    )


class TodoWriteTool(BaseTool):
    """Append an item to a TODO markdown file with optional verification reminder.

    Enhanced with verification nudge mechanism:
    When closing multiple items (>=3) without any verification step,
    automatically suggests adding a verification task.

    V2 Enhancement:
    Optional integration with Task system for unified task tracking.
    """

    name = "todo_write"
    description = (
        "Append a TODO item to a markdown checklist file. "
        "When marking items complete, may suggest adding verification steps. "
        "Optionally sync with Task system via use_task_system=True."
    )
    input_model = TodoWriteToolInput

    async def execute(
        self, arguments: TodoWriteToolInput, context: ToolExecutionContext
    ) -> ToolResult:
        path = Path(context.cwd) / arguments.path
        prefix = "- [x]" if arguments.checked else "- [ ]"
        existing = path.read_text(encoding="utf-8") if path.exists() else "# TODO\n"
        updated = existing.rstrip() + f"\n{prefix} {arguments.item}\n"
        path.write_text(updated, encoding="utf-8")

        result_parts = [f"Updated {path}"]

        if arguments.use_task_system:
            task_result = self._sync_to_task_system(arguments, context)
            if task_result:
                result_parts.append(task_result)

        if arguments.checked:
            result_parts.append(self._check_verification_nudge(existing))

        return ToolResult(output="\n".join(filter(None, result_parts)))

    def _sync_to_task_system(
        self, arguments: TodoWriteToolInput, context: ToolExecutionContext
    ) -> str | None:
        """将 TODO 同步到 Task 系统（V2 统一集成）"""
        try:
            from openharness.tasks.manager import get_task_manager

            manager = get_task_manager()

            if not arguments.checked:
                manager.create_task(
                    description=arguments.item,
                    status="pending",
                    source="todo_write",
                )
                return f"[Task V2] 已创建任务: {arguments.item}"
            else:
                tasks = manager.get_all_tasks()
                item_stripped = arguments.item.strip()
                for t in tasks:
                    if t.description.strip() == item_stripped:
                        manager.update_task_status(t.id, "completed")
                        return f"[Task V2] 已完成任务: {t.id}"
                    if item_stripped in t.description and t.source == "todo_write":
                        manager.update_task_status(t.id, "completed")
                        return f"[Task V2] 已完成匹配任务: {t.id}"
            return None
        except Exception as e:
            log.debug("Task 系统同步失败（非致命）: %s", e)
            return None

    def _check_verification_nudge(self, existing_content: str) -> str | None:
        """检查是否需要提醒添加验证步骤

        参考 Claude Code TodoWriteTool.ts 第 245-255 行:
        如果关闭了 3+ 个任务且没有验证步骤，提醒添加验证

        Args:
            existing_content: 更新前的 TODO 文件内容

        Returns:
            提醒消息（如果需要），否则返回 None
        """
        completed_items = re.findall(r"- \[x\]\s+(.+)", existing_content)

        if len(completed_items) < VERIFICATION_NUDGE_MIN_ITEMS - 1:
            return None

        all_items = re.findall(r"- \[[ x]\]\s+(.+)", existing_content)
        has_verification = any(VERIFICATION_KEYWORDS.search(item) for item in all_items)

        if has_verification:
            log.debug("TODO 已包含验证步骤，跳过提醒")
            return None

        nudge_msg = (
            "\n⚠️ **验证提醒**: 您已关闭多个任务。"
            "建议添加一个验证任务（如 '验证功能正常' 或 '运行测试套件'）"
            "以确保所有更改都经过验证。"
        )

        log.info("触发 TODO 验证提醒 (已完成 %d 个任务)", len(completed_items))

        return nudge_msg
