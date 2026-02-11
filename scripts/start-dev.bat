@echo off
echo Starting backend...

cd /d "%~dp0..\backend"

REM Activate API environment
call .venv\api\Scripts\activate.bat

REM Start backend
start cmd /k ""%CD%\.venv\api\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000"

timeout /t 2

echo Starting frontend...
cd /d "%~dp0..\frontend"

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

call npm run dev
