@echo off
REM Start backend in new command window
echo Starting backend...
cd /d "%~dp0.."
REM Activate virtual environment
call .venv\Scripts\activate.bat
cd /d "%~dp0..\backend"
start cmd /k "%~dp0..\\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

REM Wait a moment for backend to start
timeout /t 2

REM Start frontend
echo Starting frontend...
cd /d "%~dp0..\frontend"

REM Check if dependencies are installed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

call npm run dev
