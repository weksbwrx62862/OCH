"""Session model — represents a conversation session with QueryEngine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, Float, Integer, JSON, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.message import Message
    from app.models.task import Task


class Session(Base):
    """会话实体 — 对应 OpenHarness QueryEngine 实例."""

    __tablename__ = 'sessions'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('agents.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default='active')
    title: Mapped[str] = mapped_column(String(256), default='')

    # 统计信息
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_turns: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    metadata_: Mapped[Dict[str, Any]] = mapped_column('metadata', JSON, default=dict)

    # 关系
    agent: Mapped[Optional['Agent']] = relationship('Agent', back_populates='sessions')
    messages: Mapped[List['Message']] = relationship(
        'Message', back_populates='session',
        order_by='Message.created_at',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    tasks: Mapped[List['Task']] = relationship(
        'Task', back_populates='session',
        cascade='all, delete-orphan'
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'status': self.status,
            'title': self.title,
            'total_messages': self.total_messages,
            'total_turns': self.total_turns,
            'total_tokens_input': self.total_tokens_input,
            'total_tokens_output': self.total_tokens_output,
            'total_cost_usd': self.total_cost_usd,
            'metadata': self.metadata_ or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
