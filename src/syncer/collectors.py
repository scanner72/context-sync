"""Collectors for extracting chat sessions and workspace context from AI agents."""

import os
import sys
import glob
import json
import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProjectSession:
    agent: str                  # "codex", "cursor", "claude", "antigravity"
    project_name: str           # e.g. "context_sync", "monitoring", "goldv2"
    project_path: Optional[str] # Absolute path to project root
    session_id: str             # Unique thread or conversation UUID
    title: str                  # Subject or first user prompt
    updated_at_ms: int          # Epoch millisecond of last update
    messages: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""           # Cleaned markdown excerpt / decisions summary


def _clean_project_name(raw_path: Optional[str], default_name: str = "global") -> str:
    """Extract clean folder name from path or URI."""
    if not raw_path:
        return default_name
    cleaned = raw_path.replace("\\\\?\\", "").replace("file:///", "").replace("file://", "").strip()
    cleaned = cleaned.replace("%3A", ":").replace("%20", " ")
    cleaned = cleaned.replace("\\", "/")
    norm = Path(cleaned)
    name = norm.name or default_name
    return name.lower()


class CodexCollector:
    """Reads projects and conversations from OpenAI Codex SQLite databases and session logs."""

    def __init__(self, codex_home: Optional[Path] = None):
        self.home = codex_home or (Path.home() / ".codex")
        self.state_db = self.home / "state_5.sqlite"
        self.history_db = self.home / "thread_history_1.sqlite"
        self.sessions_dir = self.home / "sessions"

    def is_available(self) -> bool:
        return self.state_db.exists() or self.history_db.exists()

    def get_known_projects(self) -> Dict[str, str]:
        """Return dict of {project_id: absolute_path}."""
        projects = {}
        if not self.state_db.exists():
            return projects

        try:
            con = sqlite3.connect(f"file:{self.state_db}?mode=ro", uri=True)
            cur = con.cursor()
            cur.execute("SELECT project_id, path FROM project_roots")
            for pid, path in cur.fetchall():
                clean_path = path.replace("\\\\?\\", "")
                projects[pid] = clean_path
            con.close()
        except Exception as e:
            logger.warning(f"CodexCollector: error reading project_roots: {e}")
        return projects

    def collect_sessions(self, since_ms: int = 0) -> List[ProjectSession]:
        """Collect updated thread sessions since given timestamp."""
        sessions: List[ProjectSession] = []
        if not self.state_db.exists():
            return sessions

        project_roots = self.get_known_projects()

        try:
            con = sqlite3.connect(f"file:{self.state_db}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            query = """
                SELECT id, rollout_path, cwd, title, first_user_message,
                       created_at_ms, updated_at_ms, project_id
                FROM threads
                WHERE updated_at_ms >= ?
                ORDER BY updated_at_ms DESC
            """
            cur.execute(query, (since_ms,))
            thread_rows = cur.fetchall()
            con.close()
        except Exception as e:
            logger.warning(f"CodexCollector: error querying threads: {e}")
            return sessions

        for row in thread_rows:
            thread_id = row["id"]
            updated_at = row["updated_at_ms"] or 0
            cwd = (row["cwd"] or "").replace("\\\\?\\", "")
            pid = row["project_id"]
            proj_path = cwd or project_roots.get(pid)
            proj_name = _clean_project_name(proj_path)

            title = row["title"] or row["first_user_message"] or f"Codex Thread {thread_id[:8]}"
            messages = self._load_thread_messages(thread_id, row["rollout_path"])

            summary = self._build_session_summary("Codex", title, proj_name, messages)

            sessions.append(
                ProjectSession(
                    agent="codex",
                    project_name=proj_name,
                    project_path=proj_path,
                    session_id=thread_id,
                    title=title,
                    updated_at_ms=updated_at,
                    messages=messages,
                    summary=summary,
                )
            )

        return sessions

    def _load_thread_messages(self, thread_id: str, rollout_path: Optional[str]) -> List[Dict[str, Any]]:
        """Load messages from thread_history_1.sqlite or rollout JSONL."""
        messages: List[Dict[str, Any]] = []

        # 1. Try SQLite thread_items
        if self.history_db.exists():
            try:
                con = sqlite3.connect(f"file:{self.history_db}?mode=ro", uri=True)
                cur = con.cursor()
                cur.execute(
                    "SELECT item_type, item_json, created_at_ms FROM thread_items WHERE thread_id = ? ORDER BY rollout_ordinal ASC",
                    (thread_id,)
                )
                rows = cur.fetchall()
                con.close()

                if rows:
                    for item_type, item_json, created_ms in rows:
                        try:
                            data = json.loads(item_json)
                            if item_type == "userMessage":
                                text = ""
                                content = data.get("content")
                                if isinstance(content, list):
                                    text = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                                elif isinstance(content, str):
                                    text = content
                                if text.strip():
                                    messages.append({
                                        "role": "user",
                                        "text": text.strip(),
                                        "timestamp": created_ms,
                                    })
                            elif item_type == "agentMessage":
                                text = data.get("text") or ""
                                if text.strip() and not text.startswith("[external_agent_tool_result]"):
                                    messages.append({
                                        "role": "assistant",
                                        "text": text.strip(),
                                        "timestamp": created_ms,
                                    })
                        except Exception:
                            continue
                    return messages
            except Exception as e:
                logger.debug(f"Failed to read thread_items for {thread_id}: {e}")

        # 2. Fallback to rollout_path JSONL
        if rollout_path and os.path.exists(rollout_path):
            try:
                with open(rollout_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            item = json.loads(line)
                            payload = item.get("payload", {})
                            ptype = item.get("type") or payload.get("type")
                            if ptype == "userMessage":
                                content = payload.get("content", [])
                                text = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                                if text.strip():
                                    messages.append({"role": "user", "text": text.strip()})
                            elif ptype == "agentMessage":
                                text = payload.get("text") or ""
                                if text.strip():
                                    messages.append({"role": "assistant", "text": text.strip()})
                        except Exception:
                            continue
            except Exception as e:
                logger.debug(f"Failed to read rollout JSONL {rollout_path}: {e}")

        return messages

    def _build_session_summary(self, agent_name: str, title: str, project_name: str, messages: List[Dict[str, Any]]) -> str:
        """Create a compact LLM-ready markdown excerpt of the conversation."""
        lines = [f"### [{agent_name}] Проект: {project_name} — {title}"]
        user_turns = [m for m in messages if m["role"] == "user"]
        asst_turns = [m for m in messages if m["role"] == "assistant"]

        if user_turns:
            lines.append(f"**Запрос / Цель**: {user_turns[0]['text'][:300]}")
        if asst_turns:
            # Last turn often has the final conclusion or summary
            last_msg = asst_turns[-1]["text"][:600]
            lines.append(f"**Итог / Решение**: {last_msg}")

        return "\n".join(lines)


class CursorCollector:
    """Reads workspaces and chat history from Cursor IDE."""

    def __init__(self):
        is_mac = sys.platform == "darwin"
        is_win = sys.platform.startswith("win")
        if is_mac:
            appdata = Path.home() / "Library" / "Application Support"
        elif is_win:
            appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            appdata = Path.home() / ".config"

        self.workspace_storage = appdata / "Cursor" / "User" / "workspaceStorage"
        self.global_storage = appdata / "Cursor" / "User" / "globalStorage"

    def is_available(self) -> bool:
        return self.workspace_storage.exists()

    def get_known_workspaces(self) -> Dict[str, str]:
        """Find mapping of workspace_hash -> absolute project folder."""
        workspaces = {}
        if not self.workspace_storage.exists():
            return workspaces

        for wdir in self.workspace_storage.iterdir():
            if not wdir.is_dir():
                continue
            wjson = wdir / "workspace.json"
            if wjson.exists():
                try:
                    data = json.loads(wjson.read_text(encoding="utf-8"))
                    folder_uri = data.get("folder")
                    if folder_uri:
                        clean = folder_uri.replace("file:///", "").replace("file://", "").replace("%3A", ":").replace("%20", " ")
                        workspaces[wdir.name] = clean
                except Exception:
                    continue
        return workspaces

    def collect_sessions(self, since_ms: int = 0) -> List[ProjectSession]:
        """Collect sessions from Cursor workspace databases."""
        sessions: List[ProjectSession] = []
        workspaces = self.get_known_workspaces()

        for whash, proj_path in workspaces.items():
            db_path = self.workspace_storage / whash / "state.vscdb"
            if not db_path.exists():
                continue

            try:
                mod_time_ms = int(db_path.stat().st_mtime * 1000)
                if mod_time_ms < since_ms:
                    continue

                con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                cur = con.cursor()
                cur.execute(
                    "SELECT key, value FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%composer%' LIMIT 10"
                )
                rows = cur.fetchall()
                con.close()

                proj_name = _clean_project_name(proj_path)
                messages = []

                for key, val in rows:
                    if not val:
                        continue
                    try:
                        data = json.loads(val)
                        if isinstance(data, dict):
                            text = str(data.get("text") or data.get("prompt") or "")
                            if text:
                                messages.append({"role": "user", "text": text[:300]})
                    except Exception:
                        pass

                if messages:
                    sessions.append(
                        ProjectSession(
                            agent="cursor",
                            project_name=proj_name,
                            project_path=proj_path,
                            session_id=f"cursor-{whash[:8]}",
                            title=f"Cursor Workspace: {proj_name}",
                            updated_at_ms=mod_time_ms,
                            messages=messages,
                            summary=f"### [Cursor] Проект: {proj_name}\nНедавняя работа в Cursor IDE над кодом проекта.",
                        )
                    )
            except Exception as e:
                logger.debug(f"CursorCollector error reading {whash}: {e}")

        return sessions


class ClaudeCollector:
    """Reads projects and sessions from Claude Code CLI and Claude Desktop."""

    def __init__(self):
        self.home = Path.home()
        self.claude_json = self.home / ".claude.json"
        is_mac = sys.platform == "darwin"
        is_win = sys.platform.startswith("win")

        if is_mac:
            self.desktop_dir = self.home / "Library" / "Application Support" / "Claude"
        elif is_win:
            local_app_data = Path(os.environ.get("LOCALAPPDATA", self.home / "AppData" / "Local"))
            packages = glob.glob(str(local_app_data / "Packages" / "Claude_*" / "LocalCache" / "Roaming" / "Claude"))
            std_dir = Path(os.environ.get("APPDATA", self.home / "AppData" / "Roaming")) / "Claude"
            self.desktop_dir = Path(packages[0]) if packages else std_dir
        else:
            self.desktop_dir = self.home / ".config" / "Claude"

    def is_available(self) -> bool:
        return self.claude_json.exists() or (self.desktop_dir is not None and self.desktop_dir.exists())

    def collect_sessions(self, since_ms: int = 0) -> List[ProjectSession]:
        sessions: List[ProjectSession] = []

        # Claude Code CLI
        if self.claude_json.exists():
            try:
                mod_time = int(self.claude_json.stat().st_mtime * 1000)
                if mod_time >= since_ms:
                    data = json.loads(self.claude_json.read_text(encoding="utf-8"))
                    projects = data.get("projects", {})
                    for p_path, p_info in projects.items():
                        p_name = _clean_project_name(p_path)
                        sessions.append(
                            ProjectSession(
                                agent="claude-code",
                                project_name=p_name,
                                project_path=p_path,
                                session_id=f"claude-cli-{p_name}",
                                title=f"Claude Code: {p_name}",
                                updated_at_ms=mod_time,
                                summary=f"### [Claude Code CLI] Активный проект: {p_name}\nСессия терминального агента Claude Code.",
                            )
                        )
            except Exception as e:
                logger.debug(f"ClaudeCollector error reading .claude.json: {e}")

        return sessions


class AntigravityCollector:
    """Reads conversation transcripts and projects from Antigravity."""

    def __init__(self):
        self.brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"

    def is_available(self) -> bool:
        return self.brain_dir.exists()

    def get_known_projects(self) -> Dict[str, str]:
        """Discover unique project directories from recent transcripts."""
        projects = {}
        if not self.brain_dir.exists():
            return projects

        for conv_dir in self.brain_dir.iterdir():
            if not conv_dir.is_dir():
                continue
            transcript_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if not transcript_file.exists():
                continue
            try:
                with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            st = json.loads(line)
                            for tc in st.get("tool_calls") or []:
                                args = tc.get("args") or {}
                                for k in ("Cwd", "DirectoryPath", "TargetFile", "AbsolutePath", "SearchPath"):
                                    if k in args:
                                        val = str(args[k]).strip("\"'")
                                        if val and ".gemini" not in val.lower() and ("\\" in val or "/" in val or ":" in val):
                                            p_val = Path(val)
                                            norm_path = str(p_val.parent) if p_val.suffix and p_val.parent else str(p_val)
                                            if os.path.exists(norm_path):
                                                name = _clean_project_name(norm_path)
                                                projects[name] = norm_path
                                                break
                                if projects.get(conv_dir.name):
                                    break
                        except Exception:
                            continue
            except Exception:
                continue
        return projects

    def collect_sessions(self, since_ms: int = 0) -> List[ProjectSession]:
        sessions: List[ProjectSession] = []
        if not self.brain_dir.exists():
            return sessions

        for conv_dir in self.brain_dir.iterdir():
            if not conv_dir.is_dir():
                continue
            transcript_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if not transcript_file.exists():
                continue

            try:
                mtime_ms = int(transcript_file.stat().st_mtime * 1000)
                if mtime_ms < since_ms:
                    continue

                detected_path = None
                messages: List[Dict[str, Any]] = []

                with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            step = json.loads(line)
                            # Detect project path from tool calls
                            if not detected_path:
                                for tc in step.get("tool_calls") or []:
                                    args = tc.get("args") or {}
                                    for k in ("Cwd", "DirectoryPath", "TargetFile", "AbsolutePath", "SearchPath"):
                                        if k in args:
                                            val = str(args[k]).strip("\"'")
                                            if val and ".gemini" not in val.lower() and ("\\" in val or "/" in val or ":" in val):
                                                p_val = Path(val)
                                                detected_path = str(p_val.parent) if p_val.suffix and p_val.parent else str(p_val)
                                                break
                                    if detected_path:
                                        break

                            st_type = step.get("type")
                            if st_type == "USER_INPUT":
                                txt = step.get("content", "").replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
                                if "<ADDITIONAL_METADATA>" in txt:
                                    txt = txt.split("<ADDITIONAL_METADATA>")[0].strip()
                                txt = " ".join(txt.split())
                                if txt:
                                    messages.append({"role": "user", "text": txt, "timestamp": mtime_ms})
                            elif st_type == "PLANNER_RESPONSE":
                                cnt = step.get("content", "").strip()
                                if cnt:
                                    messages.append({"role": "assistant", "text": cnt, "timestamp": mtime_ms})
                        except Exception:
                            continue

                user_turns = [m for m in messages if m["role"] == "user"]
                asst_turns = [m for m in messages if m["role"] == "assistant"]

                if user_turns:
                    title = user_turns[0]["text"][:100]
                    proj_path = detected_path or os.getcwd()
                    proj_name = _clean_project_name(proj_path)

                    summary_lines = [f"### [Antigravity] Проект: {proj_name} — {title}"]
                    summary_lines.append(f"**Запрос / Цель**: {user_turns[0]['text'][:350]}")
                    if asst_turns:
                        summary_lines.append(f"**Итог / Решение**: {asst_turns[-1]['text'][:650]}")
                    summary = "\n".join(summary_lines)

                    sessions.append(
                        ProjectSession(
                            agent="antigravity",
                            project_name=proj_name,
                            project_path=proj_path,
                            session_id=conv_dir.name,
                            title=title,
                            updated_at_ms=mtime_ms,
                            messages=messages,
                            summary=summary,
                        )
                    )
            except Exception as e:
                logger.debug(f"AntigravityCollector error reading {transcript_file}: {e}")

        return sessions


def get_all_active_projects() -> List[Dict[str, Any]]:
    """Discover all known projects across Codex, Cursor, Claude Desktop, Antigravity, and local filesystem."""
    projects_map: Dict[str, Dict[str, Any]] = {}

    # 1. From Codex
    codex = CodexCollector()
    for pid, path in codex.get_known_projects().items():
        if path and os.path.exists(path):
            norm = os.path.normpath(path)
            name = _clean_project_name(norm)
            projects_map[norm.lower()] = {
                "name": name,
                "path": norm,
                "sources": ["codex"],
            }

    # 2. From Cursor
    cursor = CursorCollector()
    for whash, path in cursor.get_known_workspaces().items():
        if path and os.path.exists(path):
            norm = os.path.normpath(path)
            key = norm.lower()
            if key in projects_map:
                if "cursor" not in projects_map[key]["sources"]:
                    projects_map[key]["sources"].append("cursor")
            else:
                projects_map[key] = {
                    "name": _clean_project_name(norm),
                    "path": norm,
                    "sources": ["cursor"],
                }

    # 3. From Claude Code
    claude = ClaudeCollector()
    if claude.claude_json.exists():
        try:
            data = json.loads(claude.claude_json.read_text(encoding="utf-8"))
            for p_path in (data.get("projects") or {}).keys():
                if p_path and os.path.exists(p_path):
                    norm = os.path.normpath(p_path)
                    key = norm.lower()
                    if key in projects_map:
                        if "claude" not in projects_map[key]["sources"]:
                            projects_map[key]["sources"].append("claude")
                    else:
                        projects_map[key] = {
                            "name": _clean_project_name(norm),
                            "path": norm,
                            "sources": ["claude"],
                        }
        except Exception:
            pass

    # 4. From Antigravity
    antigravity = AntigravityCollector()
    for p_name, path in antigravity.get_known_projects().items():
        if path and os.path.exists(path):
            norm = os.path.normpath(path)
            key = norm.lower()
            if key in projects_map:
                if "antigravity" not in projects_map[key]["sources"]:
                    projects_map[key]["sources"].append("antigravity")
            else:
                projects_map[key] = {
                    "name": p_name,
                    "path": norm,
                    "sources": ["antigravity"],
                }

    # 5. Always include current workspace
    cwd = os.path.normpath(os.getcwd())
    if cwd.lower() in projects_map:
        if "workspace" not in projects_map[cwd.lower()]["sources"]:
            projects_map[cwd.lower()]["sources"].append("workspace")
    else:
        projects_map[cwd.lower()] = {
            "name": _clean_project_name(cwd),
            "path": cwd,
            "sources": ["workspace"],
        }

    return list(projects_map.values())
