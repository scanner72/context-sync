#!/usr/bin/env bash
# macOS and Linux deployment script to launch Context Sync on a remote Docker server
set -e

REMOTE_HOST="${1:-10.10.10.11}"
REMOTE_USER="${2:-energetik}"
REMOTE_PATH="${3:-/home/energetik/context_sync}"
APP_PORT="${4:-8200}"
POSTGRES_PORT="${5:-5445}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  Deploying Context Sync to ${REMOTE_HOST} (${REMOTE_USER}) "
echo "============================================================"
echo "• App Port: ${APP_PORT} | Postgres Port: ${POSTGRES_PORT}"
echo ""

echo "[1/4] Creating remote directory ${REMOTE_PATH}..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_PATH}"

echo "[2/4] Packaging and uploading repository..."
tar --exclude=".git" --exclude="*__pycache__*" --exclude="*.pytest_cache*" --exclude="*.venv*" --exclude="*fastembed_cache*" --exclude="*postgres_data*" -czf context_sync_full.tar.gz .
scp context_sync_full.tar.gz "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && tar -xzf context_sync_full.tar.gz && rm context_sync_full.tar.gz && chmod +x *.sh"
rm -f context_sync_full.tar.gz

echo "[3/4] Building and launching Docker Compose..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && APP_PORT=${APP_PORT} POSTGRES_EXTERNAL_PORT=${POSTGRES_PORT} docker compose up -d --build"

echo "[4/4] Verifying health status..."
sleep 5
if curl -fs "http://${REMOTE_HOST}:${APP_PORT}/health" > /dev/null 2>&1; then
    echo "SUCCESS: Context Sync is running and healthy on http://${REMOTE_HOST}:${APP_PORT}"
else
    echo "Warning: Service still warming up. Check logs with: ssh ${REMOTE_USER}@${REMOTE_HOST} 'docker logs context-sync-app'"
fi