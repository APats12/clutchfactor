from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GameStatus(str, enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    final = "final"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    season: Mapped[int] = mapped_column(index=True)
    week: Mapped[int]
    home_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    status: Mapped[GameStatus] = mapped_column(
        SAEnum(GameStatus, name="gamestatus"),
        default=GameStatus.scheduled,
        index=True,
    )
    nflfastr_game_id: Mapped[str | None] = mapped_column(index=True)
    scheduled_at: Mapped[datetime | None]
    started_at: Mapped[datetime | None]
    final_home_score: Mapped[int | None]
    final_away_score: Mapped[int | None]
    venue: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    home_team: Mapped["Team"] = relationship(  # noqa: F821
        "Team", foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(  # noqa: F821
        "Team", foreign_keys=[away_team_id]
    )
    plays: Mapped[list["Play"]] = relationship(  # noqa: F821
        "Play", back_populates="game", order_by="Play.sequence"
    )

    def __repr__(self) -> str:
        return f"<Game {self.id} season={self.season} week={self.week} status={self.status}>"
