@echo off
chcp 65001 > nul
echo ========================================
echo    TEI-HA Backend Auto Starter
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install/update dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy aiosqlite httpx authlib python-multipart email-validator

:: Start the server
echo.
echo ========================================
echo    Starting FastAPI Server...
echo ========================================
echo.
uvicorn server:app --reload --host 0.0.0.0 --port 8000

pause
