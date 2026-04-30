"""Tool for deleting teams with graceful shutdown handshake."""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from openharness.coordinator.coordinator_mode import get_team_registry
from openharness.coordinator.handler import CoordinationProtocolHandler, ProtocolTimeoutError
from openharness.tasks.manager import get_task_manager
from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult

log = logging.getLogger(__name__)


class TeamDeleteToolInput(BaseModel):
    """Arguments for deleting a team with graceful shutdown."""

    name: str = Field(description="Team name")
    graceful: bool = Field(
        default=True,
        description="Whether to perform graceful shutdown (wait for agents to acknowledge)",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Timeout for shutdown handshake (seconds)",
    )


class TeamDeleteTool(BaseTool):
    """Delete a team with optional graceful shutdown handshake.

    When graceful=True, sends shutdown requests to all team members and waits
    for acknowledgment before deleting the team. This prevents data loss and
    ensures clean termination.

    Reference: Claude Code src/utils/swarm/teamHelpers.ts
    """

    name = "team_delete"
    description = (
        "Delete a team. With graceful=True (default), performs shutdown handshake "
        "with all members before deletion."
    )
    input_model = TeamDeleteToolInput

    async def execute(
        self, arguments: TeamDeleteToolInput, context: ToolExecutionContext
    ) -> ToolResult:
        del context

        try:
            registry = get_team_registry()
            team = registry._require_team(arguments.name)

            if not arguments.graceful:
                # 强制删除（不等待确认）
                registry.delete_team(arguments.name)
                return ToolResult(output=f"Force deleted team {arguments.name}")

            # 优雅关闭：执行握手流程
            protocol = CoordinationProtocolHandler(
                team_registry=registry,
                task_manager=get_task_manager(),
            )

            shutdown_results = []

            # 向每个团队成员发送关机请求
            for agent_id in team.agents:
                try:
                    success = await protocol.send_shutdown_request(
                        target_agent=agent_id,
                        reason=f"Team {arguments.name} is being deleted",
                        graceful=True,
                        timeout=arguments.timeout_seconds,
                    )
                    status = "✅ 确认" if success else "❌ 拒绝"
                    shutdown_results.append((agent_id, status))

                except ProtocolTimeoutError:
                    log.warning("Agent %s 关机超时", agent_id)
                    shutdown_results.append((agent_id, f"⏰ 超时 ({arguments.timeout_seconds}s)"))

                except Exception as e:
                    log.error("Agent %s 关机失败: %s", agent_id, e)
                    shutdown_results.append((agent_id, f"❌ 错误: {str(e)}"))

            # 所有 Agent 处理完毕后，删除团队
            registry.delete_team(arguments.name)

            # 构建结果消息
            result_lines = [f"🗑️ 团队 **{arguments.name}** 已删除"]
            result_lines.append(f"\n**关机握手结果** ({len(shutdown_results)} 个成员):\n")

            for agent_id, status in shutdown_results:
                result_lines.append(f"- `{agent_id[:12]}`: {status}")

            succeeded = sum(1 for _, s in shutdown_results if "✅" in s)
            if succeeded == len(shutdown_results):
                result_lines.append("\n✅ 所有成员已优雅关闭")
            else:
                result_lines.append(f"\n⚠️ {succeeded}/{len(shutdown_results)} 成员优雅关闭")

            return ToolResult(output="\n".join(result_lines))

        except ValueError as exc:
            return ToolResult(output=str(exc), is_error=True)
