"""Pydantic schemas for the three analytics features:
  - Momentum Swings
  - Clutch Index
  - Coach Decision Grades
"""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class PlayRef(BaseModel):
    """Minimal play reference used inside analytics objects."""
    play_id: uuid.UUID
    sequence: int
    quarter: int
    game_clock_seconds: int
    description: str | None


# ---------------------------------------------------------------------------
# 1. Momentum Swings
# ---------------------------------------------------------------------------

class MomentumSwing(BaseModel):
    rank: int
    play_ref: PlayRef
    wp_before: float
    wp_after: float
    delta_wp: float          # signed: positive = helped home
    magnitude: float         # abs(delta_wp)
    tag: str | None          # "turnover" | "touchdown" | "field_goal" | "fourth_down" | None
    is_turning_point: bool   # True only for rank == 1


class MomentumSwingsResponse(BaseModel):
    game_id: uuid.UUID
    swings: list[MomentumSwing]


# ---------------------------------------------------------------------------
# 2. Clutch Index
# ---------------------------------------------------------------------------

class ClutchPlay(BaseModel):
    rank: int
    play_ref: PlayRef
    delta_wp: float
    clutch_score: float
    time_factor: float
    close_factor: float
    score_diff: int           # home - away at the time of the play


class ClutchDrive(BaseModel):
    drive_number: int         # sequential within game (derived from possession flips)
    posteam_abbr: str | None
    clutch_total: float
    play_count: int


class ClutchTeamTotals(BaseModel):
    offense: float
    defense: float


class ClutchResponse(BaseModel):
    game_id: uuid.UUID
    top_plays: list[ClutchPlay]
    top_drives: list[ClutchDrive]
    team_totals: dict[str, ClutchTeamTotals]  # keys: "home" | "away"


# ---------------------------------------------------------------------------
# 3. Coach Decision Grades
# ---------------------------------------------------------------------------

class DecisionOption(BaseModel):
    wp: float
    detail: str | None = None      # e.g. "p_conv=0.63" or "expected_net=41 yds"


class CoachDecision(BaseModel):
    play_ref: PlayRef
    situation: str                  # "4th & 2 at OPP 43"
    actual_type: Literal["go_for_it", "punt", "field_goal"]
    actual_wp_after: float
    alternatives: dict[str, DecisionOption | None]  # key = action name
    best_action: str
    decision_delta: float           # actual_wp - best_wp  (≤ 0)
    grade: Literal["Optimal", "Questionable", "Bad", "Very Bad"]
    grade_emoji: str


class DecisionGradesResponse(BaseModel):
    game_id: uuid.UUID
    decisions: list[CoachDecision]
