@echo off

echo Starting backend...
start cmd /k ".\backend\.venv\api\Scripts\python.exe -m uvicorn app.main:app --reload --port 8070 --app-dir backend"
timeout /t 2

echo Starting frontend...
cd /d "%~dp0..\frontend"
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)
call npm run dev
