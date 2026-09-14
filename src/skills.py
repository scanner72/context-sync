"""Cross-Agent Skills Management & Replication Engine.

Enables AI coding agents (Antigravity, Cursor, Claude Code, Codex, Windsurf)
to publish, discover, and synchronize skills (SKILL.md and bundled assets)
across environments and devices.
"""

import os
import sys
import uuid
import yaml
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_

from src.models import FleetSkill
from src.database import get_db_session

logger = logging.getLogger(__name__)


def get_agent_skills_dir(agent_app_id: str, custom_base: Optional[Path] = None) -> Optional[Path]:
    """Resolve the appropriate skills directory for a given agent on current OS."""
    home = custom_base or Path.home()
    is_win = sys.platform.startswith("win")
    app_data = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) if is_win else home

    agent = agent_app_id.lower().strip()
    if agent in ("antigravity", "gemini"):
        return home / ".gemini" / "antigravity" / "skills"
    elif agent == "cursor":
        return home / ".cursor" / "skills"
    elif agent in ("claude", "claude-code"):
        return home / ".claude" / "skills"
    elif agent == "codex":
        return home / ".codex" / "skills"
    elif agent == "windsurf":
        return home / ".codeium" / "windsurf" / "skills"
    return None


class SkillsStore:
    """Repository and synchronizer for AI agent skills."""

    async def publish_skill(
        self,
        name: str,
        content_md: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        files_bundle: Optional[Dict[str, str]] = None,
        source_agent: str = "unknown",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publish or update a skill in the centralized fleet repository."""
        name = name.strip().lower()
        files_bundle = files_bundle or {}
        tags = tags or []

        # Try to parse frontmatter from markdown if description not given
        if not description and content_md.startswith("---"):
            try:
                parts = content_md.split("---", 2)
                if len(parts) >= 3:
                    parsed = yaml.safe_load(parts[1])
                    if isinstance(parsed, dict):
                        description = parsed.get("description", "")
            except Exception:
                pass

        description = description or f"Skill {name}"

        async with get_db_session() as session:
            stmt = select(FleetSkill).where(FleetSkill.name == name)
            result = await session.execute(stmt)
            existing: Optional[FleetSkill] = result.scalars().first()

            if existing:
                existing.version = version
                existing.description = description
                existing.content_md = content_md
                existing.files_bundle = files_bundle
                existing.source_agent = source_agent
                existing.tags = tags
                existing.updated_at = datetime.now(timezone.utc)
                skill = existing
                action = "updated"
            else:
                skill = FleetSkill(
                    id=uuid.uuid4(),
                    name=name,
                    version=version,
                    description=description,
                    content_md=content_md,
                    files_bundle=files_bundle,
                    source_agent=source_agent,
                    tags=tags,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(skill)
                action = "published"

            await session.flush()
            data = skill.to_dict()
            data["action"] = action
            return data

    async def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve full skill specification by unique name."""
        name = name.strip().lower()
        async with get_db_session() as session:
            stmt = select(FleetSkill).where(FleetSkill.name == name)
            result = await session.execute(stmt)
            skill = result.scalars().first()
            return skill.to_dict() if skill else None

    async def list_skills(
        self,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List skills in the catalog with optional filtering."""
        async with get_db_session() as session:
            conditions = []
            if tag:
                conditions.append(FleetSkill.tags.any(tag.strip().lower()))
            if search:
                term = f"%{search.strip().lower()}%"
                conditions.append(
                    or_(
                        FleetSkill.name.ilike(term),
                        FleetSkill.description.ilike(term),
                    )
                )

            stmt = select(FleetSkill)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(FleetSkill.name.asc()).limit(limit)

            result = await session.execute(stmt)
            skills = result.scalars().all()
            return [s.to_dict() for s in skills]

    async def install_skill(
        self,
        name: str,
        target_agent: str,
        custom_base: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Unpack and install a skill into a specific agent's local filesystem."""
        skill = await self.get_skill(name)
        if not skill:
            raise ValueError(f"Skill '{name}' not found in registry")

        target_dir = get_agent_skills_dir(target_agent, custom_base=custom_base)
        if not target_dir:
            raise ValueError(f"Unsupported or unknown target agent: '{target_agent}'")

        skill_folder = target_dir / skill["name"]
        skill_folder.mkdir(parents=True, exist_ok=True)

        # 1. Write SKILL.md
        skill_md_path = skill_folder / "SKILL.md"
        skill_md_path.write_text(skill["content_md"], encoding="utf-8")

        # 2. Write bundled files (scripts, templates, etc.)
        files_bundle = skill.get("files_bundle") or {}
        for rel_path, file_content in files_bundle.items():
            dest_file = skill_folder / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(file_content, encoding="utf-8")

        return {
            "status": "installed",
            "skill": skill["name"],
            "version": skill["version"],
            "target_agent": target_agent,
            "installed_path": str(skill_folder),
            "files_count": 1 + len(files_bundle),
        }

    async def install_to_all_agents(
        self,
        name: str,
        custom_base: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Deploy skill across all supported agents."""
        supported_agents = ["cursor", "claude", "antigravity", "codex", "windsurf"]
        results = {}
        for agent in supported_agents:
            try:
                res = await self.install_skill(name, agent, custom_base=custom_base)
                results[agent] = res
            except Exception as e:
                results[agent] = {"status": "skipped", "error": str(e)}

        return {
            "skill": name,
            "results": results,
        }


# Global singleton instance
skills_store = SkillsStore()
