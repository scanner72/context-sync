"""Unit and integration tests for Context Sync MCP Service."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from src.config import settings
from src.api import app, active_sessions
from src.mcp_server import mcp_handler
from src.embeddings import _pseudo_embedding


@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a known test auth token
    settings.auth_token = "test-secret-token"
    active_sessions.clear()


@pytest.mark.asyncio
async def test_pseudo_embedding():
    """Verify fallback embedding generator generates unit normalized vectors."""
    vec = _pseudo_embedding("Hello world context synchronization", dim=384)
    assert len(vec) == 384
    norm = sum(x * x for x in vec)
    assert pytest.approx(norm, 0.001) == 1.0


@pytest.mark.asyncio
async def test_health_check():
    """Verify /health endpoint returns 200 without auth."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "remote-context-store"


@pytest.mark.asyncio
async def test_ui_endpoint():
    """Verify / serves the HTML Web Dashboard."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "Context Sync" in resp.text
        assert "text/html" in resp.headers.get("content-type", "")

        resp_css = await client.get("/static/style.css")
        assert resp_css.status_code == 200



@pytest.mark.asyncio
async def test_auth_rejection():
    """Verify unauthorized requests are rejected with 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # No token
        resp = await client.get("/api/v1/contexts")
        assert resp.status_code == 401

        # Bad Bearer token
        resp = await client.get(
            "/api/v1/contexts",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

        # Bad Query param token
        resp = await client.get("/api/v1/contexts?token=invalid-token")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_success():
    """Verify valid token succeeds via Bearer header or query parameter."""
    with patch("src.context_store.context_store.list_all", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Bearer header
            resp1 = await client.get(
                "/api/v1/contexts",
                headers={"Authorization": "Bearer test-secret-token"},
            )
            assert resp1.status_code == 200

            # 2. Query param
            resp2 = await client.get("/api/v1/contexts?token=test-secret-token")
            assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_mcp_initialize():
    """Verify MCP JSON-RPC initialize handshake."""
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    resp = await mcp_handler.handle_request(req)
    assert resp is not None
    assert resp["id"] == 1
    assert "serverInfo" in resp["result"]
    assert resp["result"]["serverInfo"]["name"] == "remote-context-store"
    assert "tools" in resp["result"]["capabilities"]


@pytest.mark.asyncio
async def test_mcp_tools_list():
    """Verify MCP tools/list returns standard context tools."""
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    resp = await mcp_handler.handle_request(req)
    assert resp is not None
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "context_save" in tool_names
    assert "context_search" in tool_names
    assert "context_get" in tool_names
    assert "context_list" in tool_names
    assert "context_delete" in tool_names


@pytest.mark.asyncio
async def test_mcp_tools_call_save_and_get():
    """Verify context_save and context_get flow."""
    fake_doc = {
        "id": "11111111-2222-3333-4444-555555555555",
        "title": "OAuth2 Architecture Decision",
        "content": "Use PKCE flow with short-lived JWTs and Redis refresh tokens.",
        "tags": ["auth", "security", "oauth2"],
        "project": "core-backend",
        "author_device": "laptop-work",
        "metadata": {},
        "action": "created",
    }

    with patch("src.context_store.context_store.save", new_callable=AsyncMock) as mock_save, \
         patch("src.context_store.context_store.get", new_callable=AsyncMock) as mock_get:
        
        mock_save.return_value = fake_doc
        mock_get.return_value = fake_doc

        # 1. Call context_save
        save_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "context_save",
                "arguments": {
                    "title": fake_doc["title"],
                    "content": fake_doc["content"],
                    "tags": fake_doc["tags"],
                    "project": fake_doc["project"],
                },
            },
        }
        save_resp = await mcp_handler.handle_request(save_req, client_info="laptop-work")
        assert save_resp["id"] == 3
        text_payload = json.loads(save_resp["result"]["content"][0]["text"])
        assert text_payload["status"] == "success"
        assert text_payload["id"] == fake_doc["id"]

        # 2. Call context_get
        get_req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "context_get",
                "arguments": {
                    "context_id": fake_doc["id"],
                },
            },
        }
        get_resp = await mcp_handler.handle_request(get_req)
        assert get_resp["id"] == 4
        doc_payload = json.loads(get_resp["result"]["content"][0]["text"])
        assert doc_payload["title"] == fake_doc["title"]
        assert doc_payload["tags"] == fake_doc["tags"]


@pytest.mark.asyncio
async def test_mcp_tools_call_search():
    """Verify context_search returns ranked items."""
    search_results = [
        {
            "id": "11111111-2222-3333-4444-555555555555",
            "title": "OAuth2 Architecture Decision",
            "content": "Use PKCE flow with short-lived JWTs.",
            "tags": ["auth", "security"],
            "project": "core-backend",
            "score": 0.88,
        }
    ]

    with patch("src.context_store.context_store.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = search_results

        search_req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "context_search",
                "arguments": {
                    "query": "How is authentication handled?",
                },
            },
        }
        resp = await mcp_handler.handle_request(search_req)
        assert resp["id"] == 5
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert payload["count"] == 1
        assert payload["results"][0]["score"] == 0.88


@pytest.mark.asyncio
async def test_mcp_resources():
    """Verify MCP resources/list and resources/read."""
    with patch("src.context_store.context_store.list_all", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [{"id": "abc", "title": "Test Title"}]

        # 1. List
        list_req = {"jsonrpc": "2.0", "id": 6, "method": "resources/list", "params": {}}
        list_resp = await mcp_handler.handle_request(list_req)
        assert list_resp["id"] == 6
        assert len(list_resp["result"]["resources"]) >= 1
        assert list_resp["result"]["resources"][0]["uri"] == "context://recent"

        # 2. Read
        read_req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/read",
            "params": {"uri": "context://recent"},
        }
        read_resp = await mcp_handler.handle_request(read_req)
        assert read_resp["id"] == 7
        content = json.loads(read_resp["result"]["contents"][0]["text"])
        assert len(content) == 1
        assert content[0]["title"] == "Test Title"


@pytest.mark.asyncio
async def test_messages_session_validation():
    """Verify /messages requires active SSE session."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Invalid session_id
        resp = await client.post(
            "/messages?session_id=nonexistent",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Authorization": "Bearer test-secret-token"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_fleet_tracker_api():
    """Verify fleet tracking registers active agents."""
    from src.fleet import fleet_tracker
    fleet_tracker._sessions.clear()

    sess = fleet_tracker.register("test-sess-1", "127.0.0.1", user_agent="Cursor/1.0", device_name="Dev-PC")
    sess.record_activity("context_search")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/fleet", headers={"Authorization": "Bearer test-secret-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["agents"][0]["device_name"] == "Dev-PC"
        assert data["agents"][0]["last_tool_called"] == "context_search"


@pytest.mark.asyncio
async def test_scanner_injection(tmp_path):
    """Verify agent config scanner and injector safely writes configs with backup."""
    from src.scanner import AgentTarget, inject_mcp_server

    fake_config = tmp_path / "claude_desktop_config.json"
    fake_config.write_text('{"mcpServers": {"old-server": {}}}', encoding="utf-8")

    target = AgentTarget("Claude Desktop", "claude-desktop", fake_config, detected=True)
    success = inject_mcp_server(target, "http://localhost:8000/sse", "test-token-123")
    assert success is True

    # Check that .bak was created
    bak_file = tmp_path / "claude_desktop_config.json.bak"
    assert bak_file.exists()

    # Check updated content for Claude Desktop (stdio command proxy)
    updated = json.loads(fake_config.read_text(encoding="utf-8"))
    assert "remote-context" in updated["mcpServers"]
    assert "command" in updated["mcpServers"]["remote-context"]
    assert "mcp-remote" in updated["mcpServers"]["remote-context"]["args"]
    assert "old-server" in updated["mcpServers"]

    # Also test standard SSE target (e.g. Cursor)
    cursor_config = tmp_path / "cursor_mcp.json"
    cursor_config.write_text('{"mcpServers": {}}', encoding="utf-8")
    cursor_target = AgentTarget("Cursor IDE", "cursor", cursor_config, detected=True)
    inject_mcp_server(cursor_target, "http://localhost:8000/sse", "test-token-123")
    cursor_updated = json.loads(cursor_config.read_text(encoding="utf-8"))
    assert cursor_updated["mcpServers"]["remote-context"]["url"] == "http://localhost:8000/sse"
    assert cursor_updated["mcpServers"]["remote-context"]["headers"]["Authorization"] == "Bearer test-token-123"


@pytest.mark.asyncio
async def test_scanner_inject_all_api(tmp_path):
    """Verify /api/v1/scanner/inject-all endpoint triggers batch configuration."""
    from httpx import AsyncClient, ASGITransport
    from src.api import app
    from unittest.mock import patch
    from src.scanner import AgentTarget

    fake_config = tmp_path / "mcp.json"
    fake_config.write_text("{}", encoding="utf-8")
    mock_targets = [
        AgentTarget(name="Mock Agent", app_id="mock-agent", config_path=fake_config, detected=True, configured=False)
    ]

    with patch("src.api.scan_agents", return_value=mock_targets):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/scanner/inject-all",
                json={"force": False},
                headers={"Authorization": "Bearer test-secret-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert data["processed"] == 1
            assert data["successful"] == 1


@pytest.mark.asyncio
async def test_stream_http_initialize_and_tools():
    """Verify Stream over HTTP (POST /sse and POST /mcp) works for modern MCP clients."""
    from httpx import AsyncClient, ASGITransport
    from src.api import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /sse initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "Antigravity", "version": "1.0"},
            },
        }
        resp = await client.post(
            "/sse",
            json=init_req,
            headers={"Authorization": "Bearer test-secret-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert "serverInfo" in data["result"]
        assert data["result"]["serverInfo"]["name"] == "remote-context-store"

        # 2. POST /sse notifications/initialized
        notif_req = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        resp_notif = await client.post(
            "/sse",
            json=notif_req,
            headers={"Authorization": "Bearer test-secret-token"},
        )
        assert resp_notif.status_code == 200

        # 3. POST /sse tools/list
        tools_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        resp_tools = await client.post(
            "/sse",
            json=tools_req,
            headers={"Authorization": "Bearer test-secret-token"},
        )
        assert resp_tools.status_code == 200
        tools_data = resp_tools.json()
        assert "tools" in tools_data["result"]
        tool_names = [t["name"] for t in tools_data["result"]["tools"]]
        assert "context_search" in tool_names
        assert "context_save" in tool_names

        # 4. GET /.well-known/oauth-protected-resource
        oauth_resp = await client.get("/.well-known/oauth-protected-resource")
        assert oauth_resp.status_code == 200


