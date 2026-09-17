"""FastAPI application with MCP SSE transport, Bearer authentication, and REST endpoints."""

import json
import uuid
import asyncio
import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Security, Depends, status, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config import settings
from src.database import init_db
from src.mcp_server import mcp_handler
from src.context_store import context_store
from src.facts import fact_store
from src.skills import skills_store
from src.mcp_registry import mcp_registry
from src.fleet import fleet_tracker
from src.scanner import scan_agents, inject_mcp_server


logger = logging.getLogger(__name__)

# Security scheme for Swagger UI & header validation
security_scheme = HTTPBearer(auto_error=False)

# In-memory store for active SSE client message queues: session_id -> asyncio.Queue
active_sessions: Dict[str, asyncio.Queue] = {}

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing database schema...")
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database init warning (might be using SQLite/mock or pending migration): {e}")
    yield
    logger.info("Shutting down context sync service...")


app = FastAPI(
    title="Remote Context Store MCP Service",
    description="Cross-device AI Context Synchronizer & Vector Memory via Model Context Protocol (MCP).",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static assets (CSS, JS, icons)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Enable CORS for web-based or remote clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["UI"], include_in_schema=False)
async def serve_ui():
    """Serve the Web Dashboard SPA."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return JSONResponse({"message": "Remote Context Store API is running. UI assets not found."})


def _get_effective_base_url(request: Request) -> str:
    """Derive external base URL taking reverse proxy headers into account."""
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        proto = forwarded_proto or request.url.scheme
        return f"{proto}://{forwarded_host}".rstrip("/")
    return str(request.base_url).rstrip("/")


@app.get("/scanner.py", tags=["Agent Bootstrap"])
async def serve_scanner_script():
    """Download standalone agent scanner & MCP injector script."""
    scanner_path = Path(__file__).resolve().parent / "scanner.py"
    if not scanner_path.exists():
        raise HTTPException(status_code=404, detail="scanner.py not found")
    return FileResponse(
        path=str(scanner_path),
        media_type="text/x-python",
        filename="scanner.py",
    )


@app.get("/install.ps1", tags=["Agent Bootstrap"], response_class=PlainTextResponse)
async def serve_install_ps1(request: Request, token: Optional[str] = Query(None)):
    """PowerShell one-liner installer for Windows machines."""
    base_url = _get_effective_base_url(request)
    auth_token = token or settings.auth_token
    script = f"""# ContextSync Windows Auto-Installer & Scanner
$ErrorActionPreference = "Stop"
try {{ [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 }} catch {{}}
try {{ $OutputEncoding = [System.Text.Encoding]::UTF8 }} catch {{}}
$BaseUrl = "{base_url}"
$Token = "{auth_token}"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   ContextSync AI Agent Scanner & MCP Auto-Connector   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Detect Python
$pythonExe = $null
foreach ($cmd in @("python", "py", "python3")) {{
    try {{
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $ver -match "Python") {{
            $pythonExe = $cmd
            break
        }}
    }} catch {{}}
}}

if (-not $pythonExe) {{
    Write-Host "[ERROR] Python 3 не найден в системе (PATH)." -ForegroundColor Red
    Write-Host "Установите Python 3 с https://www.python.org/ и перезапустите терминал." -ForegroundColor Yellow
    exit 1
}}

# 2. Download standalone scanner.py to temp folder
$tempFile = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "context_scanner_$([System.Guid]::NewGuid().ToString('N')).py")

try {{
    Write-Host "[1/2] Загрузка сканера с $BaseUrl/scanner.py ..." -ForegroundColor Gray
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "$BaseUrl/scanner.py" -OutFile $tempFile -UseBasicParsing

    Write-Host "[2/2] Запуск сканирования и автоподключения агентов..." -ForegroundColor Green
    & $pythonExe $tempFile --url "$BaseUrl/sse" --token "$Token" @args
}} finally {{
    if (Test-Path $tempFile) {{
        Remove-Item -Force $tempFile -ErrorAction SilentlyContinue
    }}
}}
"""
    return PlainTextResponse(content=script, media_type="text/plain; charset=utf-8")


@app.get("/install.sh", tags=["Agent Bootstrap"], response_class=PlainTextResponse)
async def serve_install_sh(request: Request, token: Optional[str] = Query(None)):
    """Bash one-liner installer for Linux / macOS machines."""
    base_url = _get_effective_base_url(request)
    auth_token = token or settings.auth_token
    script = f"""#!/usr/bin/env bash
set -e

BASE_URL="{base_url}"
TOKEN="{auth_token}"

echo -e "\\033[36m========================================================\\033[0m"
echo -e "\\033[36m   ContextSync AI Agent Scanner & MCP Auto-Connector    \\033[0m"
echo -e "\\033[36m========================================================\\033[0m"

PYTHON_BIN=""
for cmd in python3 python py; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PYTHON_BIN="$cmd"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "\\033[31m[ERROR] Python 3 не найден в системе (PATH).\\033[0m"
    echo -e "\\033[33mУстановите Python 3 (apt install python3 / brew install python3) и повторите.\\033[0m"
    exit 1
fi

TMP_FILE=$(mktemp /tmp/context_scanner_XXXXXX.py)
trap 'rm -f "$TMP_FILE"' EXIT

echo -e "\\033[90m[1/2] Загрузка сканера с $BASE_URL/scanner.py ...\\033[0m"
if command -v curl >/dev/null 2>&1; then
    curl -sSL "$BASE_URL/scanner.py" -o "$TMP_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$BASE_URL/scanner.py" -O "$TMP_FILE"
else
    echo -e "\\033[31m[ERROR] Не найден curl или wget.\\033[0m"
    exit 1
fi

echo -e "\\033[32m[2/2] Запуск сканирования и автоподключения агентов...\\033[0m"
"$PYTHON_BIN" "$TMP_FILE" --url "$BASE_URL/sse" --token "$TOKEN" "$@"
"""
    return PlainTextResponse(content=script, media_type="text/plain; charset=utf-8")


async def verify_token(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    token: Optional[str] = Query(None, description="Auth token via query parameter"),
) -> str:
    """Validate Bearer token from header or URL query parameter."""
    provided_token: Optional[str] = None

    # Check Authorization header: Bearer <token>
    if auth and auth.credentials:
        provided_token = auth.credentials

    # Check query parameter ?token=<token>
    elif token:
        provided_token = token

    # Check raw header as fallback
    elif "Authorization" in request.headers:
        header_val = request.headers["Authorization"]
        if header_val.startswith("Bearer "):
            provided_token = header_val[7:].strip()

    if not provided_token or provided_token != settings.auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return provided_token


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Docker / orchestration."""
    return {
        "status": "healthy",
        "service": "remote-context-store",
        "embedding_provider": settings.embedding_provider,
        "active_sse_sessions": len(active_sessions),
    }


@app.get("/api/v1/system/info", tags=["System"])
async def system_info(request: Request):
    """Provide system info and auto-auth token for localhost clients."""
    client_host = request.client.host if request.client else ""
    # In Docker Desktop on Windows or local loopback:
    is_local = (
        client_host in ("127.0.0.1", "::1", "localhost", "testclient")
        or client_host.startswith("192.168.")
        or client_host.startswith("10.")
        or client_host.startswith("172.")
    )
    return {
        "is_localhost": is_local,
        "auth_token": settings.auth_token if is_local else None,
        "service": "remote-context-store",
        "status": "healthy",
        "embedding_provider": settings.embedding_provider,
    }


@app.get("/.well-known/oauth-protected-resource", include_in_schema=False)
@app.get("/.well-known/oauth-protected-resource/{path:path}", include_in_schema=False)
async def oauth_protected_resource():
    """OAuth 2.0 Protected Resource Metadata (RFC 9728) for MCP client discovery."""
    return {
        "resource": "http://localhost:8000",
        "authorization_servers": [],
        "scopes_supported": [],
        "bearer_methods_supported": ["header", "query"],
    }


# ============================================================================
# MCP SSE & Stream over HTTP Transport Endpoints
# ============================================================================

@app.get("/sse", tags=["MCP"])
@app.get("/mcp", tags=["MCP"])
async def mcp_sse_endpoint(
    request: Request,
    _token: str = Depends(verify_token),
):
    """MCP SSE endpoint.
    
    Establishes Server-Sent Events stream with client and registers message queue.
    """
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    active_sessions[session_id] = queue

    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent")
    client_device = request.headers.get("X-Client-Device") or request.query_params.get("device")
    fleet_tracker.register(session_id, client_host, user_agent, client_device)
    logger.info(f"New MCP SSE client connected: session_id={session_id}, host={client_host}")

    async def event_generator():
        try:
            # 1. First event required by MCP SSE spec: advertise the message POST endpoint
            # Client will append session_id when posting messages
            endpoint_path = f"/messages?session_id={session_id}"
            yield f"event: endpoint\r\ndata: {endpoint_path}\r\n\r\n"

            # 2. Main event loop: stream messages from queue or emit heartbeat ping
            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info(f"MCP SSE client disconnected: session_id={session_id}")
                    break

                try:
                    # Wait for message with 15s timeout for heartbeat
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: message\r\ndata: {json.dumps(msg, ensure_ascii=False)}\r\n\r\n"
                    queue.task_done()
                except asyncio.TimeoutError:
                    # Send periodic SSE comment to keep TCP connection active through proxies/NAT
                    yield ": ping\r\n\r\n"

        finally:
            active_sessions.pop(session_id, None)
            fleet_tracker.unregister(session_id)
            logger.info(f"Cleaned up MCP session {session_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/messages", tags=["MCP"])
async def mcp_messages_endpoint(
    request: Request,
    session_id: str = Query(..., description="Active session ID received from SSE endpoint"),
    _token: str = Depends(verify_token),
):
    """MCP message receiver.
    
    Receives JSON-RPC 2.0 requests from client and routes them through the MCP Server.
    """
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active session '{session_id}' not found. Please connect to /sse first.",
        )

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}")

    client_device = request.headers.get("X-Client-Device") or request.headers.get("User-Agent")
    
    # Record fleet activity
    tool_name = None
    if body.get("method") == "tools/call":
        tool_name = body.get("params", {}).get("name")
    fleet_tracker.record_activity(session_id, tool_name)

    # Process the request through MCP server handler
    response = await mcp_handler.handle_request(body, client_info=client_device)

    # If the method was a request that requires a response, send it back via SSE queue
    if response is not None:
        queue = active_sessions.get(session_id)
        if queue:
            await queue.put(response)

    # Return HTTP 202 Accepted per MCP HTTP transport specification
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"status": "accepted"})


@app.post("/sse", tags=["MCP"])
@app.post("/mcp", tags=["MCP"])
async def mcp_stream_http_endpoint(
    request: Request,
    _token: str = Depends(verify_token),
):
    """Handle MCP Stream over HTTP (HTTP POST Transport).
    
    Directly receives JSON-RPC 2.0 requests (e.g. initialize, tools/list, tools/call)
    and returns JSON-RPC responses over HTTP without requiring an active SSE stream.
    """
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}")

    client_device = request.headers.get("X-Client-Device") or request.headers.get("User-Agent")
    client_host = request.client.host if request.client else "unknown"

    # Support batch JSON-RPC requests
    is_batch = isinstance(body, list)
    requests_list = body if is_batch else [body]
    responses = []

    for item in requests_list:
        if not isinstance(item, dict):
            continue

        method = item.get("method")
        
        # Track fleet sessions on initialize
        if method == "initialize":
            client_info = item.get("params", {}).get("clientInfo", {})
            client_name = client_info.get("name") or client_device or "MCP Client"
            sess_id = str(uuid.uuid4())
            fleet_tracker.register(
                sess_id, client_host, user_agent=client_device, device_name=client_name
            )

        # Track fleet tool calls
        if method == "tools/call":
            tool_name = item.get("params", {}).get("name")
            for s in fleet_tracker._sessions.values():
                s.record_activity(tool_name)

        resp = await mcp_handler.handle_request(item, client_info=client_device)
        if resp is not None:
            responses.append(resp)

    if is_batch:
        return JSONResponse(status_code=200, content=responses)
    
    if responses:
        return JSONResponse(status_code=200, content=responses[0])
    
    # For notifications (e.g. notifications/initialized) where no JSON-RPC response is returned
    return JSONResponse(status_code=200, content={"status": "accepted"})


# ============================================================================
# Fleet & Auto-Scanner Endpoints
# ============================================================================

@app.get("/api/v1/fleet", tags=["Fleet"])
async def get_fleet_api(_token: str = Depends(verify_token)):
    """List all connected agent sessions and registered fleet computers."""
    agents = fleet_tracker.list_active()
    nodes = fleet_tracker.list_nodes()
    return {
        "agents": agents,
        "count": len(agents),
        "nodes": nodes,
        "nodes_count": len(nodes),
    }


@app.post("/api/v1/fleet/register", tags=["Fleet"])
async def register_fleet_node_api(
    data: Dict[str, Any],
    request: Request,
    _token: str = Depends(verify_token),
):
    """Register or heartbeat a remote workstation/laptop in the Fleet registry."""
    reported_ip = data.get("client_ip")
    client_ip = (
        reported_ip
        or request.headers.get("X-Real-IP")
        or (request.headers.get("X-Forwarded-For", "").split(",")[0].strip() if request.headers.get("X-Forwarded-For") else None)
        or (request.client.host if request.client else "unknown")
    )
    hostname = data.get("hostname") or client_ip
    os_name = data.get("os_name") or "unknown"
    username = data.get("username") or ""
    agents = data.get("agents") or []

    node = fleet_tracker.register_node(
        hostname=hostname,
        ip=client_ip,
        os_name=os_name,
        username=username,
        agents=agents,
    )
    return {"status": "success", "node": node.to_dict()}


@app.get("/api/v1/scanner", tags=["Scanner"])
async def get_scanner_api(_token: str = Depends(verify_token)):
    """Scan local host for installed coding agents and IDE configurations."""
    targets = scan_agents()
    return {
        "targets": [
            {
                "name": t.name,
                "app_id": t.app_id,
                "config_path": str(t.config_path),
                "detected": t.detected,
                "configured": t.configured,
            }
            for t in targets
        ],
        "detected_count": sum(1 for t in targets if t.detected),
        "configured_count": sum(1 for t in targets if t.configured),
    }


@app.post("/api/v1/scanner/inject", tags=["Scanner"])
async def inject_agent_api(
    data: Dict[str, Any],
    request: Request,
    _token: str = Depends(verify_token),
):
    """Auto-inject Remote Context MCP configuration into a detected local agent."""
    app_id = data.get("app_id")
    use_stdio = bool(data.get("use_stdio", False))
    sse_url = data.get("url") or str(request.url_for("mcp_sse_endpoint"))

    targets = scan_agents()
    target = next((t for t in targets if t.app_id == app_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Agent target '{app_id}' not found")

    success = inject_mcp_server(
        target=target,
        sse_url=sse_url,
        token=_token,
        use_command_proxy=use_stdio,
    )
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to inject configuration into {target.name}")

    return {
        "status": "success",
        "agent": target.name,
        "config_path": str(target.config_path),
        "configured": True,
    }


@app.post("/api/v1/scanner/inject-all", tags=["Scanner"])
async def inject_all_agents_api(
    request: Request,
    data: Optional[Dict[str, Any]] = None,
    _token: str = Depends(verify_token),
):
    """Auto-inject Remote Context MCP configuration into all detected agents."""
    payload = data or {}
    force = bool(payload.get("force", False))
    use_stdio = bool(payload.get("use_stdio", False))
    sse_url = payload.get("url") or str(request.url_for("mcp_sse_endpoint"))

    targets = scan_agents()
    results = []
    for t in targets:
        if t.detected and (force or not t.configured):
            success = inject_mcp_server(
                target=t,
                sse_url=sse_url,
                token=_token,
                use_command_proxy=use_stdio,
            )
            results.append({
                "agent": t.name,
                "app_id": t.app_id,
                "success": success,
                "config_path": str(t.config_path),
            })

    return {
        "status": "success",
        "processed": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "results": results,
    }


# ============================================================================
# Auto-Sync & Projects Endpoints
# ============================================================================

@app.get("/api/v1/sync/status", tags=["Auto-Sync"])
async def sync_status_api(
    _token: str = Depends(verify_token),
):
    """Get status of auto-sync daemon, database stored contexts, and active projects."""
    from src.syncer.daemon import AutoSyncDaemon
    from src.syncer.collectors import get_all_active_projects

    daemon = AutoSyncDaemon()
    projects = []
    try:
        projects = get_all_active_projects()
    except Exception:
        pass

    db_projects = await context_store.get_projects_summary()
    fleet_projects = fleet_tracker.get_all_registered_projects()
    total_proj_count = max(len(projects), len(db_projects), len(fleet_projects))
    total_contexts = sum(p.get("count", 0) for p in db_projects)

    return {
        "status": "ready",
        "last_cycle": daemon.state.get("last_cycle_info", {}),
        "total_projects": total_proj_count,
        "synced_sessions_total": total_contexts or len(daemon.state.get("synced_session_ids", {})),
    }


@app.get("/api/v1/sync/projects", tags=["Auto-Sync"])
async def sync_projects_api(
    _token: str = Depends(verify_token),
):
    """List all detected active projects across fleet workstations, stored database contexts, and local filesystem."""
    from src.syncer.collectors import get_all_active_projects

    projects_map: Dict[str, Dict[str, Any]] = {}

    # 1. Projects registered by fleet workstations (ai-studio, laptops)
    for fp in fleet_tracker.get_all_registered_projects():
        name = fp.get("name") or "unknown"
        projects_map[name.lower()] = {
            "name": name,
            "path": fp.get("path") or "",
            "sources": fp.get("sources") or ["fleet"],
            "host": fp.get("host"),
        }

    # 2. Local filesystem projects (if running locally)
    try:
        local_projects = get_all_active_projects()
        for lp in local_projects:
            name = lp.get("name") or "unknown"
            key = name.lower()
            if key not in projects_map:
                projects_map[key] = lp
            else:
                for s in lp.get("sources", []):
                    if s not in projects_map[key]["sources"]:
                        projects_map[key]["sources"].append(s)
    except Exception:
        pass

    # 3. Database stored projects (contexts already synchronized)
    try:
        db_projects = await context_store.get_projects_summary()
        for dp in db_projects:
            name = dp.get("name") or "global"
            key = name.lower()
            if key in projects_map:
                projects_map[key]["contexts_count"] = dp["count"]
                projects_map[key]["last_updated"] = dp["last_updated"]
            else:
                projects_map[key] = {
                    "name": name,
                    "path": "(синхронизировано в базе знаний)",
                    "sources": ["synced-db"],
                    "contexts_count": dp["count"],
                    "last_updated": dp["last_updated"],
                }
    except Exception as e:
        logger.warning(f"Error reading db projects: {e}")

    result = list(projects_map.values())
    return {"projects": result, "count": len(result)}


@app.post("/api/v1/sync/projects/register", tags=["Auto-Sync"])
async def register_workstation_projects_api(
    request: Request,
    _token: str = Depends(verify_token),
):
    """Register projects discovered on a client workstation."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    hostname = body.get("hostname") or "Unknown Workstation"
    projects = body.get("projects") or []
    fleet_tracker.register_node_projects(hostname, projects)
    return {
        "status": "success",
        "registered_projects": len(projects),
        "hostname": hostname,
    }


@app.post("/api/v1/sync/trigger", tags=["Auto-Sync"])
async def sync_trigger_api(
    _token: str = Depends(verify_token),
):
    """Trigger an immediate cross-agent sync cycle on demand."""
    from src.syncer.daemon import AutoSyncDaemon

    daemon = AutoSyncDaemon(auth_token=_token)
    result = daemon.run_sync_cycle()
    return {
        "status": "completed",
        "result": result,
    }


# ============================================================================
# Optional Direct REST API Endpoints (for web dashboards / curl)
# ============================================================================

@app.get("/api/v1/contexts", tags=["REST API"])
async def list_contexts_api(
    project: Optional[str] = None,
    limit: int = 20,
    _token: str = Depends(verify_token),
):
    """List contexts via REST."""
    items = await context_store.list_all(project=project, limit=limit)
    return {"contexts": items, "count": len(items)}


@app.post("/api/v1/contexts", tags=["REST API"])
async def save_context_api(
    data: Dict[str, Any],
    _token: str = Depends(verify_token),
):
    """Save or update context via REST."""
    title = data.get("title")
    content = data.get("content")
    if not title or not content:
        raise HTTPException(status_code=400, detail="Fields 'title' and 'content' are required")

    result = await context_store.save(
        title=title,
        content=content,
        tags=data.get("tags") or [],
        project=data.get("project", "global"),
        metadata=data.get("metadata") or {},
    )
    return result


@app.post("/api/v1/contexts/search", tags=["REST API"])
async def search_context_api(
    data: Dict[str, Any],
    _token: str = Depends(verify_token),
):
    """Semantic search via REST."""
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Field 'query' is required")

    results = await context_store.search(
        query=query,
        project=data.get("project"),
        tags=data.get("tags"),
        limit=int(data.get("limit", 5)),
        min_score=float(data.get("min_score", 0.25)),
    )
    return {"query": query, "results": results, "count": len(results)}


@app.get("/api/v1/contexts/{context_id}", tags=["REST API"])
async def get_context_api(
    context_id: str,
    _token: str = Depends(verify_token),
):
    """Get context details by ID or title."""
    item = await context_store.get(context_id)
    if not item:
        raise HTTPException(status_code=404, detail="Context not found")
    return item


@app.delete("/api/v1/contexts/{context_id}", tags=["REST API"])
async def delete_context_api(
    context_id: str,
    _token: str = Depends(verify_token),
):
    """Delete context by ID or title."""
    deleted = await context_store.delete(context_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Context not found")
    return {"status": "deleted", "id": context_id}


# ============================================================================
# Atomic Facts & Conflict Resolution API (FLCR)
# ============================================================================

@app.get("/api/v1/facts", tags=["Facts API"])
async def list_facts_api(
    project: str = "global",
    entity: Optional[str] = None,
    _token: str = Depends(verify_token),
):
    """List active atomic project facts (Truth-Table)."""
    facts = await fact_store.list_facts(project=project, entity=entity, only_active=True)
    return {"project": project, "count": len(facts), "facts": facts}


@app.post("/api/v1/facts", tags=["Facts API"])
async def set_fact_api(
    data: Dict[str, Any],
    _token: str = Depends(verify_token),
):
    """Set or update an atomic fact with conflict resolution."""
    entity = data.get("entity")
    attribute = data.get("attribute")
    value = data.get("value")
    if not entity or not attribute or value is None:
        raise HTTPException(status_code=400, detail="'entity', 'attribute', and 'value' are required")

    result = await fact_store.set_fact(
        entity=entity,
        attribute=attribute,
        value=value,
        project=data.get("project", "global"),
        source_agent=data.get("source_agent", "api"),
        confidence=float(data.get("confidence", 1.0)),
        policy=data.get("policy", "lww"),
    )
    return result


@app.get("/api/v1/facts/{entity}/{attribute}", tags=["Facts API"])
async def get_fact_api(
    entity: str,
    attribute: str,
    project: str = "global",
    _token: str = Depends(verify_token),
):
    """Get the current active fact for an entity and attribute."""
    fact = await fact_store.get_fact(entity=entity, attribute=attribute, project=project)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    return fact


@app.get("/api/v1/facts/{entity}/{attribute}/history", tags=["Facts API"])
async def get_fact_history_api(
    entity: str,
    attribute: str,
    project: str = "global",
    _token: str = Depends(verify_token),
):
    """Get full audit and version history for an atomic fact."""
    history = await fact_store.get_fact_history(entity=entity, attribute=attribute, project=project)
    return {"entity": entity, "attribute": attribute, "history": history, "count": len(history)}


@app.post("/api/v1/facts/resolve", tags=["Facts API"])
async def resolve_fact_api(
    data: Dict[str, Any],
    _token: str = Depends(verify_token),
):
    """Explicitly resolve a contested fact conflict."""
    fact_id = data.get("fact_id")
    chosen_value = data.get("chosen_value")
    resolver_agent = data.get("resolver_agent", "user")
    if not fact_id or chosen_value is None:
        raise HTTPException(status_code=400, detail="'fact_id' and 'chosen_value' are required")

    resolved = await fact_store.resolve_conflict(
        fact_id=fact_id,
        chosen_value=chosen_value,
        resolver_agent=resolver_agent,
    )
    if not resolved:
        raise HTTPException(status_code=404, detail="Fact not found")
    return resolved


# ============================================================================
# Skills Management & Cross-Agent Replication API
# ============================================================================

@app.get("/api/v1/skills", tags=["Skills API"])
async def list_skills_api(
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    _token: str = Depends(verify_token),
):
    """List available skills across the AI agent fleet."""
    items = await skills_store.list_skills(tag=tag, search=search, limit=limit)
    return {"count": len(items), "skills": items}


@app.post("/api/v1/skills", tags=["Skills API"])
async def publish_skill_api(
    data: Dict[str, Any],
    _token: str = Depends(verify_token),
):
    """Publish or update a skill in the centralized fleet repository."""
    name = data.get("name")
    content_md = data.get("content_md")
    if not name or not content_md:
        raise HTTPException(status_code=400, detail="'name' and 'content_md' are required")

    res = await skills_store.publish_skill(
        name=name,
        content_md=content_md,
        description=data.get("description"),
        version=data.get("version", "1.0.0"),
        files_bundle=data.get("files_bundle") or {},
        source_agent=data.get("source_agent", "api"),
        tags=data.get("tags") or [],
    )
    return res


@app.get("/api/v1/skills/{name}", tags=["Skills API"])
async def get_skill_api(
    name: str,
    _token: str = Depends(verify_token),
):
    """Retrieve full skill specification and assets."""
    skill = await skills_store.get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return skill


@app.post("/api/v1/skills/{name}/install", tags=["Skills API"])
async def install_skill_api(
    name: str,
    data: Optional[Dict[str, Any]] = None,
    _token: str = Depends(verify_token),
):
    """Deploy skill into local agent filesystem (or all agents)."""
    target = (data or {}).get("target_agent", "all")
    try:
        if target == "all":
            res = await skills_store.install_to_all_agents(name)
        else:
            res = await skills_store.install_skill(name, target)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MCP Fleet Hub Registry & Propagation API
# ============================================================================

@app.get("/api/v1/mcp-registry", tags=["MCP Registry API"])
async def list_mcp_servers_api(
    only_active: bool = True,
    _token: str = Depends(verify_token),
):
    """List all registered external MCP servers."""
    servers = await mcp_registry.list_servers(only_active=only_active)
    return {"count": len(servers), "servers": servers}


@app.post("/api/v1/mcp-registry", tags=["MCP Registry API"])
async def register_mcp_server_api(
    data: Dict[str, Any],
    _token: str = Depends(verify_token),
):
    """Register or update an MCP server configuration in the fleet repository."""
    name = data.get("name")
    transport = data.get("transport")
    config = data.get("config")
    if not name or not transport or not config:
        raise HTTPException(status_code=400, detail="'name', 'transport', and 'config' are required")

    try:
        res = await mcp_registry.register_server(
            name=name,
            transport=transport,
            config=config,
            source_agent=data.get("source_agent", "api"),
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/mcp-registry/{name}", tags=["MCP Registry API"])
async def get_mcp_server_api(
    name: str,
    _token: str = Depends(verify_token),
):
    """Retrieve an MCP server configuration."""
    server = await mcp_registry.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    return server


@app.post("/api/v1/mcp-registry/{name}/install", tags=["MCP Registry API"])
async def install_mcp_server_api(
    name: str,
    data: Optional[Dict[str, Any]] = None,
    _token: str = Depends(verify_token),
):
    """Inject an MCP server into local agent configuration files."""
    target = (data or {}).get("target_agent", "all")
    try:
        if target == "all":
            res = await mcp_registry.install_to_all_detected(name)
        else:
            res = await mcp_registry.install_server(name, target)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


