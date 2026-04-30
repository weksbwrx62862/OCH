"""Plugin model for managing extensions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Plugin(Base):
    """插件实体 — 管理已安装的插件."""

    __tablename__ = 'plugins'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String(32), default='0.0.0')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[str] = mapped_column(String(16), default='local')  # local, github, npm, marketplace
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    install_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    has_commands: Mapped[bool] = mapped_column(Boolean, default=False)
    has_hooks: Mapped[bool] = mapped_column(Boolean, default=False)
    has_agents: Mapped[bool] = mapped_column(Boolean, default=False)

    integrity_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    installed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'source': self.source,
            'source_url': self.source_url,
            'install_path': self.install_path,
            'enabled': self.enabled,
            'config': self.config,
            'has_commands': self.has_commands,
            'has_hooks': self.has_hooks,
            'has_agents': self.has_agents,
            'installed_by': self.installed_by,
            'installed_at': self.installed_at.isoformat() if self.installed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
