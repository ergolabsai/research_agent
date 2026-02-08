@echo off
setlocal

echo Setting up backend...

REM Go to backend directory
cd /d "%~dp0..\backend"

REM Create venv if missing
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Backend setup complete.

endlocal
