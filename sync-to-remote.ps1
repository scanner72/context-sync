param (
    [string]$RemoteHost = "10.10.10.11",
    [string]$RemoteUser = "energetik",
    [string]$RemotePath = "/home/energetik/context_sync"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

Write-Host "Syncing src, migrations, and tests to $RemoteHost..." -ForegroundColor Cyan
tar --exclude="*__pycache__*" --exclude="*.pytest_cache*" --exclude="*.venv*" --exclude="*fastembed_cache*" --exclude="*postgres_data*" -czf context_sync_update.tar.gz src migrations tests
scp context_sync_update.tar.gz "${RemoteUser}@${RemoteHost}:${RemotePath}/"
ssh "${RemoteUser}@${RemoteHost}" "cd $RemotePath && tar -xzf context_sync_update.tar.gz && rm context_sync_update.tar.gz && docker restart context-sync-app"
Remove-Item -Force context_sync_update.tar.gz

Write-Host "Done! Server restarted and updated at http://${RemoteHost}:8200" -ForegroundColor Green