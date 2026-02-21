from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.shap import ShapFeature


class PredictRequest(BaseModel):
    game_id: uuid.UUID
    down: int | None = Field(None, ge=1, le=4)
    yards_to_go: int | None = Field(None, ge=0, le=100)
    yardline_100: int | None = Field(None, ge=1, le=99, description="Distance from opponent end zone")
    qtr: int = Field(..., ge=1, le=5)
    game_seconds_remaining: int = Field(..., ge=0, le=3600)
    score_differential: int = Field(..., description="home_score - away_score")
    posteam_timeouts_remaining: int = Field(..., ge=0, le=3)
    defteam_timeouts_remaining: int = Field(..., ge=0, le=3)
    half_seconds_remaining: int = Field(..., ge=0, le=1800)
    spread_line: float | None = None


class PredictResponse(BaseModel):
    play_id: uuid.UUID
    home_wp: float
    away_wp: float
    model_version: str
    top_shap: list[ShapFeature]
    predicted_at: datetime
