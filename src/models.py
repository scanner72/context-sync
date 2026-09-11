"""SQLAlchemy models for context storage."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback placeholder for environments without pgvector installed
    Vector = None  # type: ignore

Base = declarative_base()


class ContextDocument(Base):
    __tablename__ = "contexts"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=False, default=list)
    project = Column(String(128), nullable=False, default="global", index=True)
    author_device = Column(String(128), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    
    # Vector column (384 dimensions by default for fastembed)
    if Vector is not None:
        embedding = Column(Vector(384), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self, include_embedding: bool = False) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "tags": list(self.tags or []),
            "project": self.project,
            "author_device": self.author_device,
            "metadata": dict(self.metadata_ or {}),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_embedding and self.embedding is not None:
            if hasattr(self.embedding, "tolist"):
                data["embedding"] = self.embedding.tolist()
            else:
                data["embedding"] = list(self.embedding)
        return data
