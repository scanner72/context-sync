#!/usr/bin/env bash
# macOS and Linux helper to incrementally sync code changes to a remote Context Sync host
set -e

REMOTE_HOST="${1:-10.10.10.11}"
REMOTE_USER="${2:-energetik}"
REMOTE_PATH="${3:-/home/energetik/context_sync}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Syncing src, migrations, and tests to ${REMOTE_HOST}..."
tar --exclude="*__pycache__*" --exclude="*.pytest_cache*" --exclude="*.venv*" --exclude="*fastembed_cache*" --exclude="*postgres_data*" -czf context_sync_update.tar.gz src migrations tests
scp context_sync_update.tar.gz "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && tar -xzf context_sync_update.tar.gz && rm context_sync_update.tar.gz && docker restart context-sync-app"
rm -f context_sync_update.tar.gz

echo "Done! Server updated and restarted on http://${REMOTE_HOST}:8200"