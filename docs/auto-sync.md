# Autonomous Multi-Agent Synchronization Daemon

The Auto-Sync Daemon provides completely hands-free, autonomous context sharing across all AI agents working on your machine or across your team.

---

## 1. The Core Problem It Solves

When working across multiple AI assistants (e.g. brainstorming in Claude Desktop, coding in Cursor, terminal tasks in Codex CLI, and deep refactoring in Antigravity):
- Context is fragmented across isolated apps.
- Developers are forced to manually copy-paste prompt instructions, architecture decisions, and task progress.
- Agent rule files (`AGENTS.md`, `.cursorrules`, `CLAUDE.md`) quickly become outdated.

**The Auto-Sync Daemon eliminates manual prompts by automatically maintaining a live synchronization digest in every active project workspace.**

---

## 2. How the Daemon Works

```
Every 90s:
1. Scan Active Workspaces (Cursor, VS Code, JetBrains, Codex, Antigravity)
2. Extract Recent Agent Actions:
   - Codex SQLite: Recent threads & commands
   - Antigravity: Recent conversation transcripts
   - Remote Context DB: Newest decisions saved by any agent
3. Generate Unified Context Digest:
   - Current project status
   - Decisions made by other agents in the last 24h
   - Live fleet activity
4. Non-Destructive Update:
   - Write/Update `AGENTS.md` & `.cursorrules` in each workspace
   - Preserve all existing user rules outside sync markers!
```

---

## 3. Safe Marker Injection Format

The daemon injects a clearly delimited block into project rule files:

```markdown
<!-- CONTEXT-SYNC-START -->
## 🔄 Multi-Agent Sync (ContextSync)
> 🕒 Synchronized: **2026-09-11 14:30** | 🤖 Fleet: **Codex CLI, Cursor, Antigravity**

### 📌 Recent Actions from Other Agents:
- **Codex CLI** (11 Sep, 14:25): Implemented PostgreSQL HNSW vector search indexing
- **Cursor** (11 Sep, 14:15): Added multilingual i18n support to Web UI dashboard

### 🧠 Central Project Memory:
- Search shared knowledge: call `context_search(query="...")`
- Save architectural decisions: call `context_save(title="...", content="...")`
- Web Dashboard: [http://localhost:8000](http://localhost:8000)
<!-- CONTEXT-SYNC-END -->
```

> [!IMPORTANT]
> Everything outside `<!-- CONTEXT-SYNC-START -->` and `<!-- CONTEXT-SYNC-END -->` is strictly preserved. Your custom coding standards, system prompts, and formatting rules are never touched or modified.

---

## 4. Running the Daemon

### Option A: Windows PowerShell Script
Run the background sync helper script:
```powershell
.\start-auto-sync.ps1 -IntervalSeconds 90
```

### Option B: Direct Python Execution
```bash
python scripts/auto-sync-daemon.py --interval 90
```

### Option C: Run in Headless / Daemon Mode
To keep the daemon running continuously in the background on Windows:
```powershell
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "scripts/auto-sync-daemon.py --interval 90"
```