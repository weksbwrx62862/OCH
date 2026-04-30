"""MCPServer model for MCP (Model Context Protocol) server management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MCPServer(Base):
    """MCP 服务器配置实体."""

    __tablename__ = 'mcp_servers'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    server_type: Mapped[str] = mapped_column(
        String(16), default='stdio'
    )  # stdio, streamable-http

    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    args: Mapped[List[str]] = mapped_column('args', JSON, default=list)
    env: Mapped[Dict[str, str]] = mapped_column('env', JSON, default=dict)

    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    headers: Mapped[Dict[str, str]] = mapped_column('headers', JSON, default=dict)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_start: Mapped[bool] = mapped_column(Boolean, default=False)

    # 运行时状态
    status: Mapped[str] = mapped_column(String(16), default='configured')  # configured, running, error
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_test_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 发现的工具和资源
    discovered_tools: Mapped[List[str]] = mapped_column('discovered_tools', JSON, default=list)
    discovered_resources: Mapped[List[str]] = mapped_column('discovered_resources', JSON, default=list)

    metadata_: Mapped[Dict[str, Any]] = mapped_column('metadata', JSON, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.server_type,
            'command': self.command,
            'args': self.args or [],
            'env': {k: ('***' if any(s in k.lower() for s in ('key', 'token', 'secret')) else v)
                      for k, v in (self.env or {}).items()},
            'url': self.url,
            'enabled': self.enabled,
            'auto_start': self.auto_start,
            'status': self.status,
            'last_error': self.last_error,
            'last_test_at': self.last_test_at.isoformat() if self.last_test_at else None,
            'latency_ms': self.latency_ms,
            'tools_count': len(self.discovered_tools) if self.discovered_tools else 0,
            'resources_count': len(self.discovered_resources) if self.discovered_resources else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
