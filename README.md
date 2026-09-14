<div align="center">

# 🧠 Context Sync
### Universal Neural Memory & Context Synchronization Fabric for AI Coding Agents

[![CI](https://github.com/scanner72/context-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/scanner72/context-sync/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169E1.svg?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![MCP Protocol](https://img.shields.io/badge/MCP%20Protocol-2024--11--05-8A2BE2.svg?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/Tests-23%2F23%20Passed-brightgreen.svg)]()

**[English](README.md)** • **[Русский](README.ru.md)** • **[Architecture](docs/architecture.md)** • **[Agent Setup](docs/agents-setup.md)** • **[Auto-Sync](docs/auto-sync.md)** • **[API Reference](docs/api-reference.md)**

<p align="center">
  <b>Context Sync</b> unites fragmented AI coding assistants into a single, cohesive team.<br/>
  Cursor, Claude Desktop, Claude Code, OpenAI Codex, Antigravity, Windsurf, and Cline share a continuous neural knowledge base across all your machines.
</p>

---

</div>

## 🌟 Why Context Sync?

Modern software engineering involves multiple AI tools across several machines: **Cursor** on your desktop, **Claude Desktop** on your laptop, **OpenAI Codex CLI** on your build server, and **Claude Code** in your terminal. 

Today, these agents are **siloed and amnesic**:
- A bug analyzed and resolved in Cursor in the morning has to be re-explained to Claude Desktop in the afternoon.
- Architecture decisions made on your laptop never reach your home desktop.
- Multiple agents overwrite project rule files or work from stale assumptions.

**Context Sync fixes this permanently.** It provides a centralized, ultra-fast **Model Context Protocol (MCP)** memory server powered by **PostgreSQL 16 + pgvector** and **FastEmbed ONNX**, backed by an autonomous background sync daemon that extracts chat decisions and keeps `CLAUDE.md`, `AGENTS.md`, and `.cursorrules` updated with **zero manual prompts**.

---

## ⚡ Feature Matrix & Comparison

| Capability | Context Sync | Mem0 / Zep | Raw Vector DB (Chroma/Pinecone) | Single-Agent Memory |
|:---|:---:|:---:|:---:|:---:|
| **Native MCP Protocol (SSE + stdio)** | **✅ Native** | ❌ HTTP only | ❌ DB client only | ❌ Isolated |
| **Multi-Agent Fleet Support (8+ IDEs)** | **✅ Out of the box** | ⚠️ Custom code | ❌ Manual | ❌ Single tool |
| **Autonomous Background Chat Sync** | **✅ Continuous daemon** | ❌ Manual push | ❌ Manual push | ❌ Local only |
| **Automatic Project Context Injection** (`CLAUDE.md`, `.cursorrules`, `AGENTS.md`) | **✅ Non-destructive** | ❌ No | ❌ No | ⚠️ Static rules |
| **1-Click Agent Auto-Discovery & Injector** | **✅ Windows / macOS / Linux** | ❌ Manual | ❌ Manual | ❌ No |
| **Zero-Cost Local CPU Embeddings** | **✅ FastEmbed ONNX** | ⚠️ Paid API required | ⚠️ External API | ❌ No |
| **Real-time Live Fleet Web Dashboard** | **✅ Bilingual (EN / RU)** | ⚠️ Cloud UI | ⚠️ Raw DB admin | ❌ No |
| **Multi-Account Thread Resolution** | **✅ Supported (Codex)** | ❌ No | ❌ No | ❌ No |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph ClientDevices [" Developer Workstations & Laptops "]
        Cursor[" Cursor IDE "]
        ClaudeDesk[" Claude Desktop "]
        ClaudeCode[" Claude Code CLI "]
        Codex[" OpenAI Codex "]
        AntiG[" Google Antigravity "]
        Cline[" Cline / Roo Code "]
    end

    subgraph AutoSyncDaemon [" Autonomous Background Sync Daemon "]
        CodexCol["Codex Collector (SQLite)"]
        CursorCol["Cursor Collector (vscdb)"]
        ClaudeCol["Claude Collector (Logs)"]
        DigestEng["Digest Engine (Non-Destructive)"]
    end

    subgraph Server [" Context Sync Core Platform (Port 8200) "]
        FastAPI[" FastAPI Core & Auth Middleware "]
        MCPEndpoint[" MCP Server (Stream over HTTP / SSE) "]
        RESTEndpoint[" REST API & Web Dashboard "]
        FastEmbed[" FastEmbed Engine (ONNX CPU, 384-dim) "]
        FleetTrack[" Live Fleet Session Tracker "]
    end

    subgraph Storage [" Persistent Database Layer (Port 5445) "]
        PGVector[(" PostgreSQL 16 + pgvector ")]
        HNSW[" HNSW Cosine Index "]
        GIN[" GIN Tags & Full-Text Index "]
    end

    subgraph LocalProjects [" Local Project Repositories "]
        RuleFiles[" CLAUDE.md • AGENTS.md • .cursorrules "]
    end

    Cursor -->|SSE / Bearer Auth| MCPEndpoint
    ClaudeDesk -->|mcp-remote stdio| MCPEndpoint
    ClaudeCode -->|SSE / Bearer Auth| MCPEndpoint
    AntiG -->|SSE / Bearer Auth| MCPEndpoint
    Cline -->|SSE / Bearer Auth| MCPEndpoint

    MCPEndpoint <--> FastAPI
    RESTEndpoint <--> FastAPI
    FastAPI <--> FleetTrack
    FastAPI <--> FastEmbed
    FastAPI <--> PGVector
    PGVector --- HNSW
    PGVector --- GIN

    ClientDevices -.->|Chat history & state| AutoSyncDaemon
    CodexCol --> DigestEng
    CursorCol --> DigestEng
    ClaudeCol --> DigestEng
    DigestEng -->|Ingest new sessions| RESTEndpoint
    DigestEng -->|Auto-update| LocalProjects
```

---

## 🤖 Supported AI Coding Agents

Context Sync includes built-in auto-discovery, 1-click configuration injection, and conversation history collectors:

| Agent / Editor | Transport | macOS Path | Linux Path | Windows Path | Status |
|:---|:---:|:---|:---|:---|:---:|
| **Claude Desktop** | `stdio` | `~/Library/Application Support/Claude/claude_desktop_config.json` | `~/.config/Claude/claude_desktop_config.json` | `%APPDATA%\Claude\claude_desktop_config.json` | 🟢 Supported |
| **Claude Code CLI** | `SSE` | `~/.claude.json` | `~/.claude.json` | `%USERPROFILE%\.claude.json` | 🟢 Supported |
| **Cursor IDE** | `SSE` | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` | `%USERPROFILE%\.cursor\mcp.json` | 🟢 Supported |
| **OpenAI Codex** | `TOML` | `~/.codex/config.toml` | `~/.codex/config.toml` | `%USERPROFILE%\.codex\config.toml` | 🟢 Supported |
| **Google Antigravity** | `SSE` | `~/.gemini/antigravity/mcp_config.json` | `~/.gemini/antigravity/mcp_config.json` | `%USERPROFILE%\.gemini\antigravity\mcp_config.json` | 🟢 Supported |
| **Windsurf IDE** | `SSE` | `~/.codeium/windsurf/mcp_config.json` | `~/.codeium/windsurf/mcp_config.json` | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` | 🟢 Supported |
| **Cline (VS Code)** | `SSE` | `~/Library/Application Support/Code/User/...` | `~/.config/Code/User/...` | `%APPDATA%\Code\User\...` | 🟢 Supported |
| **Roo Code (VS Code)** | `SSE` | `~/Library/Application Support/Code/User/...` | `~/.config/Code/User/...` | `%APPDATA%\Code\User\...` | 🟢 Supported |

---

## 🌐 Universal Cross-Platform Architecture

Context Sync is engineered for 100% native execution across **macOS**, **Linux**, and **Windows**:

| Component / Capability | 🍏 macOS (Apple Silicon M1–M4 & Intel) | 🐧 Linux (Ubuntu, Debian, Fedora, Arch) | 🪟 Windows (10, 11, WSL2) |
|:---|:---|:---|:---|
| **Server & Container** | Docker Desktop (Native `arm64` / `amd64`) | Docker Engine 24+ & Docker Compose | Docker Desktop / WSL2 |
| **Vector Embedding Engine** | FastEmbed (Native ONNX CPU `arm64`) | FastEmbed (Native ONNX CPU `amd64`) | FastEmbed (Native ONNX CPU x64) |
| **Database & Vectors** | PostgreSQL 16 + pgvector | PostgreSQL 16 + pgvector | PostgreSQL 16 + pgvector |
| **1-Click Agent Connect** | `./connect-agents.sh` | `./connect-agents.sh` | `.\connect-agents.ps1` or `.bat` |
| **Autonomous Background Sync** | `./start-auto-sync.sh` | `./start-auto-sync.sh` | `.\start-auto-sync.ps1` or `.bat` |
| **Remote Deploy & Sync** | `./deploy-remote.sh`, `./sync-to-remote.sh` | `./deploy-remote.sh`, `./sync-to-remote.sh` | `.\deploy-remote.ps1`, `.\sync-to-remote.ps1` |
| **File Normalization** | Native POSIX (`/`) | Native POSIX (`/`) | Auto-normalized (`\` -> `/`) |

---

## 🚀 Quick Start in 60 Seconds

### 1. Launch with Docker Compose
Clone the repository and start the services:
```bash
git clone https://github.com/scanner72/context-sync.git
cd context-sync

# Copy environment file
cp .env.example .env

# Start containers (Runs on non-conflicting ports 8200 & 5445)
docker compose up -d --build
```

The Web Dashboard is now live at **`http://localhost:8200`** (or `http://localhost:8000` if configured).

### 2. Auto-Connect All Local Agents
Run the native auto-connect script for your OS:
- **macOS & Linux**:
  ```bash
  ./connect-agents.sh
  # Or targeting a remote server:
  ./connect-agents.sh http://10.10.10.11:8200/sse <YOUR_AUTH_TOKEN>
  ```
- **Windows (PowerShell)**:
  ```powershell
  .\connect-agents.ps1
  # Or targeting a remote server:
  .\connect-agents.ps1 -Url "http://10.10.10.11:8200/sse" -Token "<YOUR_AUTH_TOKEN>"
  ```
- **Or via Web UI**: Open `http://localhost:8200` ➔ Go to **"Fleet & Scanner"** ➔ Click **"Find & Connect Agents"**.

### 3. Launch Autonomous Auto-Sync Daemon
Keep project memory and `.cursorrules` / `CLAUDE.md` automatically synchronized across all running agents:
- **macOS & Linux**:
  ```bash
  ./start-auto-sync.sh
  ```
- **Windows**:
  ```powershell
  .\start-auto-sync.ps1
  ```

---

## 🛠️ Model Context Protocol (MCP) Tools

Once connected, your AI agents have access to 5 native tools:

### 1. `context_search`
Perform high-speed hybrid vector and keyword search across your team memory:
```json
{
  "name": "context_search",
  "arguments": {
    "query": "How is PostgreSQL connection pooling configured?",
    "limit": 5,
    "project": "context_sync",
    "tags": ["database", "backend"]
  }
}
```

### 2. `context_save`
Save an architectural decision, solution, or bug investigation:
```json
{
  "name": "context_save",
  "arguments": {
    "title": "Port conflict resolution on remote deployment",
    "content": "Mapped Web UI to 8200 and PostgreSQL to 5445 to avoid Portainer collision.",
    "tags": ["docker", "devops"],
    "project": "context_sync"
  }
}
```

### 3. `context_get`
Retrieve a document by UUID.

### 4. `context_list`
List recent context documents with project, tag, or time filters.

### 5. `context_delete`
Safely remove outdated or superseded knowledge items.

---

## ⚡ Fact-Level Conflict Resolution (FLCR)

ContextSync prevents knowledge drift by maintaining an atomic, version-controlled **Fact Truth-Table** across all AI agents:

* **Atomic Triplets (`Entity -> Attribute -> Value`)**: Instead of overwriting entire documents, agents can register precise parameters (e.g. `backend.port=8200`, `database.engine=postgresql`).
* **Conflict Policies**:
  * `LWW (Last-Write-Wins)`: Increments versioning (`v1 -> v2`) while keeping a complete audit trail (`fact_history`) and explicit links to superseded facts (`superseded_by`).
  * `Authority Policy`: Prioritizes sources (`User/Human (100)` > `Architect/Lead (80)` > `Agent (50)` > `Worker (10)`). Changes from lower-ranked agents cannot overwrite human decisions and are flagged (`conflict_flag = True`) for review.
* **Auto Truth-Table Injection**: Active facts are automatically rendered as clean Markdown tables in `AGENTS.md` and `CLAUDE.md`.

### Dedicated MCP Fact Tools:
* `fact_set`: Store or update an atomic fact with configurable conflict policy (`lww` or `authority`).
* `fact_get`: Fetch current active value for any entity and attribute.
* `fact_list`: Retrieve the complete active Truth-Table for a project.
* `fact_history`: Inspect the full version audit trail and resolved conflicts.

---

## 🌐 Live Fleet & Web Dashboard

Open `http://localhost:8200` to access the real-time management dashboard:
- **Bilingual Interface**: Instant **EN / RU** toggle with zero page reloads.
- **Live Fleet Tracker**: See all active MCP sessions across your laptops, their IP addresses, user-agents, and last tool calls in real time.
- **Interactive Knowledge Explorer**: Semantic search with similarity score sliders, tag badges, and rich Markdown previews.
- **Context Editor**: Create, edit, and categorize memory entries with instant Markdown preview.
- **Auto-Sync Status**: Real-time inspection of active projects, sync intervals, and last cycle metrics.

---

## 💻 Remote Server Deployment

Context Sync is designed to run seamlessly on remote VPS or home lab servers (e.g. `10.10.10.11`):
- **Port Conflict Protection**: Default configuration uses port `8200` for the Web/MCP app and `5445` for PostgreSQL, ensuring no clashes with Portainer, standard PostgreSQL, or web servers.
- **Instant Deployment**:
  ```powershell
  .\deploy-remote.ps1 -RemoteHost "10.10.10.11" -RemoteUser "energetik" -AppPort 8200 -PostgresPort 5445
  ```
- **Rapid Development Sync**:
  ```powershell
  .\sync-to-remote.ps1
  ```

---

## 🧪 Testing & Verification

Context Sync maintains a comprehensive test suite covering FastEmbed vectors, FLCR versioning, skills replication, MCP fleet hub injection, MCP JSON-RPC handlers, fleet tracking, scanner injection, and auto-sync collectors:

```bash
python -m pytest tests/ -v
============================== 32 passed in 2.70s ==============================
```

---

## 📚 Documentation

Detailed guides and technical references are available in the [`docs/`](docs/) directory:
- **[REST & MCP API Reference](docs/api-reference.md)** ([Русская версия](docs/api-reference.ru.md)): Complete schema for all endpoints, FLCR tools, Skills API, MCP Registry, and JSON-RPC methods.
- **[Architecture & System Design](docs/architecture.md)** ([Русская версия](docs/architecture.ru.md)): Deep dive into pgvector HNSW indexing, FLCR mechanics, and FastEmbed local inference.
- **[Agent Setup Guide](docs/agents-setup.md)**: Step-by-step instructions for Cursor, Claude Desktop, Claude Code, OpenAI Codex, and Antigravity.
- **[Auto-Sync Daemon Guide](docs/auto-sync.md)**: Details on background workspace discovery and safe rules injection.

---

## 🗺️ Roadmap

### 🟢 Completed (v0.1.0 – v0.3.0)
- [x] Full FastMCP SSE (Server-Sent Events) transport with Bearer token authentication.
- [x] Vector semantic memory powered by PostgreSQL 16 + pgvector (HNSW) and FastEmbed CPU.
- [x] Bilingual Web Dashboard (EN / RU) and real-time Live Fleet Tracker.
- [x] Autonomous background sync daemon for `AGENTS.md`, `CLAUDE.md`, and `.cursorrules`.
- [x] **Fact-Level Conflict Resolution (FLCR)**: atomic fact versioning (`v1 -> v2`), LWW & Authority Hierarchy policies, `fact_*` MCP tools.
- [x] **Cross-Agent Skills Replication (Skills Sync)**:
  - Unified Canonical Skill schema (`CanonicalSkill`: `SKILL.md` + scripts + templates).
  - Bidirectional adapters between **Antigravity**, **Cursor IDE**, **Claude Code**, **OpenAI Codex**, and **Windsurf**.
  - Agent MCP tools: `skill_publish`, `skill_list`, `skill_get`, `skill_install(target_agent)`.
- [x] **Centralized MCP Fleet Registry (MCP Hub)**:
  - Central repository of validated MCP server configurations in PostgreSQL.
  - 1-Click propagation of any MCP server across all installed local/remote agents (`mcp_server_install`).

### 🟡 Planned (v0.4.0)
- [ ] Visual Skill Designer and prompt editor in the Web Dashboard.
- [ ] Semantic duplicate detection for published skills.


---

## 🤝 Contributing



Contributions are warmly welcome! Please see **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed development guidelines, code standards, and PR workflows.

1. Fork the Project (`https://github.com/scanner72/context-sync/fork`)
2. Create your Feature Branch (`git checkout -b feature/amazing-agent`)
3. Commit your Changes (`git commit -m 'feat: add adapter for NewAgent'`)
4. Push to the Branch (`git push origin feature/amazing-agent`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See **[LICENSE](LICENSE)** for more information.

<div align="center">
  <sub>Built with ❤️ by AI Engineers for the global agentic coding community.</sub>
</div>