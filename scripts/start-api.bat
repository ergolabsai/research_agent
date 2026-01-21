:: scripts/start-api.bat
@echo off
:: Load environment variables from .env file
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%b"=="" set %%a=%%b
)
:: Start API server
cd api
%PYTHON_PATH% -m uvicorn main:app --reload --host 0.0.0.0 --port %API_PORT%