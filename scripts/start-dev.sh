#!/bin/bash

# Start backend in background
echo "Starting backend..."
cd "$(dirname "$0")"/.. || exit 1

# Activate virtual environment
source .venv/bin/activate

cd backend || exit 1
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend
echo "Starting frontend..."
cd ../frontend

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run dev

# Cleanup on exit
echo "Cleaning up..."
kill $BACKEND_PID
