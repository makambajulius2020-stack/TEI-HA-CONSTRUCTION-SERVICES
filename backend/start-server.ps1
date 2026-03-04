# TEI-HA Backend Server PowerShell Launcher
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TEI-HA Backend Server Auto-Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if server is already running
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "WARNING: Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "The backend server might already be running." -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to continue anyway? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 0
    }
}

Write-Host "Starting backend server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Use the launcher which handles dependency checking
if (Test-Path "launcher.py") {
    python launcher.py
} else {
    Write-Host "ERROR: launcher.py not found!" -ForegroundColor Red
    Write-Host "Please ensure you're in the correct directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

