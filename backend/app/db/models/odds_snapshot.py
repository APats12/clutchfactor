from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("games.id"), index=True)
    provider: Mapped[str]
    home_ml: Mapped[float | None] = mapped_column(Float)    # moneyline
    away_ml: Mapped[float | None] = mapped_column(Float)
    home_spread: Mapped[float | None] = mapped_column(Float) # point spread
    snap_at: Mapped[datetime] = mapped_column(server_default=func.now())
