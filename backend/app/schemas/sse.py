from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.db.models.game import GameStatus
from app.schemas.play import PlayRead
from app.schemas.shap import ShapFeature


class PlayUpdateEvent(BaseModel):
    event_type: Literal["play_update"] = "play_update"
    game_id: str
    play: PlayRead
    home_wp: float
    away_wp: float
    top_shap: list[ShapFeature]


class GameStatusEvent(BaseModel):
    event_type: Literal["game_status"] = "game_status"
    game_id: str
    status: GameStatus
    home_score: int
    away_score: int


class ReplayCompleteEvent(BaseModel):
    event_type: Literal["replay_complete"] = "replay_complete"
    game_id: str


SSEEvent = Annotated[
    PlayUpdateEvent | GameStatusEvent | ReplayCompleteEvent,
    Field(discriminator="event_type"),
]
