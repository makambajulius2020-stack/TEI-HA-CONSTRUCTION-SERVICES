#!/bin/bash
echo "Starting TEI-HA Backend Server..."
echo ""
echo "Make sure you have Python and the required packages installed."
echo "Run: pip install -r requirements.txt"
echo ""
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

