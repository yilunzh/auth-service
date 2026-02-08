.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

.PHONY: up down logs build clean

up: ## Start all services (docker-compose up -d)
	docker compose up -d --build

down: ## Stop all services
	docker compose down

logs: ## Tail service logs
	docker compose logs -f

build: ## Build the Docker image
	docker build -t auth-service .

clean: ## Remove containers, volumes, and dangling images
	docker compose down -v --remove-orphans
	docker image prune -f

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

.PHONY: test test-unit test-integration

test: ## Run all tests (unit + integration — requires MySQL)
	python -m pytest tests/ -v

test-unit: ## Run unit tests only (no DB required)
	python -m pytest tests/unit -v

test-integration: ## Run integration tests (starts MySQL via docker-compose, runs on host)
	docker compose up -d mysql
	@echo "Waiting for MySQL to be healthy..."
	@until docker compose exec mysql mysqladmin ping -h localhost --silent 2>/dev/null; do \
		sleep 1; \
	done
	@echo "MySQL is ready."
	python -m pytest tests/integration -v

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

.PHONY: lint format

lint: ## Run ruff linter
	python -m ruff check .

format: ## Auto-format code with ruff
	python -m ruff format .

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
		/^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
