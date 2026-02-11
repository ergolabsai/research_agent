#!/bin/bash
set -e  # Exit immediately if a command fails

echo "Setting up backend..."

# Navigate to backend directory relative to script location
cd "$(dirname "$0")/../backend"

# -----------------------
# Ensure Python versions exist
# -----------------------

check_python() {
    PY_VERSION=$1
    if ! command -v "python${PY_VERSION}" &>/dev/null; then
        echo "Python ${PY_VERSION} not found."
        echo "Please install Python ${PY_VERSION} manually."
        exit 1
    else
        echo "Python ${PY_VERSION} found: $(python${PY_VERSION} --version)"
    fi
}

echo "Checking Python 3.11..."
check_python 3.11

echo "Checking Python 3.14..."
check_python 3.14

# -----------------------
# API ENV (Python 3.14)
# -----------------------
if [ ! -d ".venv/api" ]; then
    echo "Creating API virtual environment (Python 3.14)"
    python3.14 -m venv .venv/api
fi

echo "Activating API virtual environment..."
source .venv/api/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-api.txt
deactivate

# -----------------------
# TORCH ENV (Python 3.11)
# -----------------------
if [ ! -d ".venv/torch" ]; then
    echo "Creating Torch virtual environment (Python 3.11)"
    python3.11 -m venv .venv/torch
fi

echo "Activating Torch virtual environment..."
source .venv/torch/bin/activate
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
python -m pip install -r requirements-torch.txt
deactivate

echo "Backend setup complete."
