@echo off
chcp 65001 >nul
title Context Sync Auto-Sync Daemon
cd /d "%~dp0"

echo ============================================================
echo   Context Sync: Фоновый демон кросс-агентной синхронизации
echo ============================================================
echo.
echo • Сканирует чаты Codex, Cursor, Claude и Antigravity
echo • Сохраняет решения в центральную векторную базу знаний
echo • Обновляет CLAUDE.md, AGENTS.md и .cursorrules в проектах
echo.

python -m src.syncer.daemon --interval 90
pause
