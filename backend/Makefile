# Makefile for RapidRole Backend Development

.PHONY: help build up down restart logs shell db-shell redis-shell test migrate clean

# Default target
help:
	@echo "RapidRole Backend - Development Commands"
	@echo ""
	@echo "Setup & Run:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make up-dev         - Start with development tools (pgAdmin, Redis Commander)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo ""
	@echo "Logs & Monitoring:"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-api       - View API logs only"
	@echo "  make logs-db        - View database logs only"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell          - Open shell in API container"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make redis-shell    - Open Redis CLI"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make db-reset       - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-api       - Run API tests only"
	@echo "  make test-cov       - Run tests with coverage"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make verify         - Verify setup"
	@echo "  make health         - Check service health"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Services started! API available at http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Health Check: http://localhost:8000/health"

# Start with development tools
up-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "Development services started!"
	@echo "API: http://localhost:8000/docs"
	@echo "pgAdmin: http://localhost:5050 (admin@rapidrole.com / admin)"
	@echo "Redis Commander: http://localhost:8081"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-db:
	docker-compose logs -f postgres

# Shell access
shell:
	docker-compose exec api /bin/bash

db-shell:
	docker-compose exec postgres psql -U postgres -d job_copilot

redis-shell:
	docker-compose exec redis redis-cli

# Database migrations
migrate:
	docker-compose exec api uv run alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec api uv run alembic revision --autogenerate -m "$$msg"

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		docker-compose up -d api; \
	fi

# Testing
test:
	docker-compose exec api uv run pytest tests/ -v

test-api:
	docker-compose exec api uv run pytest tests/test_api.py -v

test-cov:
	docker-compose exec api uv run pytest tests/ --cov=. --cov-report=html --cov-report=term

# Utilities
clean:
	docker-compose down -v
	docker system prune -f

verify:
	docker-compose exec api ./scripts/verify.sh

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"
	@docker-compose exec postgres pg_isready -U postgres || echo "PostgreSQL not ready"
	@docker-compose exec redis redis-cli ping || echo "Redis not responding"
