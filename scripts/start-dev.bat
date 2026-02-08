@echo off
echo Starting backend...

REM Go to backend directory
cd /d "%~dp0..\backend"
REM Activate virtual environment
call .venv\Scripts\activate.bat
REM Start backend in new command window
start cmd /k ""%CD%\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000"

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
