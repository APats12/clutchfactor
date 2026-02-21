.PHONY: dev dev-backend dev-frontend migrate migrate-down seed demo demo-setup \
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

# ─── Demo (local quickstart with bundled game data) ─────────
demo-setup:
	@echo "Copying demo CSVs into ml/data/ ..."
	cp ml/demo/*.csv ml/data/

demo: demo-setup
	@echo "Starting all services ..."
	docker compose up -d --build
	@echo "Waiting for backend to be ready ..."
	@until curl -sf http://localhost:8000/api/v1/health > /dev/null; do sleep 2; done
	@echo "Seeding database ..."
	curl -sf -X POST http://localhost:8000/api/v1/admin/seed
	@echo "Running replays for all 3 demo games (this takes ~30 s) ..."
	curl -sf -X POST "http://localhost:8000/api/v1/replay/00000000-0000-0000-0000-000000000001/start?csv_filename=cin_kc_2022.csv&nflfastr_game_id=2022_21_CIN_KC&speed=50"
	curl -sf -X POST "http://localhost:8000/api/v1/replay/00000000-0000-0000-0000-000000000002/start?csv_filename=sample_game.csv&nflfastr_game_id=2023_18_DAL_WAS&speed=50"
	curl -sf -X POST "http://localhost:8000/api/v1/replay/00000000-0000-0000-0000-000000000003/start?csv_filename=la_phi_2025.csv&nflfastr_game_id=2025_03_LA_PHI&speed=50"
	@echo ""
	@echo "Done! Open http://localhost:3000"

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
