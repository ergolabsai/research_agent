#!/bin/bash

# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

set -e

echo "Setting up backend..."

cd "$(dirname "$0")/../backend"

# -----------------------
# Ensure Python 3.12 exists
# -----------------------

echo "Checking Python 3.12..."
if ! command -v python3.12 &>/dev/null; then
    echo "Python 3.12 not found. Please install it manually."
    exit 1
else
    echo "Python 3.12 found: $(python3.12 --version)"
fi

# -----------------------
# API ENV (Python 3.12)
# -----------------------
if [ ! -d ".venv/api" ]; then
    echo "Creating API virtual environment (Python 3.12)..."
    python3.12 -m venv .venv/api
fi

echo "Activating API virtual environment..."
source .venv/api/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
deactivate

echo "Backend setup complete."