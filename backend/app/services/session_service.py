"""Session Service — manages Agent conversation sessions."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update

from app.models.agent import Agent
from app.models.session import Session
from app.models.message import Message
from app.core.exceptions import NotFoundError, SessionError
from app.services.hook_service import trigger_hook

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务 — 对接 OpenHarness QueryEngine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        agent_id: str,
        title: str = '',
        metadata_: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """创建新会话."""
        # 验证 Agent 存在
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise NotFoundError('Agent', agent_id)

        session_obj = Session(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            status='active',
            title=title or f'New Chat - {datetime.now(timezone.utc).strftime("%H:%M")}',
            metadata_=metadata_ or {},
        )

        self.db.add(session_obj)
        await self.db.commit()
        await self.db.refresh(session_obj)

        logger.info(f"Created session {session_obj.id} for agent {agent_id}")
        return session_obj

    async def get_session(self, session_id: str) -> Session:
        """获取会话详情."""
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session_obj = result.scalar_one_or_none()
        if not session_obj:
            raise NotFoundError('Session', session_id)
        return session_obj

    async def list_sessions(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> tuple[List[Session], int]:
        """列出会话（分页）."""
        query = select(Session)

        if status:
            query = query.where(Session.status == status)
        if agent_id:
            query = query.where(Session.agent_id == agent_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Session.updated_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return list(sessions), total

    async def update_session(self, session_id: str, **kwargs) -> Session:
        """更新会话."""
        session_obj = await self.get_session(session_id)

        for key, value in kwargs.items():
            if hasattr(session_obj, key):
                setattr(session_obj, key, value)

        session_obj.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(session_obj)

        return session_obj

    async def delete_session(self, session_id: str) -> None:
        """删除会话."""
        session_obj = await self.get_session(session_id)
        await self.db.delete(session_obj)
        await self.db.commit()

    async def pause_session(self, session_id: str) -> Session:
        """暂停会话."""
        return await self.update_session(session_id, status='paused')

    async def resume_session(self, session_id: str) -> Session:
        """恢复会话."""
        return await self.update_session(session_id, status='active')

    async def complete_session(self, session_id: str) -> Session:
        """标记会话完成."""
        return await self.update_session(
            session_id,
            status='completed',
            completed_at=datetime.now(timezone.utc),
        )

    async def get_messages(
        self,
        session_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[List[Message], int]:
        """获取消息列表（分页）."""
        await self.get_session(session_id)  # 验证会话存在

        query = select(Message).where(Message.session_id == session_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Message.created_at.asc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages), total

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **kwargs,
    ) -> Message:
        """添加消息到会话."""
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            **kwargs,
        )

        self.db.add(message)

        # 更新会话统计
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(
                total_messages=Session.total_messages + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )

        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def stream_chat(
        self,
        session_id: str,
        user_message: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式聊天 — 连接到 OpenHarness QueryEngine.

        返回 SSE 兼容的事件字典流.
        """
        from openharness.engine import QueryEngine
        from openharness.config import OpenHarnessConfig

        session_obj = await self.get_session(session_id)
        agent = await self.db.get(Agent, session_obj.agent_id)

        if not agent:
            raise SessionError(f"Agent {session_obj.agent_id} not found", session_id)

        # 保存用户消息
        user_msg = await self.add_message(
            session_id=session_id,
            role='user',
            content=user_message,
        )

        yield {'type': 'message_saved', 'message_id': user_msg.id}

        try:
            # 初始化 QueryEngine（实际实现中需要配置）
            config = OpenHarnessConfig()
            QueryEngine(config=config)

            # P0-2: 触发 session_start Hook（首次聊天时）
            hook_result = await trigger_hook('session_start', {
                'session_id': session_id,
                'agent_id': agent.id,
                'user_message': user_message,
            })
            if hook_result['blocked']:
                yield {'type': 'error', 'error': f"Hook blocked: {hook_result['blocked_reason']}"}
                return

            # 流式执行（模拟）
            async for event in self._simulate_stream(user_message, options, session_id):
                yield event

            # TODO: 实际对接 OpenHarness QueryEngine.submit_message()
            # async for event in engine.submit_message(user_message):
            #     yield event.to_dict()

        except Exception as e:
            logger.exception(f"Stream error for session {session_id}")
            yield {'type': 'error', 'error': str(e)}

    async def _simulate_stream(
        self,
        message: str,
        options: Optional[Dict] = None,
        session_id: str = '',
    ) -> AsyncIterator[Dict]:
        """模拟流式输出（用于开发测试）.

        P0-2: 在工具调用前后触发 PRE/POST_TOOL_USE Hook
        """
        import asyncio

        # P0-2: 模拟工具调用前触发 pre_tool_use
        pre_hook = await trigger_hook('pre_tool_use', {
            'session_id': session_id,
            'tool_name': 'simulate',
            'tool_input': {'message': message[:100]},
            'user_message': message,
        })
        if pre_hook['blocked']:
            yield {
                'type': 'turn_complete',
                'stop_reason': 'hook_blocked',
                'usage': {'input_tokens': 0, 'output_tokens': 0},
                'hook_result': pre_hook,
            }
            return

        chunks = [
            f"正在处理: {message[:30]}...",
            "分析请求中...",
            "准备工具调用...",
        ]

        for chunk in chunks:
            yield {'type': 'text_delta', 'content': chunk}
            await asyncio.sleep(0.01)

        # P0-2: 模拟工具调用后触发 post_tool_use
        post_hook = await trigger_hook('post_tool_use', {
            'session_id': session_id,
            'tool_name': 'simulate',
            'tool_input': {'message': message[:100]},
            'output': 'simulation complete',
            'success': True,
        })

        yield {
            'type': 'turn_complete',
            'stop_reason': 'end_turn',
            'usage': {'input_tokens': 100, 'output_tokens': 50},
            'hooks_triggered': pre_hook['results_count'] + post_hook['results_count'],
        }

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计数据."""
        session_obj = await self.get_session(session_id)

        base_query = select(Message).where(Message.session_id == session_id)

        total_user_result = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(Message.role == 'user').subquery()
            )
        )
        total_user_messages = total_user_result.scalar() or 0

        total_assistant_result = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(Message.role == 'assistant').subquery()
            )
        )
        total_assistant_messages = total_assistant_result.scalar() or 0

        total_tool_calls_result = await self.db.execute(
            select(func.coalesce(func.sum(
                func.json_array_length(Message.tool_uses)
            ), 0)).where(Message.session_id == session_id)
        )
        total_tool_calls = total_tool_calls_result.scalar() or 0

        avg_tokens_result = await self.db.execute(
            select(
                func.avg(Message.tokens_input + Message.tokens_output)
            ).where(Message.session_id == session_id)
        )
        avg_tokens_per_message = avg_tokens_result.scalar() or 0

        stats = {
            **session_obj.to_dict(),
            'total_user_messages': total_user_messages,
            'total_assistant_messages': total_assistant_messages,
            'total_tool_calls': total_tool_calls,
            'avg_tokens_per_message': round(avg_tokens_per_message, 2) if avg_tokens_per_message else 0,
        }

        return stats
