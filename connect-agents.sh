#!/usr/bin/env bash
# macOS and Linux helper script to connect all local AI agents to Context Sync
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

URL="${1:-http://localhost:8200/sse}"
TOKEN="${2:-$AUTH_TOKEN}"

# If token not passed and not in env, try to read from .env
if [ -z "$TOKEN" ] && [ -f ".env" ]; then
    TOKEN=$(grep -E '^AUTH_TOKEN=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
fi

echo "============================================================"
echo "  Context Sync: Auto-Connect AI Agents (macOS & Linux)      "
echo "============================================================"
echo "• Target URL: $URL"
echo ""

if [ -z "$TOKEN" ]; then
    echo "Scanning installed agents without modifying configs (scan-only mode)..."
    python3 -m src.scanner --scan-only
    echo ""
    echo "To inject configuration, provide a token:"
    echo "  ./connect-agents.sh http://localhost:8200/sse <YOUR_TOKEN>"
else
    python3 -m src.scanner --url "$URL" --token "$TOKEN"
fi