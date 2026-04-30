"""Task and TaskDependency models for background job management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class Task(Base):
    """后台任务实体 — 对应 OpenHarness 后台任务系统."""

    __tablename__ = 'tasks'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey('sessions.id'), nullable=True
    )

    task_type: Mapped[str] = mapped_column(String(32), nullable=False)  # command, query, etc.
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default='pending')  # pending, running, completed, failed, stopped
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    output_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    cwd: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    metadata_: Mapped[Dict[str, Any]] = mapped_column('metadata', JSON, default=dict)

    # 关系
    session: Mapped[Optional['Session']] = relationship('Session', back_populates='tasks')
    dependencies: Mapped[List['TaskDependency']] = relationship(
        'TaskDependency', back_populates='task',
        cascade='all, delete-orphan',
        foreign_keys='TaskDependency.task_id'
    )
    dependents: Mapped[List['TaskDependency']] = relationship(
        'TaskDependency', back_populates='dependent',
        cascade='all, delete-orphan',
        foreign_keys='TaskDependency.dep_task_id'
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'task_type': self.task_type,
            'command': self.command,
            'status': self.status,
            'result': self.result[:5000] if self.result else None,
            'error': self.error,
            'exit_code': self.exit_code,
            'pid': self.pid,
            'output_path': self.output_path,
            'cwd': self.cwd,
            'metadata': self.metadata_ or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskDependency(Base):
    """任务依赖关系 — 支持 DAG (Directed Acyclic Graph)."""

    __tablename__ = 'task_dependencies'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tasks.id'), nullable=False
    )
    dep_task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tasks.id'), nullable=False
    )
    auto_unlock: Mapped[bool] = mapped_column(Boolean, default=True)

    task: Mapped['Task'] = relationship(
        'Task', back_populates='dependencies',
        foreign_keys=[task_id]
    )
    dependent: Mapped['Task'] = relationship(
        'Task', back_populates='dependents',
        foreign_keys=[dep_task_id]
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'task_id': self.task_id,
            'dep_task_id': self.dep_task_id,
            'auto_unlock': self.auto_unlock,
        }
