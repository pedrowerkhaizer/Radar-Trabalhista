.PHONY: up down logs migrate test lint fmt install

# Docker
up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

# Database
migrate:
	docker compose -f infra/docker-compose.yml exec postgres psql -U postgres -d radar_trabalhista -f /docker-entrypoint-initdb.d/init.sql

# API (Python)
install-api:
	cd apps/api && uv sync

test-api:
	cd apps/api && uv run pytest --cov=. --cov-report=term-missing

lint-api:
	cd apps/api && uv run ruff check . && uv run mypy .

fmt-api:
	cd apps/api && uv run ruff format .

# ETL
install-etl:
	cd etl && uv sync

lint-etl:
	cd etl && uv run ruff check .

# Web (Node)
install-web:
	cd apps/web && npm install

test-web:
	cd apps/web && npm run test

lint-web:
	cd apps/web && npm run lint && npm run type-check

# All
install: install-api install-etl install-web

test: test-api test-web

lint: lint-api lint-etl lint-web

# dbt
dbt-run:
	cd dbt && dbt run

dbt-test:
	cd dbt && dbt test

dbt-docs:
	cd dbt && dbt docs generate && dbt docs serve
