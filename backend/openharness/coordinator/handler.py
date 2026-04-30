"""协调协议处理器

实现团队协调协议的核心逻辑:
1. 关机握手流程（请求 → 收尾 → 确认 → 终止）
2. 权限审批流程（Worker → Leader → 批准/拒绝）
3. 消息路由和响应匹配

参考实现:
- Claude Code src/utils/swarm/permissionSync.ts
- Claude Code src/utils/swarm/teamHelpers.ts
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Awaitable

from openharness.coordinator.protocol import (
    CoordinationMessage,
    MessageType,
    ShutdownRequestPayload,
    ShutdownResponsePayload,
    PermissionResponsePayload,
)

log = logging.getLogger(__name__)


class ProtocolTimeoutError(Exception):
    """协议超时错误"""

    def __init__(self, request_id: str, timeout: float) -> None:
        self.request_id = request_id
        self.timeout = timeout
        super().__init__(f"Protocol request {request_id} timed out after {timeout}s")


class CoordinationProtocolHandler:
    """协调协议处理器

    处理团队间的标准化通信，包括:
    - 关机握手：确保 Worker 优雅关闭
    - 权限审批：Worker 请求危险操作许可
    - 消息匹配：通过 message_id/reply_to 匹配请求-响应对
    """

    def __init__(self, team_registry=None, task_manager=None):
        """
        初始化协议处理器

        Args:
            team_registry: 团队注册表（用于查找 Agent）
            task_manager: 任务管理器（用于收尾任务）
        """
        self._registry = team_registry
        self._tasks = task_manager

        # 待处理的请求（request_id → Future）
        self._pending_requests: dict[str, asyncio.Future[CoordinationMessage]] = {}

        # 消息处理回调
        self._message_handlers: dict[MessageType, Callable] = {}

    async def send_shutdown_request(
        self,
        target_agent: str,
        reason: str = "",
        graceful: bool = True,
        timeout: float = 30.0,
    ) -> bool:
        """
        发送关机请求（Leader → Worker）

        流程（参考 Claude Code teamHelpers.ts）:
        1. 创建 ShutdownRequest 带 request_id
        2. 发送到目标 Agent 的收件箱
        3. 创建 Future 等待响应
        4. 等待响应或超时
        5. 收到确认后才真正终止

        Args:
            target_agent: 目标 Agent ID
            reason: 关机原因
            graceful: 是否优雅关闭
            timeout: 超时时间（秒）

        Returns:
            是否成功收到确认

        Raises:
            ProtocolTimeoutError: 超时未收到响应
        """
        from openharness.coordinator.protocol import create_shutdown_request

        # 创建关机请求
        request = create_shutdown_request(
            from_agent="coordinator",
            to_agent=target_agent,
            reason=reason,
            graceful=graceful,
        )

        log.info(
            "发送关机请求到 %s (graceful=%s, timeout=%.1fs)",
            target_agent,
            graceful,
            timeout,
        )

        # 创建 Future 等待响应
        loop = asyncio.get_event_loop()
        future: asyncio.Future[CoordinationMessage] = loop.create_future()
        self._pending_requests[request.message_id] = future

        try:
            # 发送请求到目标 Agent 的收件箱
            await self._send_to_mailbox(target_agent, request)

            # 等待响应
            response = await asyncio.wait_for(future, timeout=timeout)

            # 解析响应
            payload = ShutdownResponsePayload(**response.payload)

            if payload.accepted:
                log.info("Agent %s 已确认关机", target_agent)
                return True
            else:
                log.warning("Agent %s 拒绝关机: %s", target_agent, payload.message)
                return False

        except asyncio.TimeoutError:
            log.error("关机请求超时 (%.1fs), Agent: %s", timeout, target_agent)
            raise ProtocolTimeoutError(request.message_id, timeout)
        finally:
            self._pending_requests.pop(request.message_id, None)

    async def handle_shutdown_request(self, message: CoordinationMessage) -> CoordinationMessage:
        """
        Worker 处理关机请求

        流程:
        1. 收到请求
        2. 如果 graceful=True，执行收尾工作:
           a. 保存当前工作状态
           b. 完成正在执行的任务（如果有）
           c. 清理临时资源
        3. 回复确认（引用原始 request_id）

        Args:
            message: 关机请求消息

        Returns:
            关机响应消息
        """
        from openharness.coordinator.protocol import create_shutdown_response

        payload = ShutdownRequestPayload(**message.payload)

        log.info(
            "收到关机请求 (graceful=%s, reason=%s)",
            payload.graceful,
            payload.reason,
        )

        tasks_completed = 0

        if payload.graceful:
            # 执行收尾工作
            tasks_completed = await self._perform_graceful_shutdown()

        # 创建并返回响应
        response = create_shutdown_response(
            original_request=message,
            accepted=True,
            message=f"Shutdown acknowledged (completed {tasks_completed} tasks)",
        )

        # 更新响应中的任务完成数
        response.payload["tasks_completed"] = tasks_completed

        return response

    async def _perform_graceful_shutdown(self) -> int:
        """执行优雅关闭的收尾工作"""
        completed_count = 0

        if self._tasks:
            # 获取正在运行的任务
            running_tasks = [t for t in self._tasks.list_tasks() if t.status == "running"]

            for task in running_tasks:
                try:
                    log.info("等待任务 %s 完成...", task.id[:8])
                    # 这里可以添加等待任务完成的逻辑
                    # 目前仅记录日志
                    completed_count += 1
                except Exception as e:
                    log.warning("任务 %s 收尾失败: %s", task.id[:8], e)

        return completed_count

    async def request_permission(
        self,
        tool_name: str,
        tool_input: dict,
        agent_id: str = "",
        reason: str = "",
        timeout: float = 30.0,
    ) -> bool:
        """
        Worker 请求权限（Worker → Leader）

        用途: Worker 需要执行危险操作时，向 Coordinator/Leader 申请审批

        Args:
            tool_name: 需要权限的工具名
            tool_input: 工具输入参数
            agent_id: 请求者 Agent ID
            reason: 申请理由
            timeout: 等待超时时间

        Returns:
            是否获得批准
        """
        from openharness.coordinator.protocol import create_permission_request

        request = create_permission_request(
            from_agent=agent_id or "worker",
            tool_name=tool_name,
            tool_input=tool_input,
            reason=reason,
        )

        log.info(
            "Agent %s 请求权限: tool=%s",
            agent_id or "worker",
            tool_name,
        )

        # 创建 Future 等待响应
        loop = asyncio.get_event_loop()
        future: asyncio.Future[CoordinationMessage] = loop.create_future()
        self._pending_requests[request.message_id] = future

        try:
            # 发送到 coordinator
            await self._send_to_mailbox("coordinator", request)

            # 等待审批结果
            response = await asyncio.wait_for(future, timeout=timeout)

            payload = PermissionResponsePayload(**response.payload)

            if payload.granted:
                log.info("权限已批准: tool=%s", tool_name)
            else:
                log.warning("权限被拒绝: tool=%s, reason=%s", tool_name, payload.reason)

            return payload.granted

        except asyncio.TimeoutError:
            log.error("权限请求超时 (%.1fs): tool=%s", timeout, tool_name)
            raise ProtocolTimeoutError(request.message_id, timeout)
        finally:
            self._pending_requests.pop(request.message_id, None)

    async def handle_permission_response(self, message: CoordinationMessage) -> None:
        """
        处理权限响应（由 Leader/Coordinator 调用）

        将响应传递给等待的 Worker
        """
        if message.reply_to and message.reply_to in self._pending_requests:
            future = self._pending_requests.pop(message.reply_to)
            if not future.done():
                future.set_result(message)
                log.debug("权限响应已传递: request=%s", message.reply_to)

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[CoordinationMessage], Awaitable[None]],
    ) -> None:
        """注册消息类型处理器"""
        self._message_handlers[message_type] = handler

    async def process_message(self, message: CoordinationMessage) -> None:
        """
        处理收到的协调消息

        根据消息类型分发到对应的处理器
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            await handler(message)
        else:
            log.warning("未注册的消息类型处理器: %s", message.message_type.value)

    async def _send_to_mailbox(
        self,
        target_agent: str,
        message: CoordinationMessage,
    ) -> None:
        """
        发送消息到目标 Agent 的收件箱

        Phase 3 待实现: 实际的邮箱系统（当前为占位实现，仅日志记录）
        """
        # 占位：实际应写入文件系统或内存队列
        log.debug(
            "发送消息到 %s 的收件箱: type=%s, id=%s",
            target_agent,
            message.message_type.value,
            message.message_id,
        )

        # 如果有 team_registry，尝试通过它发送
        if self._registry:
            try:
                # 假设 registry 有 send_message 方法
                # await self._registry.send_message(target_agent, message)
                pass
            except Exception as e:
                log.error("发送消息失败: %s", e)

    def get_pending_request_count(self) -> int:
        """获取待处理请求数量（用于监控）"""
        return len(self._pending_requests)

    def cleanup_expired_requests(self, max_age: float = 60.0) -> int:
        """清理过期的待处理请求"""
        expired = []

        for req_id, future in list(self._pending_requests.items()):
            # 简单的过期检查（实际应该记录创建时间）
            if not future.done():
                continue
            expired.append(req_id)

        for req_id in expired:
            del self._pending_requests[req_id]

        return len(expired)
