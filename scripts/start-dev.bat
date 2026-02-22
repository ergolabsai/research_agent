@echo off
echo Starting backend...

REM Activate API environment
call backend\.venv\api\Scripts\activate.bat

REM Start backend
start cmd /k "python -m uvicorn app.main:app --reload --port 8000 --app-dir backend"

timeout /t 2

echo Starting frontend...
cd /d "%~dp0..\frontend"

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

call npm run dev
