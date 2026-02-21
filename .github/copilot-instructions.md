# GitHub Copilot Instructions for ClutchFactor

## 🏗 Architecture Overview
ClutchFactor is an NFL live win-probability app (monorepo: `backend/`, `frontend/`, `ml/`). The core loop is:

```
Replay/Live Provider → ReplayService → DB (PostgreSQL) + Redis cache
                                     → PredictionService (XGBoost)
                                     → ShapService (TreeExplainer)
                                     → SSEConnectionManager.broadcast()
                                     → Frontend EventSource listener
```

- **Backend:** Python 3.12, FastAPI (async), SQLAlchemy AsyncIO, Celery, Redis
- **Frontend:** React 18, Vite, TypeScript, TailwindCSS, TanStack Query, Recharts
- **ML:** XGBoost (`binary:logistic`), SHAP `TreeExplainer`
- **Infra:** Docker Compose, PostgreSQL 16, Redis 7

## 🛠 Developer Workflow
**Always prefer `make` commands.**

| Task | Command |
|---|---|
| Full stack (Docker) | `make dev` |
| Backend only (local) | `make dev-backend` |
| Frontend only (local) | `make dev-frontend` |
| DB migrations | `make migrate` |
| Seed DB | `make seed` |
| Train ML model | `make train` |
| DB shell | `make shell-db` |

- `make dev` uses both `docker-compose.yml` + `docker-compose.override.yml` — override enables hot-reload and dev Vite server on `:5173`
- `make dev-backend` requires `uv` installed locally; Docker containers use plain `pip`
- After `make train`, run `make migrate && make seed` to register the new model in the DB

## 🐍 Backend Patterns

**Configuration:** Always use `app.config.get_settings()` (pydantic-settings). Never import env vars directly.

**DB sessions:** Use `DbSession` from `app.deps` (FastAPI `Depends`). For long-running tasks (e.g. Celery, `ReplayService`), create a standalone session via `get_session_factory()` from `app.db.base` — see `replay_service.py` for the pattern.

**Real-time (SSE only):** Do not use WebSockets. Use the `sse_manager` singleton from `app.services.sse_manager`:
- `await sse_manager.subscribe(game_id)` → returns `asyncio.Queue`
- `await sse_manager.broadcast(game_id, event_dict)` → fans out to all subscribers
- New SSE clients receive the latest cached event immediately from Redis (`app.utils.cache`), then queue-based live updates.

**SSE event types** (defined in `app.schemas.sse`): `play_update`, `game_status`, `replay_complete` — discriminated union via `event_type` field.

**Replay vs. Live mode:** The app currently ships with `DeveloperReplayAdapter` (`app.providers.developer_replay`) as the only data provider. It reads nflfastR play-by-play CSVs from `ml/data/`. A commercial live-feed provider would implement `app.providers.base.DataProvider` and be swapped in. The `ReplayService` is the orchestrator that connects provider → DB → prediction → SHAP → SSE.

## 🤖 ML Pipeline

**Feature columns** are defined in `app.ml.features.FEATURE_COLS` (10 features, order matters — reordering requires retraining):
`down`, `yards_to_go`, `yardline_100`, `qtr`, `game_seconds_remaining`, `score_differential`, `posteam_timeouts_remaining`, `defteam_timeouts_remaining`, `half_seconds_remaining`, `spread_line`

**Model registry:** `app.ml.registry.get_current()` lazily loads the model from the path stored in the `model_versions` DB table and caches it in-process. Call `registry.invalidate()` to force a reload after training.

**SHAP:** `ShapService` builds a `TreeExplainer` once and caches it by model object `id`. Returns top-N `ShapFeature` objects sorted by `abs(shap_value)`. Each `ShapFeature` includes `display_name` (human-readable) and `direction` (`positive`/`negative`).

**Artifacts:** `ml/artifacts/` (repo root) is volume-mounted into Docker as `/artifacts`. The backend reads `settings.model_artifact_dir` to locate `.ubj` files.

**Async SHAP (Celery):** In live mode, `compute_shap_async` Celery task handles SHAP compute out-of-band. In replay mode, SHAP runs synchronously in the `ReplayService` loop (fast enough at <10ms/play).

## ⚛️ Frontend Patterns

**State management:** `TanStack Query` for all REST data (`useGame`, `useGames`, `usePlays`). SSE state is managed via `useReducer` in `useGameStream` — the reducer is in `src/store/gameStreamSlice`.

**SSE hook:** `useGameStream(gameId)` — opens a native `EventSource`, dispatches typed `SSEEvent` actions into `gameStreamReducer`. Reconnects automatically on error.

**WP chart:** `WpChart` uses Recharts `AreaChart`. Supports `onPlaySelect` callback to drive SHAP panel (`ShapPanel`) selection.

**SHAP panel:** `ShapPanel` renders a horizontal `BarChart` colored by team `primary_color`. Shows "Why it changed" per-play attribution.

## 📐 DB Schema (key tables)
`teams` → `games` → `plays` → `wp_predictions` → `shap_values`
Also: `play_raw` (raw provider payload JSONB), `game_state_snapshots`, `model_versions`, `odds_snapshots`

## ❌ What Is NOT Yet Implemented (vs. MVP spec)
- **Live ingestion** — only `DeveloperReplayAdapter` (CSV replay) exists; no commercial feed adapter
- **Odds integration** — `odds_snapshots` table exists but no ingestion; `spread_line` defaults to `0.0`
- **`/games/{id}/plays?since_play_seq=`** incremental param — endpoint exists but no `since` filter
- **Key play markers** (turnovers, 4th-down badges) — schema supports it; no UI rendering
- **Rate limiting / JWT auth** — CORS configured; no auth middleware on endpoints yet
- **Baseline logistic regression model** — only XGBoost is trained; no LR baseline for comparison
