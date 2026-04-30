"""Skill Model — 知识库技能 (Markdown .md files)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Skill(Base):
    """已安装技能实体 — 对应 OpenHarness Skills 子系统."""

    __tablename__ = 'skills'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(32), default='general')
    version: Mapped[Optional[str]] = mapped_column(String(16), default='1.0.0')

    source: Mapped[str] = mapped_column(
        String(16), default='builtin'
    )  # builtin, file, url, registry
    path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    content_md: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    triggers: Mapped[List[str]] = mapped_column('triggers', JSON, default=list)
    dependencies: Mapped[List[str]] = mapped_column('dependencies', JSON, default=list)

    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[Dict[str, Any]] = mapped_column('metadata', JSON, default=dict)

    installed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'version': self.version,
            'source': self.source,
            'path': self.path,
            'url': self.url,
            'enabled': self.enabled,
            'content_md': self.content_md,
            'triggers': self.triggers or [],
            'dependencies': self.dependencies or [],
            'usage_count': self.usage_count,
            'metadata': self.metadata_ or {},
            'installed_by': self.installed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
