# Remote Context Architecture & System Design

This document details the architectural principles, component interactions, data flows, and performance considerations of the **Remote Context Synchronization Service**.

---

## 1. High-Level System Architecture

Remote Context operates as an asynchronous, event-driven orchestration bridge between disparate AI coding assistants (Google Antigravity, Cursor, OpenAI Codex, Claude Desktop, Windsurf, Roo/Cline) and a centralized semantic knowledge store.

```
+-----------------------------------------------------------------------------------+
|                               AI AGENT FLEET                                      |
|  +---------------+  +---------------+  +---------------+  +--------------------+  |
|  |  Antigravity  |  |    Cursor     |  | Codex CLI     |  | Claude Desktop     |  |
|  |  (SSE Client) |  | (SSE Client)  |  | (Thread Sync) |  | (mcp-remote stdio) |  |
|  +-------+-------+  +-------+-------+  +-------+-------+  +---------+----------+  |
+----------|------------------|------------------|--------------------|-------------+
           |                  |                  |                    |
           | SSE/JSON-RPC     | SSE/JSON-RPC     | Direct Session     | JSON-RPC Stdio
           v                  v                  v                    v
+-----------------------------------------------------------------------------------+
|                           REMOTE CONTEXT GATEWAY                                  |
|                                                                                   |
|  +---------------------------+       +-----------------------------------------+  |
|  | FastAPI Web & REST Engine |       | FastMCP 2.0 SSE Transport Layer         |  |
|  | - Web UI Dashboard (i18n) |       | - Session Registry                      |  |
|  | - Fleet Discovery API     |       | - Bidirectional Channel /sse & /messages|  |
|  | - Direct CRUD Endpoints   |       | - JSON-RPC 2.0 Dispatcher               |  |
|  +-------------+-------------+       +--------------------+--------------------+  |
|                |                                          |                       |
|  +-------------+------------------------------------------+--------------------+  |
|  | Agent Fleet Tracker                                                         |  |
|  | - Heartbeat & liveness tracking                                             |  |
|  | - Auto-discovery across Windows registry, AppData, and user configs         |  |
|  +-------------------------------------+---------------------------------------+  |
+----------------------------------------|------------------------------------------+
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
+-----------------------------+               +-------------------------------------+
| FastEmbed Local Inference   |               | Autonomous Auto-Sync Daemon         |
| - BAAI/bge-small-en-v1.5    |               | - Project Scanner (VS Code / JetBr) |
| - ONNX Runtime on CPU       |               | - SQLite History Parsers (Codex/Ant)|
| - 384-dimensional vectors   |               | - Cross-Project Digest Synthesizer  |
| - Zero OpenAI API dependency|               | - Safe Marker Injection Engine      |
+--------------+--------------+               +------------------+------------------+
               |                                                 |
               +------------------------+------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                         PERSISTENCE & VECTOR INDEX                                |
|  PostgreSQL 16 + pgvector                                                         |
|  - Table: `contexts` (id, title, content, agent_id, project_hash, embedding)      |
|  - Index: HNSW Cosine Index (m=16, ef_construction=64)                            |
|  - Table: `fleet_agents` (agent_id, status, last_seen, metadata)                  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Breakdown

### 2.1 FastMCP 2.0 Transport Layer (`src/mcp_server.py`)
- **Protocol**: Model Context Protocol (MCP) 2024-11-05 Specification.
- **Transport Mechanism**: Server-Sent Events (SSE).
  - `GET /sse`: Clients initiate an SSE stream. The server generates a unique `session_id` and emits an `endpoint` event pointing to `/messages?session_id=<UUID>`.
  - `POST /messages?session_id=<UUID>`: Clients send standard JSON-RPC 2.0 frames (`initialize`, `tools/list`, `tools/call`, `ping`). Responses are pushed back over the persistent SSE stream.
- **Tools Registered**:
  - `context_save(title, content, tags, project)`: Embeds and persists context chunks.
  - `context_search(query, project, limit, threshold)`: Computes query vector and executes cosine similarity search.
  - `context_get(context_id)`: Fetches complete document by UUID.
  - `context_list(project, limit)`: Paginated lookup of stored knowledge.
  - `context_delete(context_id)`: Deletes outdated or invalid context entries.

### 2.2 Embedding Engine (`src/embeddings.py`)
- **Model**: `BAAI/bge-small-en-v1.5` via `fastembed`.
- **Runtime**: ONNX Runtime executing on local CPU with multithreading.
- **Characteristics**:
  - Vector Dimension: 384 floats.
  - Memory Footprint: ~130 MB RAM.
  - Latency: ~8-15 ms per 512 tokens on typical modern desktop CPUs.
  - No external API keys or network latency required.

### 2.3 Storage & Vector Search (`src/storage.py`)
- **Database**: PostgreSQL 16 with `pgvector` extension.
- **Indexing**: Hierarchical Navigable Small World (HNSW).
  ```sql
  CREATE INDEX idx_contexts_embedding_hnsw 
  ON contexts 
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```
- **Similarity Metric**: Cosine Distance (`<=>`), returning `1 - (embedding <=> query_vector)` as similarity score.

### 2.4 Autonomous Auto-Sync Daemon (`scripts/auto-sync-daemon.py`)
The daemon bridges static project rules with dynamic agent activity:
1. **Workspace Discovery**: Discovers open and recent workspaces across Cursor, VS Code, JetBrains, Codex CLI, and Antigravity.
2. **Session History Parsing**:
   - Codex: Inspects `~/.codex/state_5.sqlite` and `~/.codex/thread_history_1.sqlite`.
   - Antigravity: Inspects `~/.gemini/antigravity/brain/*/transcript.jsonl`.
3. **Digest Synthesis**: Formats the latest cross-agent achievements, pending tasks, and architecture decisions into a markdown summary.
4. **Non-Destructive Marker Injection**: Updates `AGENTS.md` and `.cursorrules` inside matching project directories between `<!-- CONTEXT-SYNC-START -->` and `<!-- CONTEXT-SYNC-END -->` without overwriting custom prompt instructions.

### 2.5 Fact-Level Conflict Resolution (FLCR) Engine (`src/facts.py`)
Standard document stores suffer from catastrophic knowledge drift when independent agents modify isolated parameters within larger documents. FLCR introduces atomic fact primitives:
- **Atomic Triplet**: Every project invariant is stored as `(project, entity, attribute) -> value` with a strictly monotonically increasing `version` counter and boolean `is_active` state.
- **Conflict Resolution Strategies**:
  - **LWW (Last-Write-Wins with Audit Trail)**: Active facts are safely transitioned to `is_active=False` with a pointer to `superseded_by`, creating a permanent lineage graph of configuration evolution.
  - **Authority Hierarchy**: Sources carry defined authority weights (`user: 100`, `architect: 80`, `agent: 50`, `worker: 10`). Changes from subordinate agents cannot overwrite human decisions without explicit manual verification, raising `conflict_flag = True`.
- **Truth-Table Injection**: Active facts are automatically compiled into a clean Markdown table and injected into the dynamic section of `AGENTS.md` and `CLAUDE.md`.

---


## 3. Security and Authentication Model

- **Token-Based Bearer Authentication**:
  All REST endpoints and SSE handshakes accept an API token:
  - Query parameter: `?token=<API_TOKEN>` (essential for browser-based EventSource and MCP SSE clients).
  - Header: `Authorization: Bearer <API_TOKEN>`.
- **Network Perimeter**:
  - Default bind: `0.0.0.0:8000` (container internal).
  - Exposed port: Host `8000`.
  - Recommended for remote multi-machine access: Cloudflare Tunnel, Tailscale Funnel, or Caddy reverse proxy with Let's Encrypt TLS.