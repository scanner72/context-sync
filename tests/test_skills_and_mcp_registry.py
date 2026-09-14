"""Unit and integration tests for Skills Replication and MCP Fleet Hub."""

import json
import uuid
import pytest
from pathlib import Path

from src.skills import skills_store
from src.mcp_registry import mcp_registry, inject_server_into_json_config
from src.mcp_server import mcp_handler


@pytest.mark.asyncio
async def test_skill_publish_and_retrieval():
    skill_name = f"test-docker-expert-{uuid.uuid4().hex[:6]}"
    content = """---
name: docker-expert
description: Automated Docker deployment and container debugging.
---
# Docker Expert Instructions
Always check port collisions before running containers.
"""
    files = {
        "scripts/check_ports.py": "print('Checking ports...')",
        "templates/compose.override.yml": "version: '3.8'\nservices: {}",
    }

    # 1. Publish skill
    pub = await skills_store.publish_skill(
        name=skill_name,
        content_md=content,
        version="1.2.0",
        files_bundle=files,
        source_agent="Antigravity",
        tags=["docker", "devops"],
    )
    assert pub["action"] == "published"
    assert pub["name"] == skill_name
    assert pub["version"] == "1.2.0"
    assert pub["description"] == "Automated Docker deployment and container debugging."

    # 2. Retrieve skill
    fetched = await skills_store.get_skill(skill_name)
    assert fetched is not None
    assert fetched["name"] == skill_name
    assert "scripts/check_ports.py" in fetched["files_bundle"]

    # 3. List skills with search
    lst = await skills_store.list_skills(search=skill_name[:10])
    assert any(s["name"] == skill_name for s in lst)


@pytest.mark.asyncio
async def test_skill_installation_to_disk(tmp_path: Path):
    skill_name = f"test-git-skill-{uuid.uuid4().hex[:6]}"
    content = "# Git Sync Guidelines\nKeep commit messages clear."
    files = {"hooks/pre-commit.sh": "echo 'running hook'"}

    await skills_store.publish_skill(
        name=skill_name,
        content_md=content,
        files_bundle=files,
        source_agent="user",
    )

    # Install into mock target agent directory
    res = await skills_store.install_skill(
        name=skill_name,
        target_agent="cursor",
        custom_base=tmp_path,
    )
    assert res["status"] == "installed"
    assert res["files_count"] == 2

    installed_dir = Path(res["installed_path"])
    assert (installed_dir / "SKILL.md").exists()
    assert (installed_dir / "SKILL.md").read_text(encoding="utf-8") == content
    assert (installed_dir / "hooks" / "pre-commit.sh").exists()
    assert (installed_dir / "hooks" / "pre-commit.sh").read_text(encoding="utf-8") == "echo 'running hook'"


@pytest.mark.asyncio
async def test_mcp_server_registry_and_injection(tmp_path: Path):
    server_name = f"test-postgres-{uuid.uuid4().hex[:6]}"
    server_cfg = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/db"],
        "env": {"DEBUG": "true"},
    }

    # 1. Register server
    reg = await mcp_registry.register_server(
        name=server_name,
        transport="stdio",
        config=server_cfg,
        source_agent="Antigravity",
    )
    assert reg["action"] == "registered"
    assert reg["name"] == server_name

    # 2. Get server
    server = await mcp_registry.get_server(server_name)
    assert server is not None
    assert server["transport"] == "stdio"
    assert server["config"]["command"] == "npx"

    # 3. Test injection into mock JSON configuration file
    mock_mcp_json = tmp_path / "mcp.json"
    mock_mcp_json.write_text(json.dumps({"mcpServers": {"existing": {}}}), encoding="utf-8")

    res = await mcp_registry.install_server(
        server_name=server_name,
        target_agent_app_id="cursor",
        custom_config_path=mock_mcp_json,
    )
    assert res["status"] == "installed"

    updated = json.loads(mock_mcp_json.read_text(encoding="utf-8"))
    assert "existing" in updated["mcpServers"]
    assert server_name in updated["mcpServers"]
    assert updated["mcpServers"][server_name]["command"] == "npx"


@pytest.mark.asyncio
async def test_mcp_protocol_skill_and_registry_tools():
    # 1. skill_publish via MCP JSON-RPC
    s_name = f"test-mcp-tool-skill-{uuid.uuid4().hex[:6]}"
    req_pub = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "skill_publish",
            "arguments": {
                "name": s_name,
                "content_md": "# Protocol Test Skill",
                "description": "Skill published via MCP tool",
            },
        },
    }
    resp_pub = await mcp_handler.handle_request(req_pub, client_info="Antigravity")
    assert "result" in resp_pub
    text_res = resp_pub["result"]["content"][0]["text"]
    assert "success" in text_res
    assert s_name in text_res

    # 2. skill_list via MCP JSON-RPC
    req_list = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {
            "name": "skill_list",
            "arguments": {"search": s_name},
        },
    }
    resp_list = await mcp_handler.handle_request(req_list)
    assert s_name in resp_list["result"]["content"][0]["text"]

    # 3. mcp_server_publish via MCP JSON-RPC
    srv_name = f"test-github-{uuid.uuid4().hex[:6]}"
    req_srv = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "mcp_server_publish",
            "arguments": {
                "name": srv_name,
                "transport": "sse",
                "config": {"url": "http://10.10.10.11:8200/sse"},
            },
        },
    }
    resp_srv = await mcp_handler.handle_request(req_srv, client_info="Claude")
    assert "success" in resp_srv["result"]["content"][0]["text"]
    assert srv_name in resp_srv["result"]["content"][0]["text"]
