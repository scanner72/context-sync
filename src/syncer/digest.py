"""Generator and injector for Cross-Agent Project Context Digest into CLAUDE.md, AGENTS.md, and .cursorrules."""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

START_MARKER = "<!-- CONTEXT-SYNC-START -->"
END_MARKER = "<!-- CONTEXT-SYNC-END -->"

RULE_FILES = [
    "CLAUDE.md",     # Claude Desktop & Claude Code CLI
    "AGENTS.md",     # OpenAI Codex CLI & Desktop
    ".cursorrules",  # Cursor IDE
]


def format_digest_block(
    project_name: str,
    recent_sessions: List[Dict[str, Any]],
    active_agents: List[str],
    dashboard_url: str = "http://localhost:8000",
    facts_markdown: Optional[str] = None,
) -> str:
    """Build standardized Markdown block containing cross-agent digest."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    agents_str = ", ".join(sorted(set(active_agents))) or "Codex, Claude, Cursor"

    lines = [
        START_MARKER,
        "## 🔄 Multi-Agent Sync (ContextSync)",
        f"> 🕒 Синхронизировано: **{now_str}** | 🤖 Агенты проекта: **{agents_str}**",
        "",
        "### 📌 Недавние действия и контекст из других агентов:",
    ]

    if not recent_sessions:
        lines.append("- *Проект подключен к общей памяти ContextSync. Новые решения и контекст чатов синхронизируются автоматически.*")
    else:
        for s in recent_sessions[:5]:
            agent = s.get("agent", "Agent").capitalize()
            raw_title = s.get("title", "").strip()
            if "<ADDITIONAL_METADATA>" in raw_title:
                raw_title = raw_title.split("<ADDITIONAL_METADATA>")[0].strip()
            title = " ".join(raw_title.split())[:120]
            time_str = s.get("date_str", "")
            time_part = f" ({time_str})" if time_str else ""
            summary_snippet = " ".join(s.get("summary_snippet", "").split())[:120]
            
            lines.append(f"- **{agent}**{time_part}: {title}")
            if summary_snippet and summary_snippet != title:
                lines.append(f"  > _{summary_snippet}_")

    if facts_markdown and facts_markdown.strip():
        lines.extend([
            "",
            facts_markdown.strip(),
        ])

    lines.extend([
        "",
        "### 🧠 Центральная память проекта:",
        f"- Поиск решений других агентов: вызовите `context_search(query=\"...\")`",
        f"- Сохранение ключевых решений: вызовите `context_save(title=\"...\", content=\"...\")`",
        f"- Веб-дашборд и флот: [{dashboard_url}]({dashboard_url})",
        END_MARKER,
    ])

    return "\n".join(lines)



def inject_digest_into_file(target_file: Path, digest_block: str) -> bool:
    """Safely insert or update digest block in a rules file, preserving user content."""
    try:
        if target_file.exists():
            content = target_file.read_text(encoding="utf-8", errors="replace")
            
            # If markers already exist, replace between them
            if START_MARKER in content and END_MARKER in content:
                before = content.split(START_MARKER)[0].rstrip()
                after = content.split(END_MARKER)[1].lstrip()
                new_parts = []
                if before:
                    new_parts.append(before)
                new_parts.append(digest_block)
                if after:
                    new_parts.append(after)
                new_content = "\n\n".join(new_parts) + "\n"
            else:
                # Backup original before modifying if no backup exists
                bak = target_file.with_suffix(target_file.suffix + ".bak")
                if not bak.exists():
                    shutil.copy2(target_file, bak)
                # Prepend block at top so LLM reads it first
                new_content = digest_block + "\n\n" + content.strip() + "\n"
        else:
            # File doesn't exist yet, create it with the block
            target_file.parent.mkdir(parents=True, exist_ok=True)
            new_content = digest_block + "\n"

        target_file.write_text(new_content, encoding="utf-8")
        return True

    except Exception as e:
        logger.error(f"Failed to inject digest into {target_file}: {e}")
        return False


def sync_project_files(
    project_path: str,
    project_name: str,
    recent_sessions: List[Dict[str, Any]],
    active_agents: List[str],
    target_rules: Optional[List[str]] = None,
    dashboard_url: str = "http://localhost:8000",
) -> Dict[str, bool]:
    """Inject cross-agent digest into project context files (CLAUDE.md, AGENTS.md, .cursorrules)."""
    p = Path(project_path)
    if not p.exists() or not p.is_dir():
        return {}

    rules_to_update = target_rules or RULE_FILES
    digest_block = format_digest_block(
        project_name=project_name,
        recent_sessions=recent_sessions,
        active_agents=active_agents,
        dashboard_url=dashboard_url,
    )

    results = {}
    for filename in rules_to_update:
        filepath = p / filename
        success = inject_digest_into_file(filepath, digest_block)
        results[filename] = success

    return results
