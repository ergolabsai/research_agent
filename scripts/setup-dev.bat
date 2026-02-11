@echo off
setlocal

echo Setting up backend...

cd /d "%~dp0..\backend"

REM -----------------------
REM Ensure Python versions exist
REM -----------------------

echo Checking Python 3.11...
py -3.11 --version >nul 2>&1 || (
    echo Python 3.11 not found. Installing...
    py install 3.11 || exit /b 1
)

echo Checking Python 3.14...
py -3.14 --version >nul 2>&1 || (
    echo Python 3.14 not found. Installing...
    py install 3.14 || exit /b 1
)

REM -----------------------
REM API ENV (Python 3.14)
REM -----------------------
if not exist ".venv\api" (
    echo Creating API virtual environment (Python 3.14)
    py -3.14 -m venv .venv\api
)

call .venv\api\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-api.txt

REM -----------------------
REM TORCH ENV (Python 3.11)
REM -----------------------
if not exist ".venv\torch" (
    echo Creating Torch virtual environment (Python 3.11)
    py -3.11 -m venv .venv\torch
)

call .venv\torch\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
python -m pip install -r requirements-torch.txt

echo Backend setup complete.
endlocal
