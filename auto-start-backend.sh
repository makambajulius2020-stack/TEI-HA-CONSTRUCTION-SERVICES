#!/bin/bash

echo "========================================"
echo "  TEI-HA Backend Server Auto-Start"
echo "========================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"
cd backend

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH!"
    echo "Please install Python from https://www.python.org/"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)

echo "Python found: $($PYTHON_CMD --version)"
echo ""

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -an 2>/dev/null | grep -q ":8000.*LISTEN"; then
    echo "WARNING: Port 8000 is already in use!"
    echo "The backend server might already be running."
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "Starting backend server..."
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================"
echo ""

# Use the launcher which handles dependency checking
if [ -f "launcher.py" ]; then
    $PYTHON_CMD launcher.py
else
    echo "ERROR: launcher.py not found!"
    echo "Please ensure you're in the correct directory."
    exit 1
fi

