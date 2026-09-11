"""Automated tests for auto-sync collectors, digest generation, and safe file injection."""

import os
import json
import sqlite3
import pytest
from pathlib import Path

from src.syncer.digest import (
    format_digest_block,
    inject_digest_into_file,
    sync_project_files,
    START_MARKER,
    END_MARKER,
)
from src.syncer.collectors import (
    CodexCollector,
    ProjectSession,
    _clean_project_name,
)


def test_clean_project_name():
    assert _clean_project_name(r"D:\monitoring") == "monitoring"
    assert _clean_project_name(r"\\?\C:\Users\scann\my-app") == "my-app"
    assert _clean_project_name(r"file:///d%3A/testbot") == "testbot"
    assert _clean_project_name(None, "default") == "default"


def test_format_digest_block():
    sessions = [
        {
            "agent": "codex",
            "title": "Configured database schema",
            "date_str": "11 Sep, 11:30",
            "summary_snippet": "Added pgvector HNSW index",
        },
        {
            "agent": "claude",
            "title": "Built REST API endpoints",
            "date_str": "11 Sep, 11:35",
            "summary_snippet": "Added auto-sync router",
        },
    ]
    block = format_digest_block("my_project", sessions, ["codex", "claude"])

    assert START_MARKER in block
    assert END_MARKER in block
    assert "Multi-Agent Sync (ContextSync)" in block
    assert "Configured database schema" in block
    assert "Built REST API endpoints" in block
    assert "Codex" in block
    assert "Claude" in block
    assert "context_search" in block


def test_inject_digest_new_file(tmp_path):
    target = tmp_path / "CLAUDE.md"
    assert not target.exists()

    block = format_digest_block("proj", [], ["codex"])
    success = inject_digest_into_file(target, block)
    assert success is True
    assert target.exists()

    content = target.read_text(encoding="utf-8")
    assert START_MARKER in content
    assert END_MARKER in content


def test_inject_digest_preserves_user_rules(tmp_path):
    target = tmp_path / "AGENTS.md"
    user_rules = "# Custom User Instructions\n\nAlways write tests in pytest.\nUse strict typing."
    target.write_text(user_rules, encoding="utf-8")

    block1 = format_digest_block("proj", [{"agent": "codex", "title": "First change"}], ["codex"])
    success = inject_digest_into_file(target, block1)
    assert success is True

    # Check backup was created
    bak = tmp_path / "AGENTS.md.bak"
    assert bak.exists()
    assert bak.read_text(encoding="utf-8") == user_rules

    content = target.read_text(encoding="utf-8")
    assert START_MARKER in content
    assert "First change" in content
    assert "Always write tests in pytest." in content

    # Now update with block2 — user rules must STILL be there!
    block2 = format_digest_block("proj", [{"agent": "claude", "title": "Second change"}], ["claude"])
    inject_digest_into_file(target, block2)

    updated_content = target.read_text(encoding="utf-8")
    assert "Second change" in updated_content
    assert "First change" not in updated_content
    assert "Always write tests in pytest." in updated_content


def test_sync_project_files_all_rules(tmp_path):
    proj_dir = tmp_path / "my_project"
    proj_dir.mkdir()

    results = sync_project_files(
        project_path=str(proj_dir),
        project_name="my_project",
        recent_sessions=[{"agent": "codex", "title": "Demo"}],
        active_agents=["codex", "cursor"],
    )

    assert results["CLAUDE.md"] is True
    assert results["AGENTS.md"] is True
    assert results[".cursorrules"] is True

    assert (proj_dir / "CLAUDE.md").exists()
    assert (proj_dir / "AGENTS.md").exists()
    assert (proj_dir / ".cursorrules").exists()


def test_codex_collector_mock(tmp_path):
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()

    state_db = codex_home / "state_5.sqlite"
    con = sqlite3.connect(state_db)
    cur = con.cursor()
    cur.execute("CREATE TABLE project_roots (project_id TEXT, position INTEGER, path TEXT)")
    cur.execute("INSERT INTO project_roots VALUES ('p1', 0, 'D:\\mock_project')")

    cur.execute("""
        CREATE TABLE threads (
            id TEXT, rollout_path TEXT, cwd TEXT, title TEXT,
            first_user_message TEXT, created_at_ms INTEGER,
            updated_at_ms INTEGER, project_id TEXT
        )
    """)
    cur.execute("""
        INSERT INTO threads VALUES (
            't1', '', 'D:\\mock_project', 'Fix auth bug',
            'Please fix auth', 1000, 2000, 'p1'
        )
    """)
    con.commit()
    con.close()

    collector = CodexCollector(codex_home=codex_home)
    assert collector.is_available() is True

    projects = collector.get_known_projects()
    assert "p1" in projects
    assert "mock_project" in projects["p1"]

    sessions = collector.collect_sessions(since_ms=0)
    assert len(sessions) == 1
    assert sessions[0].title == "Fix auth bug"
    assert sessions[0].project_name == "mock_project"
