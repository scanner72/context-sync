param(
    [string]$Server = "http://10.10.10.11:8200",
    [string]$Token = "ctx_secret_token_7f9a8b1c4e2d3f5a",
    [int]$Interval = 90,
    [switch]$Once,
    [switch]$Reset,
    [switch]$Background
)

# PowerShell runner for Context Sync Auto-Sync Daemon
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Context Sync: Фоновый демон кросс-агентной синхронизации  " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "• Сервер: $Server" -ForegroundColor Yellow
Write-Host "• Сканирует чаты Codex, Cursor, Claude и Antigravity" -ForegroundColor Gray
Write-Host "• Сохраняет решения в центральную векторную базу знаний" -ForegroundColor Gray
Write-Host "• Обновляет CLAUDE.md, AGENTS.md и .cursorrules в проектах" -ForegroundColor Gray
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

# Check Python
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Host "ОШИБКА: Python не найден в PATH!" -ForegroundColor Red
    exit 1
}

$daemonArgs = @("-m", "src.syncer.daemon", "--url", $Server, "--token", $Token, "--interval", $Interval)
if ($Once) { $daemonArgs += "--once" }
if ($Reset) { $daemonArgs += "--reset" }

if ($Background) {
    $logFile = Join-Path $env:TEMP "context_sync_daemon.log"
    Write-Host "[OK] Запуск демона в фоновом режиме (лог: $logFile)..." -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList $daemonArgs -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $logFile
    Write-Host "Фоновый процесс запущен. Контексты и проекты синхронизируются каждые $Interval с." -ForegroundColor Cyan
} else {
    & python @daemonArgs
}
