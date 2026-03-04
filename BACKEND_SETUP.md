# Backend Setup Guide

## Python Library Used

**FastAPI** - Modern, fast Python web framework for building APIs
- **Server**: Uvicorn (ASGI server)
- **Other libraries**: httpx, authlib, python-jose, Pillow, python-multipart

## Quick Start - Automatic Backend Launch

### Windows (Recommended)
1. **Double-click** `auto-start-backend.bat` in the root directory
   - Automatically checks Python installation
   - Verifies dependencies are installed
   - Starts the server on http://localhost:8000

2. **For silent background start** (no window):
   - Double-click `start-backend-silent.bat`
   - Server runs in minimized window

### Linux/Mac
1. Make script executable:
   ```bash
   chmod +x auto-start-backend.sh
   ```

2. Run:
   ```bash
   ./auto-start-backend.sh
   ```

## Manual Start

### Option 1: Using Python Launcher (Recommended)
```bash
cd backend
python launcher.py
```

### Option 2: Direct Uvicorn
```bash
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## Requirements

- **Python 3.7+**
- **Dependencies** (auto-installed by launcher):
  - fastapi==0.115.0
  - uvicorn[standard]==0.30.6
  - httpx==0.27.2
  - python-multipart==0.0.9
  - Pillow==10.4.0
  - authlib==1.3.0
  - python-jose[cryptography]==3.3.0

## Verify Server is Running

Open in browser: http://localhost:8000/health

Should return: `{"status":"ok"}`

## Server Endpoints

- **Health Check**: `GET http://localhost:8000/health`
- **User Registration**: `POST http://localhost:8000/api/users/register`
- **AI Tools**: `POST http://localhost:8000/api/tools/*`
- **Chat API**: `POST http://localhost:8000/api/chat`
- **Billing**: `POST http://localhost:8000/api/billing/*`

## Troubleshooting

### Port 8000 Already in Use
- Another instance might be running
- Check: `netstat -ano | findstr :8000` (Windows)
- Kill process or use different port

### Python Not Found
- Install Python from https://www.python.org/
- Make sure Python is in your PATH

### Dependencies Not Installing
- Run manually: `pip install -r requirements.txt`
- Make sure pip is up to date: `python -m pip install --upgrade pip`

