@echo off
REM Silent background start - runs backend without showing window
REM This can be used for auto-starting the backend

cd /d "%~dp0backend"

REM Check if already running
netstat -ano | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo Backend already running on port 8000
    exit /b 0
)

REM Start in background (minimized window)
start /MIN "" python launcher.py

timeout /t 3 /nobreak >nul
echo Backend server starting in background...
echo Check http://localhost:8000/health to verify it's running

