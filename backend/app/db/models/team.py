from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    abbr: Mapped[str] = mapped_column(unique=True, index=True)  # e.g. "KC", "BUF"
    name: Mapped[str]                                            # e.g. "Kansas City Chiefs"
    conference: Mapped[str | None]                               # AFC / NFC
    division: Mapped[str | None]                                 # AFC West
    logo_url: Mapped[str | None]
    primary_color: Mapped[str | None]                            # hex "#E31837"
    secondary_color: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"<Team {self.abbr}>"
