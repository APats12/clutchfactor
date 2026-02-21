from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    abbr: str
    name: str
    conference: str | None
    division: str | None
    logo_url: str | None
    primary_color: str | None
    secondary_color: str | None
