from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Play(Base):
    __tablename__ = "plays"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("games.id"), index=True)
    play_number: Mapped[int]
    sequence: Mapped[int]                     # ordering within game (for chart x-axis)
    quarter: Mapped[int]
    game_clock_seconds: Mapped[int]           # seconds remaining in quarter
    down: Mapped[int | None]
    yards_to_go: Mapped[int | None]
    yard_line_from_own: Mapped[int | None]    # 0–50 from own end zone
    posteam_abbr: Mapped[str | None]          # e.g. "CHI", "MIN"
    posteam_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"))
    defteam_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"))
    score_home: Mapped[int] = mapped_column(default=0)
    score_away: Mapped[int] = mapped_column(default=0)
    play_type: Mapped[str | None]
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="plays")  # noqa: F821
    raw: Mapped["PlayRaw | None"] = relationship(  # noqa: F821
        "PlayRaw", back_populates="play", uselist=False
    )
    wp_predictions: Mapped[list["WpPrediction"]] = relationship(  # noqa: F821
        "WpPrediction", back_populates="play"
    )

    def __repr__(self) -> str:
        return f"<Play game={self.game_id} seq={self.sequence} q{self.quarter}>"
