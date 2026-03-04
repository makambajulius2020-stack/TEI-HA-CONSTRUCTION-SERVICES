@echo off
title TEI-HA Backend Server (Auto-Start)
color 0A
echo ========================================
echo   TEI-HA Backend Server Auto-Start
echo ========================================
echo.

REM Change to project root directory
cd /d "%~dp0"

REM Navigate to backend directory
cd backend

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if server is already running
netstat -ano | findstr ":8000" >nul 2>nul
if not errorlevel 1 (
    echo WARNING: Port 8000 is already in use!
    echo The backend server might already be running.
    echo.
    choice /C YN /M "Do you want to continue anyway"
    if errorlevel 2 exit /b 0
)

echo Starting backend server...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

REM Use the launcher which handles dependency checking
if exist "launcher.py" (
    python launcher.py
) else (
    echo ERROR: launcher.py not found!
    echo Please ensure you're in the correct directory.
    pause
    exit /b 1
)

pause

