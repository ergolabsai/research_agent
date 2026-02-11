#!/bin/bash
set -e  # Exit immediately if a command fails

echo "Starting backend..."

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Activate Python virtual environment
if [ -f ".venv/api/bin/activate" ]; then
    source .venv/api/bin/activate
else
    echo "Virtual environment not found! Please create it first."
    exit 1
fi

# Start backend (uvicorn)
# Run in background so frontend can start
python -m uvicorn app.main:app --reload --port 8000 &

# Wait a moment for backend to start
sleep 2

echo "Starting frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
npm run dev
