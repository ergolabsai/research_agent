#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend..."

if [ ! -f "$SCRIPT_DIR/../backend/.venv/api/bin/activate" ]; then
    echo "Virtual environment not found! Please run setup.sh first."
    exit 1
fi

# Start backend in a new terminal window if possible, otherwise background it
if command -v gnome-terminal &>/dev/null; then
    gnome-terminal -- bash -c "source '$SCRIPT_DIR/../backend/.venv/api/bin/activate' && python -m uvicorn app.main:app --reload --port 8070 --app-dir '$SCRIPT_DIR/../backend'; exec bash"
elif command -v osascript &>/dev/null; then
    # macOS
    osascript -e "tell app \"Terminal\" to do script \"source '$SCRIPT_DIR/../backend/.venv/api/bin/activate' && python -m uvicorn app.main:app --reload --port 8070 --app-dir '$SCRIPT_DIR/../backend'\""
else
    # Fallback: run in background
    source "$SCRIPT_DIR/../backend/.venv/api/bin/activate"
    python -m uvicorn app.main:app --reload --port 8070 --app-dir "$SCRIPT_DIR/../backend" &
    deactivate
fi

sleep 2

echo "Starting frontend..."

cd "$SCRIPT_DIR/../frontend"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run dev