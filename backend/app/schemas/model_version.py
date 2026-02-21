from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    brier_score: float | None
    log_loss_val: float | None
    trained_on_seasons: list[str] | None
    is_current: bool
    created_at: datetime
