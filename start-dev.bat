@echo off
title TEI-HA Development Server
color 0B
echo ========================================
echo   TEI-HA Development Environment
echo ========================================
echo.

cd /d "%~dp0"

echo Starting Backend Server...
echo.

REM Start backend in a new window
start "TEI-HA Backend" cmd /k "cd /d %~dp0 && call start-backend.bat"

echo Backend server starting in a new window...
echo.
echo You can now open index.html in your browser
echo Backend will be available at http://localhost:8000
echo.
echo Press any key to exit this window (backend will keep running)...
pause >nul

