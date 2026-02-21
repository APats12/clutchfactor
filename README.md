# ClutchFactor

**Real-time NFL win-probability with play-by-play SHAP explainability.**

Every play, ClutchFactor updates a live win-probability curve and surfaces the top model features driving the prediction — so you can see *why* the model thinks a team is about to win or lose, not just *that* it does.

**[Live Demo →](https://clutchfactor.vercel.app)**

---

## What it does

- **Live win-probability chart** — XGBoost model updates on every play, trained on 8 seasons of nflfastR play-by-play data (2016–2023)
- **SHAP explainability panel** — Tree SHAP surfaces the top 4 features driving each prediction (field position, score differential, Vegas spread, time remaining, etc.)
- **Momentum swings** — detects the biggest single-play WP shifts in the game
- **Clutch index** — identifies the highest-leverage moments by quarter
- **Decision grades** — grades 4th-down go/kick decisions against expected-value thresholds
- **Replay mode** — stream any historical game through the full prediction pipeline in real time

---

## Tech stack

| Layer | Technology |
|---|---|
| ML model | XGBoost + Platt/isotonic calibration (scikit-learn) |
| Explainability | SHAP TreeExplainer |
| Backend | FastAPI, SQLAlchemy (async), Alembic, Celery |
| Streaming | Server-Sent Events (SSE) |
| Database | PostgreSQL |
| Cache / broker | Redis |
| Frontend | React 18, TypeScript, Vite, Recharts, Zustand |
| Deployment | Railway (backend + DB + Redis) · Vercel (frontend) |

---

## Model

The model is an XGBoost binary classifier calibrated with isotonic regression. It predicts home-team win probability from 14 in-game features:

| Feature | Description |
|---|---|
| `down` / `yards_to_go` | Current down and distance |
| `yardline_100` | Field position (yards from opponent end zone) |
| `game_seconds_remaining` | Total time left |
| `half_seconds_remaining` | Time left in current half |
| `score_differential` | Home score − away score |
| `posteam_is_home` | Whether the possession team is the home team |
| `posteam_timeouts_remaining` | Timeouts for offensive team |
| `defteam_timeouts_remaining` | Timeouts for defensive team |
| `receive_2h_ko` | Whether possession team receives the 2nd-half kickoff |
| `spread_line` | Pre-game Vegas spread (positive = home favored) |
| `spread_time` *(derived)* | `spread_line × game_seconds_remaining / 3600` |
| `diff_time_ratio` *(derived)* | `score_differential × (1 − game_seconds_remaining / 3600)` |
| `ep` | Expected points for current possession |

Training data: nflfastR seasons 2016–2023 (~360k plays).

---

## Project structure

```
clutchfactor/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (games, predictions, replay, stream, admin)
│   │   ├── db/
│   │   │   ├── models/   # SQLAlchemy ORM models
│   │   │   ├── seed.py   # Database seeder (teams, demo games, model version)
│   │   │   └── base.py   # Engine + session factory
│   │   ├── ml/
│   │   │   ├── train.py       # XGBoost training + calibration
│   │   │   ├── features.py    # Feature extraction pipeline
│   │   │   ├── registry.py    # Model artifact loader + cache
│   │   │   └── evaluate.py    # Brier score, log-loss
│   │   └── services/
│   │       ├── prediction_service.py
│   │       ├── replay_service.py
│   │       └── shap_service.py
│   ├── alembic/          # Database migrations
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/
│       │   └── game-detail/  # WpChart, ShapPanel, MomentumPanel, ClutchPanel, etc.
│       ├── pages/            # GameList, GameDetail
│       └── api/              # Typed API client
├── ml/
│   ├── artifacts/        # Trained model files (.joblib) — committed to repo
│   ├── demo/             # Pre-extracted play-by-play CSVs for the 3 demo games
│   └── data/             # Full nflfastR season CSVs (gitignored, large)
├── infra/                # Postgres init.sql, Redis config
├── docker-compose.yml
└── Makefile
```

---

## Running locally

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- `make` (comes with macOS/Linux; Windows: use WSL or Git Bash)

### Quickstart (demo mode)

This uses the three pre-bundled game CSVs — no data download needed.

```bash
git clone https://github.com/APats12/clutchfactor.git
cd clutchfactor
make demo
```

`make demo` will:
1. Copy the three demo CSVs into `ml/data/`
2. Build and start all services (PostgreSQL, Redis, backend, frontend)
3. Seed the database with teams, game records, and the trained model version
4. Stream all three historical games through the prediction pipeline at 50× speed (~30 s)

Open **http://localhost:3000** and the games will be ready.

### Demo games

| Season | Game | Result |
|---|---|---|
| 2022 | AFC Championship — CIN @ KC | KC 23 · CIN 20 |
| 2023 | Week 18 — DAL @ WAS | DAL 38 · WAS 10 |
| 2025 | Week 3 — LAR @ PHI | PHI 33 · LAR 26 |

### Stopping

```bash
docker compose down
```

---

## Training your own model

To retrain on full play-by-play data:

```bash
# 1. Download nflfastR CSVs (seasons 2016–2025, ~2 GB)
make download-data

# 2. Train + calibrate + save artifact to ml/artifacts/
make train

# 3. Re-seed the database to register the new model version
make seed
```

---

## API reference

All endpoints are prefixed `/api/v1`. Full interactive docs at `/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/games` | List games (filter by `season`, `week`, `status`) |
| `GET` | `/games/{id}` | Game detail |
| `GET` | `/games/{id}/wp-history` | Full WP history for a completed game |
| `GET` | `/games/{id}/momentum-swings` | Top WP swings |
| `GET` | `/games/{id}/clutch` | Clutch-index moments |
| `GET` | `/games/{id}/decision-grades` | 4th-down decision grades |
| `GET` | `/stream/games/{id}` | SSE stream for live WP updates |
| `POST` | `/replay/{id}/start` | Start a historical replay |
| `POST` | `/replay/{id}/stop` | Stop an active replay |
| `GET` | `/models/current` | Active model version info |
| `POST` | `/predict` | One-off prediction from raw features |
| `POST` | `/admin/seed` | Re-run database seeder |

---

## Environment variables

The backend reads from `.env` (or Railway/Docker env vars). Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async Postgres connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for pub/sub |
| `MODEL_ARTIFACT_DIR` | `./ml/artifacts` | Directory containing `.joblib` model files |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | JSON array of allowed origins |
| `REPLAY_SPEED_PLAYS_PER_SEC` | `1.0` | Default replay speed |

Frontend reads `VITE_API_URL` — set to your backend's public URL in production (e.g., on Vercel: `https://clutchfactor-production.up.railway.app`).
