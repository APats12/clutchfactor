<div align="center">
  <h1>🏈 ClutchFactor</h1>
  <p><strong>Real-time NFL win-probability with play-by-play SHAP explainability.</strong></p>

  <a href="https://clutchfactor.vercel.app">
    <img src="https://img.shields.io/badge/🚀%20Live%20Demo-000000?style=for-the-badge&logo=vercel&logoColor=white" height="35px" alt="Live Demo">
  </a>
</div>

<h1></h1>

Every play, ClutchFactor updates a live win-probability curve and surfaces the top model features driving the prediction — so you can see *why* the model thinks a team is about to win or lose, not just *that* it does.

---

## How It Works

ClutchFactor runs a full ML inference pipeline on every play:

1. Raw play-by-play data is passed through a **14-feature extraction pipeline**
2. An **XGBoost classifier** (calibrated with isotonic regression) predicts home win probability
3. **Tree SHAP** computes the top 4 features explaining each prediction
4. Updates are broadcast to the frontend in real time via **Server-Sent Events**

```
Play Data → Feature Extraction → XGBoost → Win Probability
                                     ↓
                               SHAP Values → Explainability Panel
                                     ↓
                              SSE Broadcast → Live Chart
```

---

## ✅ Features

- ✅ **Live win-probability chart** — XGBoost model updates on every play, trained on 8 seasons of nflfastR data (2016–2023, ~360K plays)
- ✅ **SHAP explainability panel** — Tree SHAP surfaces the top 4 features driving each prediction
- ✅ **Momentum swings** — detects the biggest single-play WP shifts in the game
- ✅ **Clutch index** — identifies the highest-leverage moments by quarter
- ✅ **Decision grades** — grades 4th-down go/kick decisions against expected-value thresholds
- ✅ **Replay mode** — stream any historical game through the full prediction pipeline in real time
- ✅ **Full API** — FastAPI backend with Swagger docs at `/docs`

---

## 🧠 The Model

XGBoost binary classifier calibrated with isotonic regression, predicting home-team win probability from 14 in-game features:

| Feature | Description |
|---------|-------------|
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

**Training data:** nflfastR seasons 2016–2023 · ~360,000 plays

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Model | XGBoost + Platt/isotonic calibration (scikit-learn) |
| Explainability | SHAP TreeExplainer |
| Backend | FastAPI, SQLAlchemy (async), Alembic, Celery |
| Streaming | Server-Sent Events (SSE) |
| Database | PostgreSQL |
| Cache / Broker | Redis |
| Frontend | React 18, TypeScript, Vite, Recharts, TailwindCSS |
| Deployment | Railway (backend + DB + Redis) · Vercel (frontend) |

---

## 🚀 Run Locally

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- `make` (comes with macOS/Linux; Windows: use WSL or Git Bash)

### Quickstart (Demo Mode)

This uses three pre-bundled game CSVs — no data download needed.

```bash
git clone https://github.com/APats12/clutchfactor.git
cd clutchfactor
make demo
```

`make demo` will:
1. Copy the three demo CSVs into `ml/data/`
2. Build and start all 5 services (PostgreSQL, Redis, backend, Celery worker, frontend)
3. Seed the database with teams, game records, and the trained model version
4. Stream all three historical games through the prediction pipeline at 50× speed (~30s)

Open **http://localhost:3000** — games will be ready.

```bash
docker compose down   # stop everything
```

### Demo Games

| Season | Game | Result |
|--------|------|--------|
| 2022 | AFC Championship — CIN @ KC | KC 23 · CIN 20 |
| 2023 | Week 18 — DAL @ WAS | DAL 38 · WAS 10 |
| 2025 | Week 3 — LAR @ PHI | PHI 33 · LAR 26 |

---

## 📬 Training Your Own Model

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

## 🗂️ Project Structure

```
clutchfactor/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers (games, predictions, replay, stream, admin)
│   │   ├── db/
│   │   │   ├── models/       # SQLAlchemy ORM models
│   │   │   ├── seed.py       # Database seeder (teams, demo games, model version)
│   │   │   └── base.py       # Engine + session factory
│   │   ├── ml/
│   │   │   ├── train.py      # XGBoost training + calibration
│   │   │   ├── features.py   # Feature extraction pipeline
│   │   │   ├── registry.py   # Model artifact loader + cache
│   │   │   └── evaluate.py   # Brier score, log-loss
│   │   └── services/
│   │       ├── prediction_service.py
│   │       ├── replay_service.py
│   │       ├── shap_service.py
│   │       ├── analytics_service.py  # Momentum, clutch, decision grades
│   │       └── sse_manager.py        # SSE connection management
│   ├── alembic/              # Database migrations
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/
│       │   └── game-detail/  # WpChart, ShapPanel, MomentumPanel, ClutchPanel, etc.
│       ├── pages/            # GamesPage, GameDetailPage
│       └── api/              # Typed API client (Axios + React Query)
├── ml/
│   ├── artifacts/            # Trained model files (.joblib) — committed to repo
│   ├── demo/                 # Pre-extracted play-by-play CSVs for 3 demo games
│   └── data/                 # Full nflfastR season CSVs (gitignored, ~2 GB)
├── infra/                    # Postgres init.sql, Redis config
├── docker-compose.yml        # 5 services: postgres, redis, backend, celery-worker, frontend
└── Makefile                  # Build, run, seed, train, lint commands
```

---

## 📡 API Reference

All endpoints are prefixed `/api/v1`. Interactive docs at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/games` | List games (filter by `season`, `week`, `status`, `date`) |
| `GET` | `/games/{id}` | Game detail with teams, score, status |
| `GET` | `/games/{id}/plays` | All plays for a game |
| `GET` | `/games/{id}/wp-history` | Full WP history with SHAP data |
| `GET` | `/games/{id}/momentum-swings` | Top N plays by WP swing magnitude |
| `GET` | `/games/{id}/clutch` | Clutch play rankings by quarter |
| `GET` | `/games/{id}/decision-grades` | 4th-down decision grades |
| `GET` | `/stream/games/{id}` | SSE stream for live WP updates |
| `POST` | `/replay/{id}/start` | Start a historical replay |
| `POST` | `/replay/{id}/stop` | Stop an active replay |
| `GET` | `/models/current` | Active model version info |
| `POST` | `/predict` | One-off prediction from raw features |
| `POST` | `/admin/seed` | Re-run database seeder |

---

## 🔑 Environment Variables

The backend reads from `.env` (or Railway/Docker env). Copy `.env.example` to get started.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async Postgres connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for pub/sub and Celery |
| `MODEL_ARTIFACT_DIR` | `./ml/artifacts` | Directory containing `.joblib` model files |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | JSON array of allowed origins |
| `REPLAY_SPEED_PLAYS_PER_SEC` | `1.0` | Default replay speed |

Frontend: set `VITE_API_URL` on Vercel to your backend's public URL (e.g., `https://clutchfactor-production.up.railway.app`).
