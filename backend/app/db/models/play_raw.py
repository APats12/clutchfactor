from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlayRaw(Base):
    __tablename__ = "play_raw"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    play_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plays.id"), unique=True, index=True
    )
    provider: Mapped[str]          # "developer_replay", "espn_live", etc.
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(server_default=func.now())

    play: Mapped["Play"] = relationship("Play", back_populates="raw")  # noqa: F821
