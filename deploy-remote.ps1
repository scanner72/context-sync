param (
    [string]$RemoteHost = "10.10.10.11",
    [string]$RemoteUser = "energetik",
    [string]$RemotePath = "/home/energetik/context_sync",
    [int]$AppPort = 8200,
    [int]$PostgresPort = 5445
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

Write-Host "Deploying Context Sync to $RemoteHost ($RemoteUser)..." -ForegroundColor Cyan
Write-Host "App Port: $AppPort | Postgres Port: $PostgresPort" -ForegroundColor Gray

Write-Host "[1/4] Creating remote directory $RemotePath..." -ForegroundColor Yellow
ssh "${RemoteUser}@${RemoteHost}" "mkdir -p $RemotePath"

Write-Host "[2/4] Packaging and syncing repository..." -ForegroundColor Yellow
tar --exclude=".git" --exclude="*__pycache__*" --exclude="*.pytest_cache*" --exclude="*.venv*" --exclude="*fastembed_cache*" --exclude="*postgres_data*" -czf context_sync_full.tar.gz .
scp context_sync_full.tar.gz "${RemoteUser}@${RemoteHost}:${RemotePath}/"
ssh "${RemoteUser}@${RemoteHost}" "cd $RemotePath && tar -xzf context_sync_full.tar.gz && rm context_sync_full.tar.gz"
Remove-Item -Force context_sync_full.tar.gz

Write-Host "[3/4] Building and starting Docker containers..." -ForegroundColor Yellow
ssh "${RemoteUser}@${RemoteHost}" "cd $RemotePath && APP_PORT=$AppPort POSTGRES_EXTERNAL_PORT=$PostgresPort docker compose up -d --build"

Write-Host "[4/4] Verifying service health..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
try {
    $health = Invoke-RestMethod -Uri "http://${RemoteHost}:${AppPort}/health" -TimeoutSec 10
    Write-Host "SUCCESS: Server is running and healthy!" -ForegroundColor Green
    Write-Host "DB Status: $($health.db_status)" -ForegroundColor Green
    Write-Host "Web UI and MCP available at: http://${RemoteHost}:${AppPort}" -ForegroundColor Cyan
} catch {
    Write-Host "Warning: Service still initializing. Check logs with: ssh ${RemoteUser}@${RemoteHost} 'docker logs context-sync-app'" -ForegroundColor Yellow
}