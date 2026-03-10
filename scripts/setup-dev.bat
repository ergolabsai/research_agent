@echo off
setlocal

echo Setting up backend...

cd /d "%~dp0..\backend"

REM -----------------------
REM Ensure Python 3.12 exists
REM -----------------------

echo Checking Python 3.12...
py -3.12 --version >nul 2>&1 || (
    echo Python 3.12 not found. Installing...
    py install 3.12 || exit /b 1
)

REM -----------------------
REM API ENV (Python 3.12)
REM -----------------------
if not exist ".venv\api" (
    echo Creating API virtual environment (Python 3.12)
    py -3.12 -m venv .venv\api
)

call .venv\api\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Backend setup complete.
endlocal