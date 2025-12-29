.PHONY: help install dev api web test lint docker-build docker-run deploy

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies
	pip install -e ".[dev]"
	cd web && npm install

dev:  ## Run both API and web in development
	@echo "Starting API on http://localhost:8000"
	@echo "Starting Web on http://localhost:3000"
	@make -j2 api web

api:  ## Run API server
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

web:  ## Run web frontend
	cd web && npm run dev

test:  ## Run tests
	pytest tests/ -v
	@python scripts/cleanup_test_data.py 2>/dev/null || true

test-cov:  ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html
	@python scripts/cleanup_test_data.py 2>/dev/null || true

cleanup-test-data:  ## Clean up test data from the database
	python scripts/cleanup_test_data.py

lint:  ## Run linters
	ruff check src/ api/
	cd web && npm run lint

format:  ## Format code
	black src/ api/ tests/
	ruff check --fix src/ api/

cli:  ## Run CLI (example: make cli CMD="search --markets indianapolis_in")
	python -m src.cli $(CMD)

# Docker commands
docker-build:  ## Build Docker images
	docker compose build

docker-run:  ## Run with Docker Compose
	docker compose up

docker-down:  ## Stop Docker containers
	docker compose down

# Deployment
deploy-api:  ## Deploy API to Fly.io
	fly deploy

deploy-web:  ## Deploy web to Fly.io
	cd web && fly deploy

deploy:  ## Deploy both to Fly.io
	@make deploy-api
	@make deploy-web
