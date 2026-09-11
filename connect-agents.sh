#!/usr/bin/env bash
# macOS and Linux helper script to connect all local AI agents to Context Sync
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SCAN_ONLY=0
URL=""
TOKEN=""

for arg in "$@"; do
    case "$arg" in
        --scan-only|-s)
            SCAN_ONLY=1
            ;;
        http*|ws*)
            URL="$arg"
            ;;
        *)
            if [ -z "$TOKEN" ]; then
                TOKEN="$arg"
            fi
            ;;
    esac
done

URL="${URL:-http://localhost:8200/sse}"
TOKEN="${TOKEN:-$AUTH_TOKEN}"

if [ -z "$TOKEN" ] && [ -f ".env" ]; then
    TOKEN=$(grep -E '^AUTH_TOKEN=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
fi

echo "============================================================"
echo "  Context Sync: Auto-Connect AI Agents for macOS and Linux  "
echo "============================================================"

if [ "$SCAN_ONLY" -eq 1 ]; then
    echo "Mode: Scan only"
    echo ""
    python3 -m src.scanner --scan-only
elif [ -z "$TOKEN" ]; then
    echo "Target URL: $URL"
    echo "Mode: Scan only (no token provided)"
    echo ""
    python3 -m src.scanner --scan-only
    echo ""
    echo "To inject configuration, provide a token:"
    echo "  ./connect-agents.sh [URL] [TOKEN]"
else
    echo "Target URL: $URL"
    echo ""
    python3 -m src.scanner --url "$URL" --token "$TOKEN"
fi