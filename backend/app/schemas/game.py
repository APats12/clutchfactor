from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.game import GameStatus
from app.schemas.team import TeamRead


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season: int
    week: int
    home_team: TeamRead
    away_team: TeamRead
    status: GameStatus
    nflfastr_game_id: str | None = None
    scheduled_at: datetime | None
    started_at: datetime | None
    final_home_score: int | None
    final_away_score: int | None
    venue: str | None
    # Live WP is injected by the service layer, not stored on the Game model
    home_wp: float | None = None
    away_wp: float | None = None


class GameDetail(GameRead):
    """Extended game info returned by GET /games/{id}."""
    play_count: int = 0
