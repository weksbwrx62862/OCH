"""MemoryFact — 结构化记忆事实模型.

参考 DeerFlow MemoryUpdater 的 Facts 表设计:
- category: 事实类别 (preference/knowledge/context/behavior/goal/pattern/error)
- confidence: 置信度 (0-1)
- source: 来源 (extracted/manual/correction/reinforcement)
- tags: 标签列表
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, JSON,
    Column, Index,
)

from app.core.database import Base


class MemoryFact(Base):
    """结构化记忆事实 — AI 辅助开发中的用户偏好/项目知识/经验模式."""

    __tablename__ = "memory_facts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False, index=True)
    category = Column(
        String(32), nullable=False, default="knowledge",
        comment="preference/knowledge/context/behavior/goal/pattern/error"
    )
    confidence = Column(Float, default=0.8, comment="置信度 0-1")
    source = Column(
        String(32), default="manual",
        comment="extracted/manual/correction/reinforcement"
    )
    tags = Column(JSON, default=list, comment="标签列表")
    importance = Column(Integer, default=5, comment="重要性 1-10")
    session_id = Column(String(36), nullable=True, comment="关联会话")
    metadata_ = Column(JSON, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True, comment="过期时间（可选）")

    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('ix_memory_facts_category', 'category'),
        Index('ix_memory_facts_confidence', 'confidence'),
        Index('ix_memory_facts_source', 'source'),
        Index('ix_memory_facts_active', 'is_active'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'category': self.category,
            'confidence': self.confidence,
            'source': self.source,
            'tags': self.tags or [],
            'importance': self.importance,
            'session_id': self.session_id,
            'metadata': self.metadata_ or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
        }

    def __repr__(self) -> str:
        return f"<MemoryFact {self.id[:8]} [{self.category}] conf={self.confidence:.1f}>"
