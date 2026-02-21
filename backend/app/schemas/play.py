from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.shap import ShapFeature


class PlayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    play_number: int
    sequence: int
    quarter: int
    game_clock_seconds: int
    down: int | None
    yards_to_go: int | None
    yard_line_from_own: int | None
    score_home: int
    score_away: int
    play_type: str | None
    description: str | None
    posteam_abbr: str | None = None
    created_at: datetime


class PlayWpRead(PlayRead):
    """PlayRead extended with win-probability, SHAP data, and possession team."""
    home_wp: float
    away_wp: float
    top_shap: list[ShapFeature]
