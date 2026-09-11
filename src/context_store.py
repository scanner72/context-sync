"""Context store operations: storage, semantic search, retrieval."""

import uuid
import math
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ContextDocument
from src.embeddings import embedding_service
from src.database import get_db_session

logger = logging.getLogger(__name__)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    n1 = math.sqrt(sum(a * a for a in vec1))
    n2 = math.sqrt(sum(b * b for b in vec2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


class ContextStore:
    """High-level repository for managing context items and vector search."""

    async def save(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        project: str = "global",
        author_device: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save or update a context document with vector embedding."""
        tags = tags or []
        metadata = metadata or {}
        
        # Vectorize title and content together for semantic richness
        embed_input = f"{title}\n\n{content}"
        embedding = await embedding_service.get_embedding(embed_input)

        async with get_db_session() as session:
            # Check for existing document with same title in same project
            stmt = select(ContextDocument).where(
                ContextDocument.title == title,
                ContextDocument.project == project,
            )
            result = await session.execute(stmt)
            existing: Optional[ContextDocument] = result.scalars().first()

            if existing:
                existing.content = content
                existing.tags = tags
                existing.author_device = author_device
                existing.metadata_ = metadata
                existing.embedding = embedding
                existing.updated_at = datetime.now(timezone.utc)
                doc = existing
                action = "updated"
            else:
                doc = ContextDocument(
                    id=uuid.uuid4(),
                    title=title,
                    content=content,
                    tags=tags,
                    project=project,
                    author_device=author_device,
                    metadata_=metadata,
                    embedding=embedding,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(doc)
                action = "created"

            await session.flush()
            data = doc.to_dict()
            data["action"] = action
            return data

    async def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by UUID or exact title."""
        async with get_db_session() as session:
            # Try UUID lookup
            try:
                doc_uuid = uuid.UUID(identifier)
                stmt = select(ContextDocument).where(ContextDocument.id == doc_uuid)
                result = await session.execute(stmt)
                doc = result.scalars().first()
                if doc:
                    return doc.to_dict()
            except ValueError:
                pass

            # Fallback: title lookup
            stmt = select(ContextDocument).where(ContextDocument.title == identifier)
            result = await session.execute(stmt)
            doc = result.scalars().first()
            if doc:
                return doc.to_dict()

            return None

    async def search(
        self,
        query: str,
        project: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
        min_score: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using pgvector or in-memory cosine fallback."""
        query_vector = await embedding_service.get_embedding(query)
        tags = tags or []

        tags = tags or []
        has_pgvector = hasattr(ContextDocument.embedding, "cosine_distance")

        async with get_db_session() as session:
            if has_pgvector:
                try:
                    distance = ContextDocument.embedding.cosine_distance(query_vector)
                    similarity = (1 - distance).label("similarity")

                    stmt = (
                        select(ContextDocument, similarity)
                        .where(ContextDocument.embedding.is_not(None))
                        .order_by(distance)
                        .limit(limit)
                    )

                    if project:
                        stmt = stmt.where(ContextDocument.project == project)

                    if tags and hasattr(ContextDocument.tags, "overlap"):
                        stmt = stmt.where(ContextDocument.tags.overlap(tags))

                    result = await session.execute(stmt)
                    matches = []
                    for doc, sim in result.all():
                        score = float(sim) if sim is not None else 0.0
                        if score >= min_score:
                            doc_dict = doc.to_dict()
                            doc_dict["score"] = round(score, 4)
                            matches.append(doc_dict)
                    return matches
                except Exception as e:
                    logger.warning(f"Native pgvector query failed ({e}), falling back to in-memory search")
                    await session.rollback()

            # In-memory cosine calculation fallback (for SQLite, test mocks, etc.)
            stmt = select(ContextDocument)
            if project:
                stmt = stmt.where(ContextDocument.project == project)
            
            result = await session.execute(stmt)
            all_docs = result.scalars().all()

            scored = []
            for doc in all_docs:
                if tags and not any(t in (doc.tags or []) for t in tags):
                    continue
                
                if doc.embedding is not None:
                    emb = doc.embedding.tolist() if hasattr(doc.embedding, "tolist") else list(doc.embedding)
                    sim = _cosine_similarity(query_vector, emb)
                else:
                    sim = 0.5 if query.lower() in doc.content.lower() or query.lower() in doc.title.lower() else 0.0

                if sim >= min_score:
                    doc_dict = doc.to_dict()
                    doc_dict["score"] = round(sim, 4)
                    scored.append(doc_dict)

            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]

    async def list_all(
        self,
        project: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List recently updated context entries."""
        async with get_db_session() as session:
            stmt = select(ContextDocument).order_by(ContextDocument.updated_at.desc())
            if project:
                stmt = stmt.where(ContextDocument.project == project)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            docs = result.scalars().all()
            return [d.to_dict() for d in docs]

    async def delete(self, identifier: str) -> bool:
        """Delete a context by UUID or exact title."""
        async with get_db_session() as session:
            try:
                doc_uuid = uuid.UUID(identifier)
                stmt = delete(ContextDocument).where(ContextDocument.id == doc_uuid)
            except ValueError:
                stmt = delete(ContextDocument).where(ContextDocument.title == identifier)

            result = await session.execute(stmt)
            return (result.rowcount or 0) > 0


context_store = ContextStore()
