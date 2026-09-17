# AI Agents Configuration & Connection Guide

This guide covers step-by-step instructions for connecting all major AI coding assistants to the **Remote Context Synchronization Server**.

---

## 1. Quick Reference: Connection Strings

| Parameter | Localhost | Remote / Tunnel |
|---|---|---|
| **SSE URL** | `http://localhost:8000/sse?token=YOUR_TOKEN` | `https://your-domain.com/sse?token=YOUR_TOKEN` |
| **REST Base URL** | `http://localhost:8000/api/v1` | `https://your-domain.com/api/v1` |
| **Stdio Bridge Command** | `cmd.exe /c npx -y mcp-remote <SSE_URL>` | `npx -y mcp-remote <SSE_URL>` |

---

## 2. Google Antigravity

Antigravity natively supports remote MCP servers with lazy loading.

1. Open Antigravity Settings or edit your global configuration file:
   - Path: `~/.gemini/antigravity/antigravity.json` or workspace `.antigravity/mcp.json`.
2. Add the `remote-context` server entry:
   ```json
   {
     "mcpServers": {
       "remote-context": {
         "url": "http://localhost:8000/sse?token=ctx_secret_token_7f9a8b1c4e2d3f5a",
         "transport": "sse"
       }
     }
   }
   ```
3. Restart Antigravity or trigger the reload MCP command.
4. Verify by checking tools in your prompt: `context_search`, `context_save`, `context_list`.

---

## 3. Cursor

Cursor supports MCP servers over Server-Sent Events (SSE) natively.

1. Open **Cursor Settings** (`Ctrl + ,` or `Cmd + ,`).
2. Navigate to **Features** -> **MCP Servers**.
3. Click **Add New MCP Server**.
4. Configure the server:
   - **Name**: `remote-context`
   - **Type**: `sse`
   - **URL**: `http://localhost:8000/sse?token=ctx_secret_token_7f9a8b1c4e2d3f5a`
5. Click **Save** and verify that the green status indicator lights up.
6. The tools are immediately available to Cursor Composer and Chat.

---

## 4. Claude Desktop

Claude Desktop currently requires an stdio-to-SSE adapter (`mcp-remote`) to attach custom authentication headers and handle SSE streams.

### Windows Configuration
Edit `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "remote-context": {
      "command": "cmd.exe",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-remote",
        "http://localhost:8000/sse?token=ctx_secret_token_7f9a8b1c4e2d3f5a",
        "--allow-http"
      ]
    }
  }
}
```

### macOS / Linux Configuration
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "remote-context": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8000/sse?token=ctx_secret_token_7f9a8b1c4e2d3f5a",
        "--allow-http"
      ]
    }
  }
}
```

---

## 5. OpenAI Codex CLI & Multi-Account Setup

The OpenAI Codex CLI does not use MCP directly; instead, Remote Context tracks Codex sessions via its SQLite databases and synchronizes context through `AGENTS.md`.

### Multi-Account Codex Setup
If you operate multiple Codex accounts on the same machine:
1. Each Codex account shares the configuration root at `~/.codex/`.
2. Active sessions and threads are stored in:
   - `~/.codex/state_5.sqlite` (contains `threads`, `projects`, and session metadata).
   - `~/.codex/thread_history_1.sqlite` (contains conversation history items).
3. The Auto-Sync Daemon automatically inspects both databases, matches active threads to projects, and updates project knowledge rules.
4. When switching accounts, Codex maintains thread history in the local database, which Remote Context continuously indexes.

---

## 6. Troubleshooting Common MCP Errors

### 1. "Method Not Allowed" (405)
- **Cause**: The agent is attempting to send a raw `POST` request directly to the `/sse` endpoint, or is misinterpreting the endpoint URL.
- **Solution**:
  - Verify that the URL is configured as `http://localhost:8000/sse?token=...`.
  - For Claude Desktop, do not use `"type": "sse"` directly; use the `mcp-remote` command wrapper.

### 2. "SSE Connection Timeout" or "ECONNREFUSED"
- **Cause**: Docker container is stopped or port 8000 is occupied.
- **Solution**:
  - Run `docker compose ps` to verify `context-sync-app` is running.
  - Check container logs: `docker compose logs -f app`.