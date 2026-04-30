"""团队协调协议：请求-响应 + 唯一 ID 模式

参考实现:
- Claude Code src/utils/swarm/teamHelpers.ts (关机握手)
- Claude Code src/utils/swarm/permissionSync.ts (权限审批)

提供团队协作中的标准化通信协议，包括:
1. 关机握手流程 (Shutdown Handshake)
2. 权限审批流程 (Permission Approval)
3. 任务认领通知 (Task Claiming)

所有消息都使用 message_id 和 reply_to 实现请求-响应匹配。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MessageType(Enum):
    """协调消息类型"""

    # 通用消息
    TEXT = "text"
    NOTIFICATION = "notification"

    # 关机协议
    SHUTDOWN_REQUEST = "shutdown_request"  # Leader → Worker: 请求关机
    SHUTDOWN_RESPONSE = "shutdown_response"  # Worker → Leader: 确认关机

    # 权限协议
    PERMISSION_REQUEST = "permission_request"  # Worker → Leader: 请求权限
    PERMISSION_RESPONSE = "permission_response"  # Leader → Worker: 权限结果

    # 任务相关
    TASK_CLAIMED = "task_claimed"  # Worker → Team: 任务被认领
    TASK_COMPLETED = "task_completed"  # Worker → Team: 任务完成
    IDLE_NOTIFICATION = "idle_notification"  # Worker → Leader: 空闲通知


@dataclass
class CoordinationMessage:
    """协调消息（带唯一 ID）

    所有团队间通信都使用此格式，确保:
    - 每条消息有唯一的 message_id
    - 响应消息引用原始请求的 reply_to
    - 支持超时和重试机制
    """

    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    message_type: MessageType = MessageType.TEXT

    from_agent: str = ""  # 发送者 Agent ID
    to_agent: str = ""  # 接收者 Agent ID（空=广播）

    payload: dict[str, Any] = field(default_factory=dict)

    timestamp: float = field(default_factory=time.time)

    # 用于请求-响应匹配
    reply_to: Optional[str] = None  # 引用原始请求的 message_id

    # 状态
    read: bool = False


# ===== 关机协议 =====


@dataclass
class ShutdownRequestPayload:
    """关机请求内容"""

    reason: str = "Leader requested shutdown"
    graceful: bool = True  # 是否优雅关闭（允许收尾工作）
    timeout_seconds: float = 30.0  # 超时时间


@dataclass
class ShutdownResponsePayload:
    """关机响应内容"""

    accepted: bool  # 是否接受关机
    original_request_id: str  # 对应的原始请求 ID
    message: str = ""
    tasks_completed: int = 0  # 收尾完成的任务数


# ===== 权限协议 =====


@dataclass
class PermissionRequestPayload:
    """权限请求内容（Worker → Leader）"""

    tool_name: str  # 需要权限的工具名
    tool_input: dict[str, Any]  # 工具输入参数
    reason: str = ""  # 申请理由
    timeout: float = 30.0  # 等待批准的超时时间（秒）


@dataclass
class PermissionResponsePayload:
    """权限响应内容（Leader → Worker）"""

    granted: bool  # 是否批准
    original_request_id: str  # 对应的原始请求 ID
    reason: str = ""  # 批准/拒绝理由


# ===== 任务通知 =====


@dataclass
class TaskClaimedNotification:
    """任务认领通知"""

    task_id: str
    agent_id: str  # 认领者
    claimed_at: float = field(default_factory=time.time)


@dataclass
class TaskCompletedNotification:
    """任务完成通知"""

    task_id: str
    agent_id: str  # 完成者
    status: str  # completed / failed
    result_summary: str = ""  # 结果摘要


@dataclass
class IdleNotification:
    """空闲通知（Worker → Leader）"""

    agent_id: str
    idle_since: float  # 空闲开始时间
    available_for_tasks: bool = True  # 是否可接受新任务


# ===== 工厂函数 =====


def create_shutdown_request(
    from_agent: str,
    to_agent: str,
    reason: str = "",
    graceful: bool = True,
) -> CoordinationMessage:
    """创建关机请求消息"""
    return CoordinationMessage(
        message_type=MessageType.SHUTDOWN_REQUEST,
        from_agent=from_agent,
        to_agent=to_agent,
        payload={
            **ShutdownRequestPayload(
                reason=reason or "Leader requested shutdown",
                graceful=graceful,
            ).__dict__,
        },
    )


def create_shutdown_response(
    original_request: CoordinationMessage,
    accepted: bool,
    message: str = "",
) -> CoordinationMessage:
    """创建关机响应消息"""
    return CoordinationMessage(
        message_type=MessageType.SHUTDOWN_RESPONSE,
        from_agent=original_request.to_agent,
        to_agent=original_request.from_agent,
        payload={
            **ShutdownResponsePayload(
                accepted=accepted,
                original_request_id=original_request.message_id,
                message=message or ("Shutdown acknowledged" if accepted else "Shutdown rejected"),
            ).__dict__,
        },
        reply_to=original_request.message_id,
    )


def create_permission_request(
    from_agent: str,
    tool_name: str,
    tool_input: dict[str, Any],
    reason: str = "",
) -> CoordinationMessage:
    """创建权限请求消息"""
    return CoordinationMessage(
        message_type=MessageType.PERMISSION_REQUEST,
        from_agent=from_agent,
        to_agent="coordinator",  # 权限请求发送给 coordinator
        payload={
            **PermissionRequestPayload(
                tool_name=tool_name,
                tool_input=tool_input,
                reason=reason,
            ).__dict__,
        },
    )


def create_permission_response(
    original_request: CoordinationMessage,
    granted: bool,
    reason: str = "",
) -> CoordinationMessage:
    """创建权限响应消息"""
    return CoordinationMessage(
        message_type=MessageType.PERMISSION_RESPONSE,
        from_agent=original_request.to_agent,
        to_agent=original_request.from_agent,
        payload={
            **PermissionResponsePayload(
                granted=granted,
                original_request_id=original_request.message_id,
                reason=reason,
            ).__dict__,
        },
        reply_to=original_request.message_id,
    )
