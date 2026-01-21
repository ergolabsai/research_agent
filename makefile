.PHONY: dev-local install-api install-frontend clean

# Load environment variables from .env
include .env
export

dev-local:
	@echo "Starting local development environment..."
	@echo "Starting API server..."
	@cd api && $(PYTHON_PATH) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 & \
	echo $$! > .api.pid
	@echo "Starting frontend..."
	@cd frontend && npm run dev & \
	echo $$! > .frontend.pid
	@echo "Development servers started!"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Run 'make stop' to stop all servers"

stop:
	@echo "Stopping development servers..."
	@if [ -f .api.pid ]; then \
		kill `cat .api.pid` 2>/dev/null || true; \
		rm .api.pid; \
	fi
	@if [ -f .frontend.pid ]; then \
		kill `cat .frontend.pid` 2>/dev/null || true; \
		rm .frontend.pid; \
	fi
	@echo "All servers stopped"

install-api:
	@echo "Installing API dependencies..."
	@cd api && $(PYTHON_PATH) -m pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

install: install-api install-frontend

clean:
	@echo "Cleaning up..."
	@rm -f .api.pid .frontend.pid
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true