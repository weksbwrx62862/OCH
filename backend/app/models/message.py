"""Message and ToolResult models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class Message(Base):
    """消息实体 — 对应 OpenHarness ConversationMessage."""

    __tablename__ = 'messages'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey('sessions.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Assistant 特有字段
    tool_uses: Mapped[Optional[List[Dict]]] = mapped_column(JSON, default=list)
    stop_reason: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Token 统计
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)

    # 关系
    session: Mapped['Session'] = relationship('Session', back_populates='messages')
    tool_results: Mapped[List['ToolResult']] = relationship(
        'ToolResult', back_populates='message',
        cascade='all, delete-orphan',
        lazy='selectin'
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'tool_uses': self.tool_uses or [],
            'stop_reason': self.stop_reason,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ToolResult(Base):
    """工具执行结果."""

    __tablename__ = 'tool_results'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey('messages.id'), nullable=False)

    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_input: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    tool_output: Mapped[str] = mapped_column(Text, default='')
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    permission_decision: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    message: Mapped['Message'] = relationship('Message', back_populates='tool_results')

    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'message_id': self.message_id,
            'tool_name': self.tool_name,
            'tool_input': self.tool_input,
            'tool_output': self.tool_output[:10000],  # 截断过长输出
            'is_error': self.is_error,
            'duration_ms': self.duration_ms,
            'permission_decision': self.permission_decision,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
