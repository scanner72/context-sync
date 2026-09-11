"""Continuous background sync daemon for multi-agent chats, memory indexing, and project digest updates."""

import os
import sys
import time
import json
import asyncio
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.syncer.collectors import (
    CodexCollector,
    CursorCollector,
    ClaudeCollector,
    AntigravityCollector,
    ProjectSession,
    get_all_active_projects,
)
from src.syncer.digest import sync_project_files

logger = logging.getLogger(__name__)


class AutoSyncDaemon:
    """Orchestrates periodic scanning of all agent chats, vector ingestion, and project file updates."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: str = "ctx_secret_token_7f9a8b1c4e2d3f5a",
        state_file: Optional[Path] = None,
        sync_interval_sec: int = 90,
    ):
        self.api_url = api_url.rstrip("/")
        self.auth_token = auth_token
        self.sync_interval_sec = sync_interval_sec
        self.state_file = state_file or (Path.home() / ".codex" / ".context_sync_daemon_state.json")
        self.state = self._load_state()
        self.is_running = False

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "last_synced_ms": 0,
            "synced_session_ids": {},
            "last_cycle_info": {},
        }

    def _save_state(self):
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not save daemon state: {e}")

    def _post_context_to_server(self, title: str, content: str, project: str, tags: List[str]) -> bool:
        """Post a synced session to the remote context store REST endpoint."""
        url = f"{self.api_url}/api/v1/contexts"
        payload = json.dumps({
            "title": title,
            "content": content,
            "project": project,
            "tags": tags,
            "metadata": {
                "source": "auto-sync-daemon",
                "synced_at": datetime.now().isoformat(),
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status in (200, 201)
        except Exception as e:
            logger.debug(f"Failed to post context to server {url}: {e}")
            return False

    def run_sync_cycle(self) -> Dict[str, Any]:
        """Execute a single synchronization pass across all agents and projects."""
        start_time = datetime.now()
        last_synced_ms = self.state.get("last_synced_ms", 0)
        synced_ids = self.state.get("synced_session_ids", {})

        collectors = [
            ("codex", CodexCollector()),
            ("cursor", CursorCollector()),
            ("claude", ClaudeCollector()),
            ("antigravity", AntigravityCollector()),
        ]

        all_sessions: List[ProjectSession] = []
        new_sessions_count = 0

        # 1. Collect sessions from each installed agent
        for name, col in collectors:
            if hasattr(col, "is_available") and not col.is_available():
                continue
            try:
                # Get sessions updated since last check (or recent 50 if first run)
                sessions = col.collect_sessions(since_ms=last_synced_ms if last_synced_ms > 0 else 0)
                all_sessions.extend(sessions)
            except Exception as e:
                logger.error(f"Error collecting sessions from {name}: {e}")

        # 2. Ingest new sessions into Context Store
        project_sessions_map: Dict[str, List[Dict[str, Any]]] = {}
        max_seen_timestamp_ms = last_synced_ms

        for s in all_sessions:
            if s.updated_at_ms > max_seen_timestamp_ms:
                max_seen_timestamp_ms = s.updated_at_ms

            # Check if this exact session update was already ingested
            prev_updated = synced_ids.get(s.session_id, 0)
            if s.updated_at_ms > prev_updated:
                # Construct document
                doc_title = f"[{s.agent.upper()}] {s.title}"
                full_content = s.summary
                if s.messages:
                    dialogue_text = "\n\n".join(
                        f"**{m['role'].capitalize()}**: {m['text']}" for m in s.messages[-8:]
                    )
                    full_content += f"\n\n#### Последние сообщения диалога:\n{dialogue_text}"

                tags = [s.agent, "auto-synced", "chat-history"]
                ingested = self._post_context_to_server(
                    title=doc_title,
                    content=full_content,
                    project=s.project_name,
                    tags=tags,
                )
                if ingested:
                    synced_ids[s.session_id] = s.updated_at_ms
                    new_sessions_count += 1

            # Group for project digest
            p_key = s.project_name.lower()
            if p_key not in project_sessions_map:
                project_sessions_map[p_key] = []
            
            date_str = ""
            if s.updated_at_ms > 0:
                dt = datetime.fromtimestamp(s.updated_at_ms / 1000.0)
                date_str = dt.strftime("%d %b, %H:%M")

            project_sessions_map[p_key].append({
                "agent": s.agent,
                "title": s.title,
                "date_str": date_str,
                "summary_snippet": s.summary.split("\n")[1][:120] if "\n" in s.summary else "",
            })

        # 3. Discover all active projects and update CLAUDE.md / AGENTS.md / .cursorrules
        active_projects = get_all_active_projects()
        updated_projects_count = 0

        for p_info in active_projects:
            p_path = p_info["path"]
            p_name = p_info["name"]
            p_sources = p_info.get("sources", [])

            recent_sess = project_sessions_map.get(p_name.lower(), [])
            res = sync_project_files(
                project_path=p_path,
                project_name=p_name,
                recent_sessions=recent_sess,
                active_agents=p_sources,
                dashboard_url=self.api_url,
            )
            if any(res.values()):
                updated_projects_count += 1

        # 4. Save state
        self.state["last_synced_ms"] = max_seen_timestamp_ms
        self.state["synced_session_ids"] = synced_ids
        cycle_info = {
            "timestamp": datetime.now().isoformat(),
            "duration_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            "total_active_projects": len(active_projects),
            "projects_updated": updated_projects_count,
            "sessions_scanned": len(all_sessions),
            "new_sessions_synced": new_sessions_count,
        }
        self.state["last_cycle_info"] = cycle_info
        self._save_state()

        return cycle_info

    def start_loop(self):
        """Run blocking continuous sync loop."""
        self.is_running = True
        logger.info(f"Starting AutoSync daemon (interval={self.sync_interval_sec}s)...")
        print(f"🚀 Фоновый демон авто-синхронизации запущен (интервал: {self.sync_interval_sec}с).")
        print(f"   API Context Store: {self.api_url}")
        print("   Нажмите Ctrl+C для остановки.\n")

        while self.is_running:
            try:
                info = self.run_sync_cycle()
                now_str = datetime.now().strftime("%H:%M:%S")
                print(
                    f"[{now_str}] 🔄 Цикл синхронизации завершён: "
                    f"проектов обновлено: {info['projects_updated']} | "
                    f"новых сессий: {info['new_sessions_synced']} | "
                    f"время: {info['duration_ms']}мс"
                )
            except Exception as e:
                logger.error(f"Error in sync cycle: {e}")
                print(f"⚠️ Ошибка цикла синхронизации: {e}")

            time.sleep(self.sync_interval_sec)


def main():
    import argparse

    # Ensure UTF-8 output
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Multi-Agent Chat & Project Auto-Sync Daemon")
    parser.add_argument("--url", default="http://localhost:8000", help="Context Store API base URL")
    parser.add_argument("--token", default="ctx_secret_token_7f9a8b1c4e2d3f5a", help="Auth token")
    parser.add_argument("--interval", type=int, default=90, help="Sync interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit without looping")

    args = parser.parse_args()

    daemon = AutoSyncDaemon(
        api_url=args.url,
        auth_token=args.token,
        sync_interval_sec=args.interval,
    )

    if args.once:
        print("🔍 Запуск единичного цикла синхронизации проектов и чатов...")
        info = daemon.run_sync_cycle()
        print("\n✅ Синхронизация успешно выполнена!")
        print(f"  • Всего активных проектов: {info['total_active_projects']}")
        print(f"  • Обновлено файлов правил (CLAUDE.md, AGENTS.md, .cursorrules): {info['projects_updated']}")
        print(f"  • Найдено и просканировано сессий: {info['sessions_scanned']}")
        print(f"  • Новых сессий сохранено в память: {info['new_sessions_synced']}")
        print(f"  • Время выполнения: {info['duration_ms']} мс")
    else:
        daemon.start_loop()


if __name__ == "__main__":
    main()
