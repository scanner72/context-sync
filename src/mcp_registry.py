"""Centralized MCP Server Registry and Fleet Injector.

Allows AI agents to discover, share, and replicate validated MCP server
configurations (stdio / sse) across all agents and IDEs on a machine.
"""

import os
import sys
import uuid
import json
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_

from src.models import FleetMCPServer
from src.database import get_db_session
from src.scanner import get_candidate_targets, AgentTarget

logger = logging.getLogger(__name__)


def inject_server_into_json_config(config_path: Path, server_name: str, server_dict: Dict[str, Any]) -> bool:
    """Safely inject an MCP server into an agent's json configuration file."""
    try:
        data: Dict[str, Any] = {}
        if config_path.exists():
            # Create backup if not already present
            bak = config_path.with_suffix(config_path.suffix + ".bak")
            if not bak.exists():
                shutil.copy2(config_path, bak)

            content = config_path.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                try:
                    data = json.loads(content)
                except Exception:
                    data = {}

        # Locate or create the mcpServers map
        if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
            data["mcpServers"] = {}

        data["mcpServers"][server_name] = server_dict

        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as exc:
        logger.error(f"Failed to inject MCP server into {config_path}: {exc}")
        return False


class MCPRegistry:
    """Central registry and fleet installer for external MCP servers."""

    async def register_server(
        self,
        name: str,
        transport: str,
        config: Dict[str, Any],
        source_agent: str = "unknown",
    ) -> Dict[str, Any]:
        """Save or update an MCP server configuration in the registry."""
        name = name.strip().lower()
        transport = transport.strip().lower()
        if transport not in ("stdio", "sse"):
            raise ValueError("Transport must be either 'stdio' or 'sse'")

        async with get_db_session() as session:
            stmt = select(FleetMCPServer).where(FleetMCPServer.name == name)
            result = await session.execute(stmt)
            existing: Optional[FleetMCPServer] = result.scalars().first()

            if existing:
                existing.transport = transport
                existing.config = config
                existing.source_agent = source_agent
                existing.is_active = True
                existing.updated_at = datetime.now(timezone.utc)
                server = existing
                action = "updated"
            else:
                server = FleetMCPServer(
                    id=uuid.uuid4(),
                    name=name,
                    transport=transport,
                    config=config,
                    source_agent=source_agent,
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(server)
                action = "registered"

            await session.flush()
            data = server.to_dict()
            data["action"] = action
            return data

    async def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve MCP server specification by name."""
        name = name.strip().lower()
        async with get_db_session() as session:
            stmt = select(FleetMCPServer).where(FleetMCPServer.name == name)
            result = await session.execute(stmt)
            server = result.scalars().first()
            return server.to_dict() if server else None

    async def list_servers(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """List all servers in the registry."""
        async with get_db_session() as session:
            stmt = select(FleetMCPServer)
            if only_active:
                stmt = stmt.where(FleetMCPServer.is_active == True)  # noqa: E712
            stmt = stmt.order_by(FleetMCPServer.name.asc())
            result = await session.execute(stmt)
            servers = result.scalars().all()
            return [s.to_dict() for s in servers]

    async def install_server(
        self,
        server_name: str,
        target_agent_app_id: str,
        custom_config_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Inject an MCP server into an agent's configuration file."""
        server = await self.get_server(server_name)
        if not server:
            raise ValueError(f"MCP server '{server_name}' not found in registry")

        # Prepare agent-compliant config payload
        transport = server["transport"]
        raw_cfg = server["config"]

        if transport == "sse":
            server_payload = {
                "url": raw_cfg.get("url"),
                "headers": raw_cfg.get("headers", {}),
            }
        else:
            server_payload = {
                "command": raw_cfg.get("command"),
                "args": raw_cfg.get("args", []),
                "env": raw_cfg.get("env", {}),
            }

        if custom_config_path:
            target_path = custom_config_path
        else:
            candidates = get_candidate_targets()
            match = next((c for c in candidates if c.app_id == target_agent_app_id), None)
            if not match:
                raise ValueError(f"Unknown agent app_id: '{target_agent_app_id}'")
            target_path = match.config_path

        success = inject_server_into_json_config(target_path, server["name"], server_payload)
        return {
            "server": server["name"],
            "target_agent": target_agent_app_id,
            "config_path": str(target_path),
            "status": "installed" if success else "failed",
        }

    async def install_to_all_detected(self, server_name: str) -> Dict[str, Any]:
        """Deploy MCP server into all detected agents on current machine."""
        server = await self.get_server(server_name)
        if not server:
            raise ValueError(f"MCP server '{server_name}' not found in registry")

        from src.scanner import scan_agents
        detected_agents = scan_agents()
        results = {}

        for agent in detected_agents:
            if agent.detected:
                res = await self.install_server(server_name, agent.app_id)
                results[agent.app_id] = res

        return {
            "server": server_name,
            "installed_count": len(results),
            "results": results,
        }


# Global singleton instance
mcp_registry = MCPRegistry()
