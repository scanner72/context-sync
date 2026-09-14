# REST & MCP API Reference

Comprehensive specification of all REST endpoints and Model Context Protocol (MCP) JSON-RPC tools provided by the Remote Context Service.

---

## 1. Authentication

All REST endpoints and SSE streams require token verification.
- **Header**: `Authorization: Bearer <API_TOKEN>`
- **Query Param**: `?token=<API_TOKEN>`

Default Development Token: `ctx_secret_token_7f9a8b1c4e2d3f5a`

---

## 2. REST Endpoints

### 2.1 Health Check
- **Endpoint**: `GET /health`
- **Auth Required**: No
- **Response**:
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "db": "connected"
  }
  ```

### 2.2 Save Context
- **Endpoint**: `POST /api/v1/contexts`
- **Request Body**:
  ```json
  {
    "title": "PostgreSQL HNSW Index Tuning",
    "content": "Configured HNSW m=16 and ef_construction=64 for pgvector index.",
    "tags": ["database", "pgvector", "performance"],
    "project": "context_sync",
    "agent_id": "Antigravity"
  }
  ```
- **Response (HTTP 201)**:
  ```json
  {
    "id": "c7a8b3d2-4f1e-4b9a-8c5d-6e2f1a3b4c5d",
    "status": "saved"
  }
  ```

### 2.3 Semantic Search
- **Endpoint**: `POST /api/v1/contexts/search`
- **Request Body**:
  ```json
  {
    "query": "vector indexing parameters",
    "project": "context_sync",
    "limit": 5,
    "threshold": 0.5
  }
  ```
- **Response (HTTP 200)**:
  ```json
  {
    "results": [
      {
        "id": "c7a8b3d2-4f1e-4b9a-8c5d-6e2f1a3b4c5d",
        "title": "PostgreSQL HNSW Index Tuning",
        "content": "Configured HNSW m=16 and ef_construction=64 for pgvector index.",
        "similarity": 0.884,
        "agent_id": "Antigravity",
        "created_at": "2026-09-11T12:00:00Z"
      }
    ]
  }
  ```

### 2.4 Agent Fleet Discovery
- **Endpoint**: `GET /api/v1/fleet`
- **Response (HTTP 200)**:
  ```json
  {
    "agents": [
      {
        "id": "Antigravity",
        "status": "active",
        "last_seen": "2026-09-11T14:20:00Z",
        "detected_via": "antigravity_logs"
      },
      {
        "id": "Cursor",
        "status": "active",
        "last_seen": "2026-09-11T14:18:00Z",
        "detected_via": "cursor_mcp_sse"
      }
    ]
  }
  ```

---

## 3. Atomic Facts & Conflict Resolution API (FLCR)

The Fact-Level Conflict Resolution (FLCR) engine manages version-controlled atomic project facts (triplets: `Entity -> Attribute -> Value`) with conflict detection policies (`lww` and `authority`).

### 3.1 List Active Facts (Truth-Table)
- **Endpoint**: `GET /api/v1/facts`
- **Query Params**:
  - `project` (str, optional, default: `"global"`)
  - `entity` (str, optional): Filter by entity (e.g., `"backend"`, `"database"`)
- **Response (HTTP 200)**:
  ```json
  {
    "project": "global",
    "count": 2,
    "facts": [
      {
        "id": "7f8b9c1d-2e3a-4b5c-6d7e-8f9a0b1c2d3e",
        "project": "global",
        "entity": "backend",
        "attribute": "port",
        "value": 8200,
        "source_agent": "Antigravity",
        "confidence": 1.0,
        "version": 2,
        "is_active": true,
        "superseded_by": null,
        "conflict_flag": false,
        "conflict_details": null,
        "created_at": "2026-09-13T17:40:00Z",
        "updated_at": "2026-09-13T17:45:00Z"
      }
    ]
  }
  ```

### 3.2 Set or Update Fact
- **Endpoint**: `POST /api/v1/facts`
- **Request Body**:
  ```json
  {
    "entity": "database",
    "attribute": "port",
    "value": 5445,
    "project": "context_sync",
    "source_agent": "Antigravity",
    "confidence": 1.0,
    "policy": "lww"
  }
  ```
- **Supported Policies**:
  - `lww` (Last-Write-Wins): Automatically supersedes older fact versions.
  - `authority`: Rejects overwrite if incoming source authority is lower than current author. Sets `conflict_flag: true`.
- **Response (HTTP 200)**:
  ```json
  {
    "id": "9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4",
    "action": "superseded_previous",
    "conflict_detected": false,
    "version": 2,
    "previous_value": 5432
  }
  ```

### 3.3 Get Active Fact
- **Endpoint**: `GET /api/v1/facts/{entity}/{attribute}`
- **Query Params**: `project` (str, default: `"global"`)
- **Response (HTTP 200)**: Returns the active `ProjectFact` object.

### 3.4 Audit Fact Version History
- **Endpoint**: `GET /api/v1/facts/{entity}/{attribute}/history`
- **Query Params**: `project` (str, default: `"global"`)
- **Response (HTTP 200)**: Complete chronological audit trail showing all previous versions, agents, and timestamps.

### 3.5 Manually Resolve Contested Conflict
- **Endpoint**: `POST /api/v1/facts/resolve`
- **Request Body**:
  ```json
  {
    "fact_id": "9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4",
    "chosen_value": 8200,
    "resolver_agent": "user"
  }
  ```
- **Response (HTTP 200)**: Resolves the conflict flag and updates the truth-table.

---

## 4. Cross-Agent Skills Replication API

Central repository for publishing, searching, and unpacking agent skills (`SKILL.md` instructions, triggers, and bundled scripts) across Antigravity, Cursor, Claude Code, Codex, and Windsurf.

### 4.1 List Skills
- **Endpoint**: `GET /api/v1/skills`
- **Query Params**: `tag` (str, opt), `search` (str, opt), `limit` (int, opt)

### 4.2 Publish Skill
- **Endpoint**: `POST /api/v1/skills`
- **Request Body**:
  ```json
  {
    "name": "docker-expert",
    "content_md": "---\nname: docker-expert\ndescription: Docker wizardry\n---\n# Instructions...",
    "description": "Docker wizardry",
    "version": "1.0.0",
    "files_bundle": {"scripts/check_ports.py": "print('ok')"},
    "tags": ["docker", "devops"]
  }
  ```

### 4.3 Install Skill into Agent Filesystem
- **Endpoint**: `POST /api/v1/skills/{name}/install`
- **Request Body**: `{"target_agent": "cursor"}` (or `"claude"`, `"antigravity"`, `"codex"`, `"all"`)

---

## 5. MCP Fleet Hub Registry API

Registry for sharing external MCP server definitions and deploying them across installed coding agents.

### 5.1 List Registered Servers
- **Endpoint**: `GET /api/v1/mcp-registry`

### 5.2 Register Server
- **Endpoint**: `POST /api/v1/mcp-registry`
- **Request Body**:
  ```json
  {
    "name": "github",
    "transport": "stdio",
    "config": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "..."}
    }
  }
  ```

### 5.3 Install Server into Agents
- **Endpoint**: `POST /api/v1/mcp-registry/{name}/install`
- **Request Body**: `{"target_agent": "all"}` (or specific app_id: `"cursor"`, `"claude-desktop"`, etc.)

---

## 6. MCP JSON-RPC Tools

When connected via `/sse` or stdio, the following tools are exposed via the standard MCP protocol:

### Context & Knowledge Base Tools
| Tool Name | Parameters | Description |
|---|---|---|
| `context_save` | `title` (str), `content` (str), `tags` (list[str], opt), `project` (str, opt), `metadata` (obj, opt) | Persists and indexes knowledge chunk with FastEmbed vector. |
| `context_search` | `query` (str), `project` (str, opt), `tags` (list[str], opt), `limit` (int, opt), `min_score` (float, opt) | Cosine similarity semantic vector search. |
| `context_get` | `context_id` (str) | Retrieves complete content and metadata by UUID or title. |
| `context_list` | `project` (str, opt), `limit` (int, opt) | Paginated list of stored memories. |
| `context_delete` | `context_id` (str) | Removes an item from the context store. |

### Fact-Level Conflict Resolution (FLCR) Tools
| Tool Name | Parameters | Description |
|---|---|---|
| `fact_set` | `entity` (str), `attribute` (str), `value` (any), `project` (str, opt), `confidence` (float, opt), `policy` (`"lww"` \| `"authority"`, opt) | Atomically stores/updates a fact with versioning and conflict policy. |
| `fact_get` | `entity` (str), `attribute` (str), `project` (str, opt) | Retrieves current active fact for given entity & attribute. |
| `fact_list` | `project` (str, opt), `entity` (str, opt) | Returns full project Truth-Table of active facts. |
| `fact_history` | `entity` (str), `attribute` (str), `project` (str, opt) | Returns complete audit trail of past versions and conflicts. |

### Skills Replication Tools
| Tool Name | Parameters | Description |
|---|---|---|
| `skill_publish` | `name` (str), `content_md` (str), `description` (str, opt), `version` (str, opt), `files_bundle` (obj, opt), `tags` (list, opt) | Publish or update a skill in the centralized fleet repository. |
| `skill_list` | `search` (str, opt), `tag` (str, opt) | Search and list available skills created across the agent fleet. |
| `skill_get` | `name` (str) | Fetch full skill specification, instructions, and bundled assets. |
| `skill_install` | `name` (str), `target_agent` (str, default: `'all'`) | Unpack and install skill into target agent directory. |

### MCP Fleet Registry Tools
| Tool Name | Parameters | Description |
|---|---|---|
| `mcp_server_publish` | `name` (str), `transport` (`"stdio"` \| `"sse"`), `config` (obj) | Register a validated external MCP server in the fleet hub. |
| `mcp_server_list` | `only_active` (bool, default: `true`) | List available registered MCP servers. |
| `mcp_server_install` | `name` (str), `target_agent` (str, default: `'all'`) | Deploy an MCP server into local agent JSON configuration files. |
