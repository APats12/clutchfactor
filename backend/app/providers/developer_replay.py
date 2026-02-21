"""
DeveloperReplayAdapter

Reads a nflfastR play-by-play CSV, filters to a single game_id,
and yields normalised GameState dicts at a configurable rate.

nflfastR column mapping:
  qtr                          → quarter
  game_seconds_remaining       → game_seconds_remaining
  ydstogo / yards_to_go        → yards_to_go
  yardline_100                 → yardline_100
  down                         → down
  posteam                      → posteam_abbr
  defteam                      → defteam_abbr
  total_home_score             → score_home
  total_away_score             → score_away
  posteam_timeouts_remaining   → posteam_timeouts_remaining
  defteam_timeouts_remaining   → defteam_timeouts_remaining
  half_seconds_remaining       → half_seconds_remaining
  spread_line                  → spread_line
  play_type                    → play_type
  desc                         → description
  play_id / old_game_id        → used for sequence
"""
from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import AsyncIterator

import pandas as pd

from app.providers.base import DataProvider, GameState

logger = logging.getLogger(__name__)


def _safe_int(val) -> int | None:
    try:
        v = float(val)
        if math.isnan(v):
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_float(val) -> float | None:
    try:
        v = float(val)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def _safe_str(val) -> str | None:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    return str(val).strip() or None


class DeveloperReplayAdapter(DataProvider):
    def __init__(
        self,
        csv_path: str,
        nflfastr_game_id: str,
        plays_per_second: float = 1.0,
    ) -> None:
        logger.info(
            "Loading CSV %s, game_id=%s, speed=%.1f plays/s",
            csv_path, nflfastr_game_id, plays_per_second,
        )
        raw = pd.read_csv(csv_path, low_memory=False)

        # Filter to the requested game
        if "game_id" in raw.columns:
            self._df = raw[raw["game_id"] == nflfastr_game_id].copy()
        else:
            logger.warning("No 'game_id' column in CSV; using all rows.")
            self._df = raw.copy()

        if self._df.empty:
            raise ValueError(
                f"No plays found for game_id='{nflfastr_game_id}' in {csv_path}. "
                "Check the nflfastR game_id format (e.g. '2022_20_CIN_KC')."
            )

        self._df = self._df.reset_index(drop=True)
        self._nflfastr_game_id = nflfastr_game_id
        self._speed = plays_per_second
        logger.info("Loaded %d plays for game %s", len(self._df), nflfastr_game_id)

    def _normalize(self, row: pd.Series, sequence: int) -> GameState:
        # Resolve yard_line columns
        yardline_100 = _safe_int(row.get("yardline_100"))
        yard_line_from_own = (100 - yardline_100) if yardline_100 is not None else None

        # Score — always home perspective (consistent with training labels)
        score_home = _safe_int(row.get("total_home_score")) or 0
        score_away = _safe_int(row.get("total_away_score")) or 0
        score_differential = score_home - score_away

        # Clock
        game_secs = _safe_int(row.get("game_seconds_remaining")) or 0
        half_secs = _safe_int(row.get("half_seconds_remaining")) or 0
        game_clock_secs = _safe_int(row.get("quarter_seconds_remaining")) or 0

        # Yards to go (nflfastR uses "ydstogo" historically)
        yards_to_go = _safe_int(row.get("yards_to_go")) or _safe_int(row.get("ydstogo"))

        # Possession features
        posteam = _safe_str(row.get("posteam"))
        home_team = _safe_str(row.get("home_team"))
        posteam_is_home = int(
            posteam is not None and home_team is not None and posteam == home_team
        )

        # receive_2h_ko: 1 if the possession team will receive the 2nd-half kickoff.
        # Formula: home_opening_kickoff XOR posteam_is_home
        # (if home got the opening kick, away gets 2nd half; if away got it, home gets 2nd half)
        home_opening_kickoff = _safe_int(row.get("home_opening_kickoff")) or 0
        receive_2h_ko = int(home_opening_kickoff != posteam_is_home)

        return GameState(
            game_id=self._nflfastr_game_id,
            play_number=int(row.name) + 1,
            sequence=sequence,
            quarter=_safe_int(row.get("qtr")) or 1,
            game_clock_seconds=game_clock_secs,
            down=_safe_int(row.get("down")),
            yards_to_go=yards_to_go,
            yardline_100=yardline_100,
            yard_line_from_own=yard_line_from_own,
            score_home=score_home,
            score_away=score_away,
            score_differential=score_differential,
            posteam_abbr=posteam,
            defteam_abbr=_safe_str(row.get("defteam")),
            posteam_is_home=posteam_is_home,
            receive_2h_ko=receive_2h_ko,
            posteam_timeouts_remaining=_safe_int(row.get("posteam_timeouts_remaining")) or 3,
            defteam_timeouts_remaining=_safe_int(row.get("defteam_timeouts_remaining")) or 3,
            game_seconds_remaining=game_secs,
            half_seconds_remaining=half_secs,
            spread_line=_safe_float(row.get("spread_line")),
            ep=_safe_float(row.get("ep")),
            play_type=_safe_str(row.get("play_type")),
            description=_safe_str(row.get("desc")),
            raw_payload=row.to_dict(),
        )

    async def stream_plays(self, game_id: str) -> AsyncIterator[GameState]:  # type: ignore[override]
        delay = 1.0 / self._speed
        for seq, (_, row) in enumerate(self._df.iterrows()):
            yield self._normalize(row, sequence=seq)
            await asyncio.sleep(delay)

    async def get_game_metadata(self, game_id: str) -> dict:
        if self._df.empty:
            return {}
        first = self._df.iloc[0]
        return {
            "game_id": game_id,
            "home_team": _safe_str(first.get("home_team")),
            "away_team": _safe_str(first.get("away_team")),
            "season": _safe_int(first.get("season")),
            "week": _safe_int(first.get("week")),
            "total_plays": len(self._df),
        }
