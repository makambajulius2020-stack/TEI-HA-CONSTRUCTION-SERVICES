#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  TEI-HA Development Environment"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo -e "${BLUE}Starting Backend Server...${NC}"
echo ""

# Start backend in background
./start-backend.sh &
BACKEND_PID=$!

echo -e "${GREEN}Backend server started (PID: $BACKEND_PID)${NC}"
echo ""
echo "You can now open index.html in your browser"
echo "Backend will be available at http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the backend server"
echo ""

# Wait for user interrupt
trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM
wait $BACKEND_PID

