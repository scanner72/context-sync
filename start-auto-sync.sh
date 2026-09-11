#!/usr/bin/env bash
# macOS and Linux runner for Context Sync Auto-Sync Daemon
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  Context Sync: Continuous Background Auto-Sync Daemon       "
echo "============================================================"
echo ""
echo "• Continuously indexes Codex, Cursor, Claude & Antigravity chats"
echo "• Saves architectural decisions to central pgvector database"
echo "• Updates CLAUDE.md, AGENTS.md, and .cursorrules across projects"
echo ""

INTERVAL="${1:-90}"
python3 -m src.syncer.daemon --interval "$INTERVAL"