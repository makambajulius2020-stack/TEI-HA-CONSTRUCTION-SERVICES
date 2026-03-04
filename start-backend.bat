@echo off
title TEI-HA Backend Server
color 0A
echo ========================================
echo   TEI-HA Backend Server Auto-Start
echo ========================================
echo.

cd /d "%~dp0backend"

REM Use Python launcher if available, otherwise fall back to direct uvicorn
if exist "launcher.py" (
    python launcher.py
) else (
    echo Checking Python installation...
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH!
        echo Please install Python from https://www.python.org/
        pause
        exit /b 1
    )
    
    echo Python found!
    echo.
    
    echo Checking if required packages are installed...
    python -c "import fastapi, uvicorn" >nul 2>&1
    if errorlevel 1 (
        echo Installing required packages...
        pip install -r ..\requirements.txt
        if errorlevel 1 (
            echo ERROR: Failed to install packages!
            pause
            exit /b 1
        )
        echo Packages installed successfully!
        echo.
    )
    
    echo Starting server on http://localhost:8000
    echo Press Ctrl+C to stop the server
    echo.
    echo ========================================
    echo.
    
    python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
)

pause

