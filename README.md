# TEI-HA Construction Services - AI Tools

This project includes a frontend website and a backend API server for TEI-HA Construction Services AI Tools.

## Quick Start

### Option 1: Automatic Start (Recommended)

**Windows:**
1. Double-click `start-backend.bat` in the root directory
2. The server will automatically check dependencies and start

**Linux/Mac:**
1. Run `chmod +x start-backend.sh` to make it executable
2. Run `./start-backend.sh`

### Option 2: Manual Start

1. Navigate to the `backend` directory
2. Install dependencies: `pip install -r ../requirements.txt`
3. Start the server: `python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload`

### Option 3: Using Python Launcher

1. Navigate to the `backend` directory
2. Run: `python launcher.py`

The launcher will automatically:
- Check Python version
- Verify and install missing dependencies
- Start the server

## Server Endpoints

Once the server is running, it will be available at:
- **Base URL:** `http://localhost:8000`
- **Health Check:** `http://localhost:8000/health`
- **User Registration:** `POST http://localhost:8000/api/users/register`
- **AI Tools:** `POST http://localhost:8000/api/tools/*`
- **Chat API:** `POST http://localhost:8000/api/chat`

## Development

### Starting Development Environment

**Windows:**
- Run `start-dev.bat` to start the backend in a separate window

**Linux/Mac:**
- Run `./start-dev.sh` to start the backend in the background

### Frontend Files

- `index.html` - Main website
- `ai-tools.html` - AI Tools page
- `pricing.html` - Pricing page

### Backend Files

- `backend/server.py` - FastAPI server (main backend)
- `backend/node-server.js` - Node.js server (optional, for email features)
- `backend/launcher.py` - Python launcher with auto-dependency checking

## Requirements

- Python 3.7 or higher
- pip (Python package manager)

Required Python packages (auto-installed by launcher):
- fastapi
- uvicorn
- httpx
- python-multipart
- Pillow

## Troubleshooting

### "Cannot connect to server" Error

1. Make sure the backend server is running
2. Check that port 8000 is not in use by another application
3. Verify Python is installed: `python --version`
4. Try running `start-backend.bat` or `start-backend.sh`

### Port Already in Use

If port 8000 is already in use:
1. Find and stop the process using port 8000
2. Or modify the port in `server.py` and update the frontend API URLs

### Dependencies Not Installing

Run manually:
```bash
pip install -r requirements.txt
```

## File Structure

```
.
├── index.html              # Main website
├── ai-tools.html          # AI Tools page
├── pricing.html           # Pricing page
├── start-backend.bat      # Windows auto-start script
├── start-backend.sh       # Linux/Mac auto-start script
├── start-dev.bat          # Windows dev environment
├── start-dev.sh           # Linux/Mac dev environment
├── requirements.txt       # Python dependencies
├── backend/
│   ├── server.py          # FastAPI backend server
│   ├── node-server.js     # Node.js server (optional)
│   ├── launcher.py        # Python launcher
│   ├── start-server.bat   # Backend startup (Windows)
│   └── start-server.sh    # Backend startup (Linux/Mac)
└── images/                # Image assets
```

## Notes

- The backend server must be running for the AI Tools features to work
- The server includes CORS middleware, so it can be accessed from the frontend
- The server runs in reload mode during development (auto-restarts on file changes)

