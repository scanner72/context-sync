@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo  Context Sync: Автоподключение локальных ИИ-агентов
echo ========================================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0connect-agents.ps1" %*
echo.
pause
