"""Agent model — represents an AI agent configuration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.permission import ToolPermission


class Agent(Base):
    """Agent 实体 — 对应 OpenHarness 的 Agent 配置."""

    __tablename__ = 'agents'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default='')
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, default=None)
    model: Mapped[str] = mapped_column(String(64), default='claude-sonnet-4-20250514')
    max_turns: Mapped[int] = mapped_column(Integer, default=8)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    workspace: Mapped[str] = mapped_column(String(512), default='./workspace')
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # 关系
    sessions: Mapped[List['Session']] = relationship(
        'Session', back_populates='agent', lazy='selectin', cascade='all, delete-orphan'
    )
    permissions: Mapped[List['ToolPermission']] = relationship(
        'ToolPermission', back_populates='agent', cascade='all, delete-orphan'
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'model': self.model,
            'max_turns': self.max_turns,
            'max_tokens': self.max_tokens,
            'workspace': self.workspace,
            'config': self.config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ToolPermission(Base):
    """工具级权限配置 — 每个 Agent 可以单独配置每个工具的权限."""

    __tablename__ = 'tool_permissions'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey('agents.id'), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    permission: Mapped[str] = mapped_column(String(16), default='ask')  # allow, deny, ask
    path_rules: Mapped[Optional[List[Dict]]] = mapped_column(JSON, nullable=True)
    approved_commands: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    denied_commands: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    agent: Mapped['Agent'] = relationship('Agent', back_populates='permissions')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'tool_name': self.tool_name,
            'permission': self.permission,
            'path_rules': self.path_rules or [],
            'approved_commands': self.approved_commands or [],
            'denied_commands': self.denied_commands or [],
        }
