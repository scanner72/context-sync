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
    Boolean,
    Integer,
    Float,
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


class ProjectFact(Base):
    """Atomic project fact with versioning and conflict tracking."""
    __tablename__ = "project_facts"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project = Column(String(128), nullable=False, default="global", index=True)
    entity = Column(String(128), nullable=False, index=True)
    attribute = Column(String(128), nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    source_agent = Column(String(128), nullable=False, default="unknown")
    confidence = Column(Float, nullable=False, default=1.0)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    superseded_by = Column(PG_UUID(as_uuid=True), nullable=True)
    conflict_flag = Column(Boolean, nullable=False, default=False)
    conflict_details = Column(JSONB, nullable=True)


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "project": self.project,
            "entity": self.entity,
            "attribute": self.attribute,
            "value": self.value,
            "source_agent": self.source_agent,
            "confidence": float(self.confidence) if self.confidence is not None else 1.0,
            "version": int(self.version) if self.version is not None else 1,
            "is_active": bool(self.is_active),
            "superseded_by": str(self.superseded_by) if self.superseded_by else None,
            "conflict_flag": bool(self.conflict_flag),
            "conflict_details": self.conflict_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

