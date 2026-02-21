from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.services.prediction_service import PredictionService
from app.services.replay_service import ReplayService
from app.services.shap_service import ShapService

router = APIRouter(tags=["replay"])

# Active replay tasks: game_id → asyncio.Task
_active_replays: dict[str, asyncio.Task] = {}


@router.post("/replay/{game_id}/start")
async def start_replay(
    game_id: str,
    csv_filename: str = Query(..., description="CSV filename inside ml/data/, e.g. play_by_play_2022.csv"),
    nflfastr_game_id: str = Query(..., description="The game_id string in the nflfastR CSV to replay"),
    speed: float = Query(default=1.0, ge=0.1, le=100.0, description="Plays per second"),
) -> dict:
    if game_id in _active_replays and not _active_replays[game_id].done():
        raise HTTPException(status_code=409, detail=f"Replay already running for game {game_id}")

    settings = get_settings()

    # Prevent path traversal
    if ".." in csv_filename or os.sep in csv_filename:
        raise HTTPException(status_code=400, detail="Invalid csv_filename")

    csv_path = Path("/ml/data") / csv_filename
    if not csv_path.exists():
        # Fall back to relative path for local dev
        csv_path = Path(settings.model_artifact_dir).parent / "data" / csv_filename
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"CSV not found: {csv_filename}")

    from app.providers.developer_replay import DeveloperReplayAdapter

    adapter = DeveloperReplayAdapter(str(csv_path), nflfastr_game_id=nflfastr_game_id, plays_per_second=speed)
    svc = ReplayService(
        adapter=adapter,
        prediction_service=PredictionService(),
        shap_service=ShapService(),
    )

    task = asyncio.create_task(svc.run(game_id))
    _active_replays[game_id] = task

    return {"status": "started", "game_id": game_id, "csv": csv_filename, "speed": speed}


@router.post("/replay/{game_id}/stop")
async def stop_replay(game_id: str) -> dict:
    task = _active_replays.get(game_id)
    if task is None or task.done():
        raise HTTPException(status_code=404, detail=f"No active replay for game {game_id}")
    task.cancel()
    _active_replays.pop(game_id, None)
    return {"status": "stopped", "game_id": game_id}
