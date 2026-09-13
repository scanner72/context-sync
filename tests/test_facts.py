import uuid
import pytest
import pytest_asyncio
from src.facts import fact_store, get_authority_weight
from src.mcp_server import mcp_handler
from src.syncer.digest import format_digest_block


@pytest.mark.asyncio
async def test_fact_creation_and_retrieval():
    project = f"test-flcr-1-{uuid.uuid4().hex[:6]}"
    
    # 1. Create a fact

    res = await fact_store.set_fact(
        entity="backend",
        attribute="port",
        value=8200,
        project=project,
        source_agent="Antigravity",
    )
    assert res["action"] == "created"
    assert res["version"] == 1
    assert res["is_active"] is True
    assert res["value"] == 8200

    # 2. Get the fact
    fact = await fact_store.get_fact(entity="backend", attribute="port", project=project)
    assert fact is not None
    assert fact["value"] == 8200
    assert fact["source_agent"] == "Antigravity"

    # 3. Unchanged value update
    res2 = await fact_store.set_fact(
        entity="backend",
        attribute="port",
        value=8200,
        project=project,
        source_agent="Claude",
    )
    assert res2["action"] == "unchanged"
    assert res2["version"] == 1


@pytest.mark.asyncio
async def test_fact_lww_conflict_resolution():
    project = f"test-flcr-lww-{uuid.uuid4().hex[:6]}"

    # Step 1: Codex sets database to sqlite

    f1 = await fact_store.set_fact(
        entity="database",
        attribute="engine",
        value="sqlite",
        project=project,
        source_agent="Codex",
        policy="lww",
    )
    assert f1["action"] == "created"
    assert f1["version"] == 1

    # Step 2: Claude decides to switch to postgresql
    f2 = await fact_store.set_fact(
        entity="database",
        attribute="engine",
        value="postgresql",
        project=project,
        source_agent="Claude",
        policy="lww",
    )
    assert f2["action"] == "superseded_previous"
    assert f2["version"] == 2
    assert f2["value"] == "postgresql"
    assert f2["previous_value"] == "sqlite"

    # Step 3: Check active fact
    active = await fact_store.get_fact(entity="database", attribute="engine", project=project)
    assert active["value"] == "postgresql"
    assert active["is_active"] is True

    # Step 4: Check full history
    history = await fact_store.get_fact_history(entity="database", attribute="engine", project=project)
    assert len(history) == 2
    assert history[0]["version"] == 1
    assert history[0]["is_active"] is False
    assert history[0]["superseded_by"] == str(active["id"])
    assert history[1]["version"] == 2
    assert history[1]["is_active"] is True


@pytest.mark.asyncio
async def test_fact_authority_policy():
    project = f"test-flcr-auth-{uuid.uuid4().hex[:6]}"

    # 1. Human user explicitly sets API port to 8200

    user_fact = await fact_store.set_fact(
        entity="server",
        attribute="port",
        value=8200,
        project=project,
        source_agent="user",
        policy="authority",
    )
    assert user_fact["action"] == "created"

    # 2. Worker subagent attempts to overwrite with 8000
    worker_fact = await fact_store.set_fact(
        entity="server",
        attribute="port",
        value=8000,
        project=project,
        source_agent="unknown",
        policy="authority",
    )
    # Lower authority agent should be rejected and flagged as conflict
    assert worker_fact["action"] == "rejected_due_to_authority"
    assert worker_fact["conflict_detected"] is True
    assert worker_fact["conflict_flag"] is True
    assert worker_fact["conflict_details"]["rejected_value"] == 8000

    # 3. Active fact remains user's 8200
    active = await fact_store.get_fact(entity="server", attribute="port", project=project)
    assert active["value"] == 8200
    assert active["conflict_flag"] is True

    # 4. Resolve the conflict
    resolved = await fact_store.resolve_conflict(
        fact_id=active["id"],
        chosen_value=8200,
        resolver_agent="user",
    )
    assert resolved["conflict_flag"] is False
    assert resolved["conflict_details"]["resolved_by"] == "user"


@pytest.mark.asyncio
async def test_fact_mcp_tools():
    # Test MCP tool dispatch for fact_set, fact_get, fact_list, fact_history
    project = f"test-flcr-mcp-{uuid.uuid4().hex[:6]}"

    # 1. fact_set tool

    set_req = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "fact_set",
            "arguments": {
                "entity": "auth",
                "attribute": "strategy",
                "value": "bearer-jwt",
                "project": project,
            },
        },
    }
    set_resp = await mcp_handler.handle_request(set_req, client_info="Antigravity")
    assert "result" in set_resp
    text_content = set_resp["result"]["content"][0]["text"]
    assert "success" in text_content
    assert "bearer-jwt" in text_content

    # 2. fact_get tool
    get_req = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {
            "name": "fact_get",
            "arguments": {
                "entity": "auth",
                "attribute": "strategy",
                "project": project,
            },
        },
    }
    get_resp = await mcp_handler.handle_request(get_req)
    assert "bearer-jwt" in get_resp["result"]["content"][0]["text"]

    # 3. fact_list tool
    list_req = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "fact_list",
            "arguments": {"project": project},
        },
    }
    list_resp = await mcp_handler.handle_request(list_req)
    assert "auth" in list_resp["result"]["content"][0]["text"]


@pytest.mark.asyncio
async def test_digest_facts_rendering():
    project = f"test-flcr-digest-{uuid.uuid4().hex[:6]}"
    await fact_store.set_fact(

        entity="infrastructure",
        attribute="cluster_ip",
        value="10.10.10.11",
        project=project,
        source_agent="Antigravity",
    )
    
    digest_md = await fact_store.render_facts_digest(project=project)
    assert "Truth-Table" in digest_md
    assert "infrastructure" in digest_md
    assert "10.10.10.11" in digest_md

    # Test format_digest_block with facts_markdown
    full_block = format_digest_block(
        project_name=project,
        recent_sessions=[],
        active_agents=["Antigravity"],
        facts_markdown=digest_md,
    )
    assert "### 📌 Утвержденные факты проекта (Truth-Table):" in full_block
    assert "10.10.10.11" in full_block
