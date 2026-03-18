# =============================================================================
#  Research Advisor — Makefile
# =============================================================================
.DEFAULT_GOAL := help
SHELL := /bin/bash

# ---- Compose file stacks ----------------------------------------------------
COMPOSE_BASE    := docker compose -f docker/docker-compose.yml
COMPOSE_DEV     := $(COMPOSE_BASE) -f docker/docker-compose.dev.yml
COMPOSE_GPU     := $(COMPOSE_BASE) -f docker/docker-compose.gpu.yml
COMPOSE_DEV_GPU := $(COMPOSE_DEV) -f docker/docker-compose.gpu.yml

# ---- ANSI colour codes ------------------------------------------------------
BLUE    := \033[1;34m
CYAN    := \033[0;36m
GREEN   := \033[0;32m
YELLOW  := \033[0;33m
RED     := \033[0;31m
ORANGE  := \033[38;5;208m
RESET   := \033[0m

# =============================================================================
#  Help
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo -e '$(CYAN) ============================================$(RESET)'
	@echo -e '$(CYAN)   Advisor Application - Makefile$(RESET)'
	@echo -e '$(CYAN) ============================================$(RESET)'
	@echo ''
	@echo -e '$(YELLOW) Usage:$(RESET)'
	@echo -e '    $(ORANGE) make $(CYAN)[target]$(RESET)'
	@echo ''
	@echo -e '$(YELLOW) Development:$(RESET)'
	@grep -E '^(dev|dev-gpu|up|up-cpu|gpu|down|restart|build|build-gpu|rebuild)[[:space:]]*:.*##' $(MAKEFILE_LIST) \
		| awk -F ':.*## ' '{printf "    $(CYAN) %-18s$(RESET) %s\n", $$1, $$2}'
	@echo ''
	@echo -e '$(YELLOW) Logs:$(RESET)'
	@grep -E '^logs[a-z-]*[[:space:]]*:.*##' $(MAKEFILE_LIST) \
		| awk -F ':.*## ' '{printf "    $(CYAN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ''
	@echo -e '$(YELLOW) Utilities:$(RESET)'
	@grep -E '^(status|ps|shell-[a-z]+|clean|clean-[a-z]+|health|env|init|db-shell)[[:space:]]*:.*##' $(MAKEFILE_LIST) \
		| awk -F ':.*## ' '{printf "    $(CYAN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ''

# =============================================================================
#  Development
# =============================================================================

.PHONY: dev dev-gpu up up-cpu gpu down restart build build-gpu rebuild

dev: _ensure-env ## Preferred daily workflow: dev mode (CPU, hot-reload)
	@echo -e '$(GREEN)Starting dev environment (CPU)...$(RESET)'
	$(COMPOSE_DEV) up --build

dev-gpu: _ensure-env ## Start all services in dev mode (GPU, hot-reload)
	@echo -e '$(GREEN)Starting dev environment (GPU)...$(RESET)'
	$(COMPOSE_DEV_GPU) up --build

up: _ensure-env ## Production runtime with GPU image (use only when GPU is required)
	@echo -e '$(GREEN)Starting production environment (GPU)...$(RESET)'
	$(COMPOSE_GPU) up -d --build

up-cpu: _ensure-env ## Production runtime on CPU (faster build/start for most local runs)
	@echo -e '$(GREEN)Starting production environment (CPU)...$(RESET)'
	$(COMPOSE_BASE) up -d --build

down: ## Stop all services
	@echo -e '$(YELLOW)Stopping all services...$(RESET)'
	$(COMPOSE_BASE) down
	@$(COMPOSE_DEV) down 2>/dev/null || true
	@$(COMPOSE_GPU) down 2>/dev/null || true

restart: down up ## Restart all services (production)

build: ## Build all Docker images (CPU)
	@echo -e '$(CYAN)Building images (CPU)...$(RESET)'
	$(COMPOSE_BASE) build

build-gpu: ## Build all Docker images (GPU)
	@echo -e '$(CYAN)Building images (GPU)...$(RESET)'
	$(COMPOSE_GPU) build

rebuild: ## Build images from scratch (no cache, CPU)
	@echo -e '$(CYAN)Rebuilding images (no cache)...$(RESET)'
	$(COMPOSE_BASE) build --no-cache

# =============================================================================
#  Logs
# =============================================================================

.PHONY: logs logs-api logs-frontend logs-streamlit logs-calculator

logs: ## Tail logs from all services
	$(COMPOSE_BASE) logs -f --tail=100

logs-api: ## Tail API logs
	$(COMPOSE_BASE) logs -f --tail=100 api

logs-frontend: ## Tail frontend logs
	$(COMPOSE_BASE) logs -f --tail=100 frontend

logs-streamlit: ## Tail Streamlit logs
	$(COMPOSE_BASE) logs -f --tail=100 streamlit

logs-calculator: ## Tail Calculator logs
	$(COMPOSE_BASE) logs -f --tail=100 calculator

# =============================================================================
#  Utilities
# =============================================================================

.PHONY: status ps health shell-api shell-frontend clean clean-volumes clean-images env init db-shell

status: ## Show running containers and health status
	@echo -e '$(CYAN)Container status:$(RESET)'
	@docker ps --filter "label=com.docker.compose.project=advisor" \
		--format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
		|| $(COMPOSE_BASE) ps

ps: status ## Alias for status

health: ## Check health endpoints
	@echo -e '$(CYAN)Checking health endpoints...$(RESET)'
	@API_PORT=$$(grep -E '^API_PORT=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
		API_PORT=$${API_PORT:-8070}; \
		echo -n "  API        ($$API_PORT): " && \
		(curl -sf http://localhost:$$API_PORT/health | python3 -m json.tool --compact 2>/dev/null \
		&& echo -e ' $(GREEN)✔$(RESET)') \
		|| echo -e '$(RED)✘ unreachable$(RESET)'
	@CALCULATOR_PORT=$$(grep -E '^CALCULATOR_PORT=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
		CALCULATOR_PORT=$${CALCULATOR_PORT:-8000}; \
		echo -n "  Calculator ($$CALCULATOR_PORT): " && \
		(curl -sf http://localhost:$$CALCULATOR_PORT/health | python3 -m json.tool --compact 2>/dev/null \
		&& echo -e ' $(GREEN)✔$(RESET)') \
		|| echo -e '$(RED)✘ unreachable$(RESET)'
	@FRONTEND_PORT=$$(grep -E '^FRONTEND_PORT=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
		FRONTEND_PORT=$${FRONTEND_PORT:-5173}; \
		echo -n "  Frontend   ($$FRONTEND_PORT): " && \
		(curl -sf -o /dev/null http://localhost:$$FRONTEND_PORT/ \
		&& echo -e '$(GREEN)✔ ok$(RESET)') \
		|| echo -e '$(RED)✘ unreachable$(RESET)'
	@STREAMLIT_PORT=$$(grep -E '^STREAMLIT_PORT=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
		STREAMLIT_PORT=$${STREAMLIT_PORT:-8511}; \
		echo -n "  Streamlit  ($$STREAMLIT_PORT): " && \
		(curl -sf -o /dev/null http://localhost:$$STREAMLIT_PORT/ \
		&& echo -e '$(GREEN)✔ ok$(RESET)') \
		|| echo -e '$(RED)✘ unreachable$(RESET)'

shell-api: ## Open a bash shell in the API container
	$(COMPOSE_BASE) exec api bash

shell-frontend: ## Open a shell in the frontend container
	$(COMPOSE_BASE) exec frontend sh

db-shell: ## Open SQLite shell on the application database
	$(COMPOSE_BASE) exec api sqlite3 /app/backend/data/app.db

clean: ## Stop services and remove containers, volumes, and images
	@echo -e '$(RED)⚠  Removing all containers, volumes, and images...$(RESET)'
	$(COMPOSE_BASE) down -v --rmi local 2>/dev/null || true
	$(COMPOSE_DEV) down -v --rmi local 2>/dev/null || true
	$(COMPOSE_GPU) down -v --rmi local 2>/dev/null || true
	@echo -e '$(GREEN)✔ Clean complete$(RESET)'

clean-volumes: ## Remove named volumes only (preserves images)
	@echo -e '$(RED)⚠  Removing volumes...$(RESET)'
	$(COMPOSE_BASE) down -v

clean-images: ## Remove project images only (preserves volumes)
	@echo -e '$(RED)⚠  Removing images...$(RESET)'
	$(COMPOSE_BASE) down --rmi local

env: ## Copy .env.example → .env
	@if [ -f .env ]; then \
		echo -e '$(YELLOW).env already exists — skipping (delete it first to regenerate)$(RESET)'; \
	else \
		cp .env.example .env; \
		echo -e '$(GREEN)✔ Created .env from template — edit it with your API keys$(RESET)'; \
	fi

init: env build ## First-time setup: create .env, build images
	@echo ''
	@echo -e '$(GREEN)✔ Initialisation complete!$(RESET)'
	@echo -e '  1. Edit $(CYAN).env$(RESET) with your API keys'
	@echo -e '  2. Run  $(ORANGE)make dev$(RESET)  for daily work, $(ORANGE)make up-cpu$(RESET) for CPU prod, or $(ORANGE)make up$(RESET) only when GPU is needed'

# =============================================================================
#  Internal helpers
# =============================================================================

.PHONY: _ensure-env
_ensure-env:
	@if [ ! -f .env ]; then \
		echo -e '$(RED)✘ .env not found$(RESET)'; \
		echo -e '  Run $(ORANGE)make env$(RESET) to create it from the template'; \
		exit 1; \
	fi
