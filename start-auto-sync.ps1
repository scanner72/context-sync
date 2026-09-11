# PowerShell runner for Context Sync Auto-Sync Daemon
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Context Sync: Фоновый демон кросс-агентной синхронизации  " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
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

# Run daemon with 90s interval
python -m src.syncer.daemon --interval 90
