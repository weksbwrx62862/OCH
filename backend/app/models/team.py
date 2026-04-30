"""Team & TeamMember models for multi-agent coordination."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent import Agent


class Team(Base):
    """多智能体团队实体."""

    __tablename__ = 'teams'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default='active')  # active, paused, dissolved

    config: Mapped[Dict[str, Any]] = mapped_column('config', JSON, default=dict)
    metadata_: Mapped[Dict[str, Any]] = mapped_column('metadata', JSON, default=dict)

    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dissolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    members: Mapped[List['TeamMember']] = relationship(
        'TeamMember', back_populates='team',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'member_count': len(self.members) if self.members else 0,
            'config': self.config or {},
            'metadata': self.metadata_ or {},
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TeamMember(Base):
    """团队成员 — 关联 Agent 和角色."""

    __tablename__ = 'team_members'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    team_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('teams.id', ondelete='CASCADE'), nullable=False
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey('agents.id', ondelete='SET NULL'), nullable=True
    )

    role: Mapped[str] = mapped_column(String(32), default='member')  # leader, reviewer, worker
    capabilities: Mapped[List[str]] = mapped_column('capabilities', JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default='idle')  # idle, busy, offline

    assigned_task_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    task_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)

    joined_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    team: Mapped['Team'] = relationship('Team', back_populates='members')
    agent: Mapped[Optional['Agent']] = relationship('Agent')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'team_id': self.team_id,
            'agent_id': self.agent_id,
            'role': self.role,
            'capabilities': self.capabilities or [],
            'status': self.status,
            'assigned_task_id': self.assigned_task_id,
            'task_count': self.task_count,
            'completed_tasks': self.completed_tasks,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
        }
