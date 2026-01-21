.PHONY: dev-local dev-local-windows dev-local-unix install-api install-frontend clean

# Detect OS
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    SCRIPT_EXT := .bat
    START_CMD := start cmd /c
else
    DETECTED_OS := Unix
    SCRIPT_EXT := .sh
    START_CMD := 
endif

dev-local:
ifeq ($(DETECTED_OS),Windows)
	@$(MAKE) dev-local-windows
else
	@$(MAKE) dev-local-unix
endif

dev-local-windows:
	@echo Starting local development environment (Windows)...
	@cmd /c "start cmd /k scripts\start-api.bat"
	@ping 127.0.0.1 -n 3 > nul
	@cmd /c "start cmd /k scripts\start-frontend.bat"
	@echo Development servers started!
	@echo API: http://localhost:8000
	@echo Frontend: http://localhost:5173

dev-local-unix:
	@echo "Starting local development environment (Unix)..."
	@chmod +x scripts/*.sh
	@scripts/start-api.sh & echo $$! > .api.pid
	@sleep 2
	@scripts/start-frontend.sh & echo $$! > .frontend.pid
	@echo "Development servers started!"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Run 'make stop' to stop all servers"

start-celery:
ifeq ($(DETECTED_OS),Windows)
	@cmd /c "start cmd /k scripts\start-celery.bat"
else
	@chmod +x scripts/start-celery.sh
	@scripts/start-celery.sh &
endif

stop:
	@echo "Stopping development servers..."
ifeq ($(DETECTED_OS),Windows)
	@taskkill /F /FI "WINDOWTITLE eq start-api*" 2>nul || echo No API process found
	@taskkill /F /FI "WINDOWTITLE eq start-frontend*" 2>nul || echo No frontend process found
	@taskkill /F /FI "WINDOWTITLE eq start-celery*" 2>nul || echo No celery process found
else
	@if [ -f .api.pid ]; then kill `cat .api.pid` 2>/dev/null || true; rm .api.pid; fi
	@if [ -f .frontend.pid ]; then kill `cat .frontend.pid` 2>/dev/null || true; rm .frontend.pid; fi
	@if [ -f .celery.pid ]; then kill `cat .celery.pid` 2>/dev/null || true; rm .celery.pid; fi
endif
	@echo "All servers stopped"

install-api:
	@echo "Installing API dependencies..."
	@cd api && pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

install: install-api install-frontend

clean:
	@echo "Cleaning up..."
	@rm -f .api.pid .frontend.pid .celery.pid 2>/dev/null || del .api.pid .frontend.pid .celery.pid 2>nul || echo Clean
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || echo Cleaned pycache
	@find . -type f -name "*.pyc" -delete 2>/dev/null || echo Cleaned pyc files