"""Fact-Level Conflict Resolution (FLCR) Engine for ContextSync.

Manages atomic project facts (triplets: entity, attribute, value) with
versioning, source attribution, and conflict resolution strategies.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ProjectFact
from src.database import get_db_session

logger = logging.getLogger(__name__)

# Authority levels for agents (higher number = higher priority)
AUTHORITY_WEIGHTS: Dict[str, int] = {
    "user": 100,
    "human": 100,
    "architect": 80,
    "lead": 80,
    "antigravity": 50,
    "claude": 50,
    "codex": 50,
    "cursor": 50,
    "unknown": 10,
}


def get_authority_weight(agent: str) -> int:
    """Return authority level for a given agent name."""
    normalized = agent.lower().strip()
    return AUTHORITY_WEIGHTS.get(normalized, 30)


class FactStore:
    """Store and resolution manager for atomic project facts."""

    async def set_fact(
        self,
        entity: str,
        attribute: str,
        value: Any,
        project: str = "global",
        source_agent: str = "unknown",
        confidence: float = 1.0,
        policy: str = "lww",  # "lww" (Last-Write-Wins) or "authority"
    ) -> Dict[str, Any]:
        """Record or update a fact with conflict detection and version history.
        
        Returns the created or updated fact dict along with resolution status.
        """
        entity = entity.strip().lower()
        attribute = attribute.strip().lower()

        async with get_db_session() as session:
            # Look for existing active fact for this (project, entity, attribute)
            stmt = select(ProjectFact).where(
                and_(
                    ProjectFact.project == project,
                    ProjectFact.entity == entity,
                    ProjectFact.attribute == attribute,
                    ProjectFact.is_active == True,  # noqa: E712
                )
            ).order_by(ProjectFact.created_at.desc())

            result = await session.execute(stmt)
            existing: Optional[ProjectFact] = result.scalars().first()

            if existing is None:
                # First time this fact is recorded
                new_fact = ProjectFact(
                    id=uuid.uuid4(),
                    project=project,
                    entity=entity,
                    attribute=attribute,
                    value=value,
                    source_agent=source_agent,
                    confidence=confidence,
                    version=1,
                    is_active=True,
                    conflict_flag=False,
                    conflict_details=None,
                )
                session.add(new_fact)
                await session.flush()
                data = new_fact.to_dict()
                data["action"] = "created"
                data["conflict_detected"] = False
                return data

            # If the value is identical, simply refresh timestamp or confidence
            if existing.value == value:
                existing.confidence = max(float(existing.confidence or 0), confidence)
                existing.source_agent = source_agent
                existing.updated_at = datetime.now(timezone.utc)
                await session.flush()
                data = existing.to_dict()
                data["action"] = "unchanged"
                data["conflict_detected"] = False
                return data

            # Values DIFFER: Conflict or Update
            conflict_detected = False
            new_version = int(existing.version or 1) + 1
            new_id = uuid.uuid4()

            if policy == "authority":
                new_weight = get_authority_weight(source_agent)
                existing_weight = get_authority_weight(existing.source_agent)

                if new_weight < existing_weight:
                    # Incoming fact has LOWER authority -> Reject overwrite, flag conflict
                    conflict_detected = True
                    existing.conflict_flag = True
                    existing.conflict_details = {
                        "rejected_value": value,
                        "rejected_agent": source_agent,
                        "rejected_at": datetime.now(timezone.utc).isoformat(),
                        "reason": f"Lower authority ({new_weight} vs {existing_weight})",
                    }
                    await session.flush()
                    data = existing.to_dict()
                    data["action"] = "rejected_due_to_authority"
                    data["conflict_detected"] = True
                    return data

            # LWW or incoming authority is >= existing authority:
            # Supersede the existing fact
            existing.is_active = False
            existing.superseded_by = new_id

            new_fact = ProjectFact(
                id=new_id,
                project=project,
                entity=entity,
                attribute=attribute,
                value=value,
                source_agent=source_agent,
                confidence=confidence,
                version=new_version,
                is_active=True,
                conflict_flag=conflict_detected,
                conflict_details=None,
            )
            session.add(new_fact)
            await session.flush()

            data = new_fact.to_dict()
            data["action"] = "superseded_previous"
            data["conflict_detected"] = conflict_detected
            data["previous_version"] = int(existing.version)
            data["previous_value"] = existing.value
            return data

    async def get_fact(
        self,
        entity: str,
        attribute: str,
        project: str = "global",
    ) -> Optional[Dict[str, Any]]:
        """Retrieve the currently active fact for an entity and attribute."""
        entity = entity.strip().lower()
        attribute = attribute.strip().lower()

        async with get_db_session() as session:
            stmt = select(ProjectFact).where(
                and_(
                    ProjectFact.project == project,
                    ProjectFact.entity == entity,
                    ProjectFact.attribute == attribute,
                    ProjectFact.is_active == True,  # noqa: E712
                )
            ).order_by(ProjectFact.created_at.desc())

            result = await session.execute(stmt)
            fact: Optional[ProjectFact] = result.scalars().first()
            return fact.to_dict() if fact else None

    async def list_facts(
        self,
        project: str = "global",
        entity: Optional[str] = None,
        only_active: bool = True,
    ) -> List[Dict[str, Any]]:
        """List facts for a project, optionally filtered by entity."""
        async with get_db_session() as session:
            conditions = [ProjectFact.project == project]
            if entity:
                conditions.append(ProjectFact.entity == entity.strip().lower())
            if only_active:
                conditions.append(ProjectFact.is_active == True)  # noqa: E712

            stmt = select(ProjectFact).where(and_(*conditions)).order_by(
                ProjectFact.entity.asc(),
                ProjectFact.attribute.asc(),
                ProjectFact.created_at.desc(),
            )
            result = await session.execute(stmt)
            facts = result.scalars().all()
            return [f.to_dict() for f in facts]

    async def get_fact_history(
        self,
        entity: str,
        attribute: str,
        project: str = "global",
    ) -> List[Dict[str, Any]]:
        """Retrieve the complete audit / version trail of a fact."""
        entity = entity.strip().lower()
        attribute = attribute.strip().lower()

        async with get_db_session() as session:
            stmt = select(ProjectFact).where(
                and_(
                    ProjectFact.project == project,
                    ProjectFact.entity == entity,
                    ProjectFact.attribute == attribute,
                )
            ).order_by(ProjectFact.version.asc())

            result = await session.execute(stmt)
            facts = result.scalars().all()
            return [f.to_dict() for f in facts]

    async def resolve_conflict(
        self,
        fact_id: str,
        chosen_value: Any,
        resolver_agent: str = "user",
    ) -> Optional[Dict[str, Any]]:
        """Explicitly resolve a contested fact by setting the definitive chosen value."""
        target_uuid = uuid.UUID(fact_id) if isinstance(fact_id, str) else fact_id

        async with get_db_session() as session:
            stmt = select(ProjectFact).where(ProjectFact.id == target_uuid)
            result = await session.execute(stmt)
            fact: Optional[ProjectFact] = result.scalars().first()
            if not fact:
                return None

            # Mark current as resolved
            fact.conflict_flag = False
            fact.conflict_details = {
                "resolved_by": resolver_agent,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }
            fact.value = chosen_value
            fact.source_agent = resolver_agent
            fact.confidence = 1.0
            fact.updated_at = datetime.now(timezone.utc)
            await session.flush()
            return fact.to_dict()

    async def render_facts_digest(self, project: str = "global") -> str:
        """Render a concise markdown truth-table of active facts for injection into rules files."""
        facts = await self.list_facts(project=project, only_active=True)
        if not facts:
            return ""

        lines = [
            "### 📌 Утвержденные факты проекта (Truth-Table):",
            "| Сущность (Entity) | Параметр (Attribute) | Значение (Value) | Агент | Версия |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for f in facts:
            val_str = str(f["value"])
            if isinstance(f["value"], (dict, list)):
                import json
                val_str = json.dumps(f["value"], ensure_ascii=False)
            # Truncate if extremely long
            if len(val_str) > 60:
                val_str = val_str[:57] + "..."
            
            conflict_note = " ⚠️ [Конфликт]" if f.get("conflict_flag") else ""
            lines.append(
                f"| `{f['entity']}` | `{f['attribute']}` | `{val_str}`{conflict_note} | {f['source_agent']} | v{f['version']} |"
            )

        return "\n".join(lines)


# Global singleton instance
fact_store = FactStore()
