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

## 3. MCP JSON-RPC Tools

When connected via `/sse`, the following tools are exposed via the standard MCP protocol:

| Tool Name | Parameters | Description |
|---|---|---|
| `context_save` | `title` (str), `content` (str), `tags` (list[str], opt), `project` (str, opt) | Persists and indexes knowledge chunk |
| `context_search` | `query` (str), `project` (str, opt), `limit` (int, opt), `threshold` (float, opt) | Semantic similarity vector search |
| `context_get` | `context_id` (str) | Retrieves complete content and metadata |
| `context_list` | `project` (str, opt), `limit` (int, opt) | Paginated list of stored memories |
| `context_delete` | `context_id` (str) | Removes an item from the vector store |