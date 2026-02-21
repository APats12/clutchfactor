.PHONY: dev dev-backend dev-frontend migrate migrate-down seed \
        train download-data build up down logs shell-backend shell-db lint test

ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
BACKEND_DIR := $(ROOT_DIR)backend
FRONTEND_DIR := $(ROOT_DIR)frontend

# ─── Dev (all services via Docker) ─────────────────────────
dev:
	docker compose -f docker-compose.yml -f docker-compose.override.yml up

dev-backend:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

# ─── Database ───────────────────────────────────────────────
migrate:
	cd $(BACKEND_DIR) && uv run alembic upgrade head

migrate-down:
	cd $(BACKEND_DIR) && uv run alembic downgrade -1

seed:
	cd $(BACKEND_DIR) && uv run python -m app.db.seed

# ─── ML ─────────────────────────────────────────────────────
download-data:
	cd $(ROOT_DIR) && uv run --directory $(BACKEND_DIR) python ml/scripts/download_pbp.py

train:
	cd $(BACKEND_DIR) && uv run python -m app.ml.train

# ─── Docker ─────────────────────────────────────────────────
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U cf -d clutchfactor

# ─── Quality ────────────────────────────────────────────────
lint:
	cd $(BACKEND_DIR) && uv run ruff check . && uv run ruff format --check .
	cd $(FRONTEND_DIR) && npm run lint

test:
	cd $(BACKEND_DIR) && uv run pytest
