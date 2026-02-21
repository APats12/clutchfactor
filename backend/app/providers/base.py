from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TypedDict


class GameState(TypedDict, total=False):
    """Normalised play dict passed to the prediction pipeline."""
    game_id: str
    play_number: int
    sequence: int
    quarter: int
    game_clock_seconds: int
    down: int | None
    yards_to_go: int | None
    yardline_100: int | None          # distance from opponent end zone (1–99)
    yard_line_from_own: int | None    # 0–50 from own end zone (for DB storage)
    score_home: int
    score_away: int
    score_differential: int           # home_score - away_score (always home perspective)
    posteam_abbr: str | None
    defteam_abbr: str | None
    posteam_is_home: int              # 1 if possession team is home team, else 0
    receive_2h_ko: int                # 1 if possession team will receive 2nd-half kickoff
    posteam_timeouts_remaining: int
    defteam_timeouts_remaining: int
    game_seconds_remaining: int
    half_seconds_remaining: int
    spread_line: float | None
    ep: float | None                  # expected points for current possession
    play_type: str | None
    description: str | None
    raw_payload: dict                 # full source row (stored in play_raw)


class DataProvider(ABC):
    @abstractmethod
    def stream_plays(self, game_id: str) -> AsyncIterator[GameState]:
        """Yield GameState dicts one play at a time."""
        ...

    @abstractmethod
    async def get_game_metadata(self, game_id: str) -> dict:
        """Return basic game info (teams, schedule) if available."""
        ...
