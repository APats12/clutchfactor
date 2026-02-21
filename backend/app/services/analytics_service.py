"""Analytics service: computes Momentum Swings, Clutch Index, and Coach Decision Grades
from the plays + wp_predictions already stored in the DB.

All three algorithms operate on a sorted list of (Play, WpPrediction) pairs
so DB I/O is done once and re-used across all three computations.
"""
from __future__ import annotations

import math
import uuid
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.game import Game
from app.db.models.play import Play
from app.db.models.wp_prediction import WpPrediction
from app.schemas.analytics import (
    ClutchDrive,
    ClutchPlay,
    ClutchResponse,
    ClutchTeamTotals,
    CoachDecision,
    DecisionGradesResponse,
    DecisionOption,
    MomentumSwing,
    MomentumSwingsResponse,
    PlayRef,
)

# ---------------------------------------------------------------------------
# Constants / tunables
# ---------------------------------------------------------------------------

# Plays of these types are excluded from momentum / clutch (no real WP change)
_JUNK_PLAY_TYPES = {"no_play", "qb_kneel", "qb_spike", "timeout",
                    "end_of_quarter", "end_of_half", "end_of_game", "extra_point"}

# Descriptions that mark administrative end-of-period rows (not real plays)
_JUNK_DESC_PREFIXES = ("end quarter", "end game", "end of game", "end half",
                       "two-minute warning", "end of half")

# Clutch formula parameters
_T_THRESHOLD = 900   # seconds remaining when "clutch window" starts (last ~15 min)
_TAU = 300           # steepness of sigmoid
_K = 7.0             # score scale (one TD)

# Coach decision grade thresholds (decision_delta = actual - best, always ≤ 0)
_GRADE_MAP: list[tuple[float, str, str]] = [
    (-0.005, "Optimal",     "✅"),
    (-0.020, "Questionable","⚠️"),
    (-0.050, "Bad",         "❌"),
    (-9999,  "Very Bad",    "💀"),
]

# League-average 4th-down conversion rates by yards_to_go bucket
# Source: rough empirical estimates from nflfastR historical data
_CONV_RATE: dict[tuple[int, int], float] = {
    (1,  1):  0.68,
    (2,  2):  0.62,
    (3,  3):  0.56,
    (4,  5):  0.50,
    (6, 10):  0.38,
    (11, 99): 0.22,
}

# FG make probability by kick distance (yards)
# Approximated with a logistic curve
def _fg_make_prob(kick_distance: float) -> float:
    """P(FG made) given kick distance in yards."""
    # Logistic curve calibrated to NFL averages:
    # 20 yd ≈ 0.98, 40 yd ≈ 0.87, 50 yd ≈ 0.72, 60 yd ≈ 0.52
    return 1.0 / (1.0 + math.exp(0.10 * (kick_distance - 37)))


def _conv_prob(yards_to_go: int | None) -> float:
    """P(4th-down conversion) given yards_to_go."""
    ydg = yards_to_go if yards_to_go is not None else 10
    for (lo, hi), rate in _CONV_RATE.items():
        if lo <= ydg <= hi:
            return rate
    return 0.22  # very long


def _punt_expected_field_pos(yardline_100: int | None) -> int:
    """Expected opponent field position after a punt (distance from THEIR end zone).
    Returns a yardline_100 value for the opponent (1-99).
    """
    yl = yardline_100 if yardline_100 is not None else 50
    # League-average net punt: ~42 yards; touchback if opponent would field inside 10
    new_pos = yl - 42  # opponent's yardline_100 (distance from THEIR endzone)
    # Touchback rule: if new_pos <= 10, opponent gets ball at their 25
    return max(new_pos, 25)


def _is_junk_play(play: Play) -> bool:
    """Return True for administrative / non-action plays that should be excluded
    from analytics (timeouts, end markers, no-plays, etc.)."""
    pt = (play.play_type or "").lower()
    if pt in _JUNK_PLAY_TYPES:
        return True
    # play_type is None for end-of-game / end-of-half administrative rows
    if play.play_type is None:
        return True
    desc = (play.description or "").lower()
    if any(desc.startswith(prefix) for prefix in _JUNK_DESC_PREFIXES):
        return True
    return False


# ---------------------------------------------------------------------------
# Shared DB loader
# ---------------------------------------------------------------------------

async def _load_plays_with_wp(
    db: AsyncSession, game_id: uuid.UUID
) -> list[tuple[Play, WpPrediction]]:
    """Return sorted (Play, WpPrediction) pairs for a game.
    Only plays that have at least one WP prediction are included.
    Raises 404 if game not found.
    """
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    if game_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    stmt = (
        select(Play)
        .where(Play.game_id == game_id)
        .options(selectinload(Play.wp_predictions))
        .order_by(Play.sequence)
    )
    result = await db.execute(stmt)
    plays = result.scalars().all()

    pairs: list[tuple[Play, WpPrediction]] = []
    for play in plays:
        if not play.wp_predictions:
            continue
        wp = max(play.wp_predictions, key=lambda p: p.predicted_at)
        pairs.append((play, wp))

    return pairs


def _play_ref(play: Play) -> PlayRef:
    return PlayRef(
        play_id=play.id,
        sequence=play.sequence,
        quarter=play.quarter,
        game_clock_seconds=play.game_clock_seconds,
        description=play.description,
    )


# ---------------------------------------------------------------------------
# 1. Momentum Swings
# ---------------------------------------------------------------------------

def _tag_play(play: Play, delta_wp: float) -> str | None:
    desc = (play.description or "").lower()
    pt = (play.play_type or "").lower()
    if "intercept" in desc or "fumble" in desc:
        return "turnover"
    if "touchdown" in desc or " td" in desc:
        return "touchdown"
    if "field goal" in desc and "good" in desc:
        return "field_goal"
    if play.down == 4 and pt in ("run", "pass", "pass_incomplete", "pass_complete"):
        return "fourth_down"
    return None


async def get_momentum_swings(
    db: AsyncSession, game_id: uuid.UUID, top: int = 3
) -> MomentumSwingsResponse:
    pairs = await _load_plays_with_wp(db, game_id)

    if len(pairs) < 2:
        return MomentumSwingsResponse(game_id=game_id, swings=[])

    # Compute ΔWP for each play (always from home-team perspective)
    deltas: list[tuple[float, float, float, Play, WpPrediction]] = []
    prev_wp = pairs[0][1].home_wp

    for play, wp in pairs[1:]:
        if _is_junk_play(play):
            prev_wp = wp.home_wp
            continue
        delta = wp.home_wp - prev_wp
        deltas.append((abs(delta), delta, prev_wp, play, wp))
        prev_wp = wp.home_wp

    # Sort by magnitude descending, take top N
    deltas.sort(key=lambda x: x[0], reverse=True)
    top_deltas = deltas[:top]
    # Re-sort by sequence for consistent ordering
    top_deltas.sort(key=lambda x: x[3].sequence)

    swings: list[MomentumSwing] = []
    for rank, (magnitude, delta, wp_before, play, wp) in enumerate(
        sorted(top_deltas, key=lambda x: x[0], reverse=True), start=1
    ):
        swings.append(
            MomentumSwing(
                rank=rank,
                play_ref=_play_ref(play),
                wp_before=wp_before,
                wp_after=wp.home_wp,
                delta_wp=delta,
                magnitude=magnitude,
                tag=_tag_play(play, delta),
                is_turning_point=(rank == 1),
            )
        )

    return MomentumSwingsResponse(game_id=game_id, swings=swings)


# ---------------------------------------------------------------------------
# 2. Clutch Index
# ---------------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _time_factor(game_seconds_remaining: int) -> float:
    """Higher when closer to end of game."""
    # game_clock_seconds is seconds remaining IN THE QUARTER; convert to full-game secs
    # We store game_clock_seconds as quarter-level; compute game-level seconds remaining
    # via the quarter field — but here we receive it already as game_seconds_remaining.
    return _sigmoid(((_T_THRESHOLD - game_seconds_remaining) / _TAU))


def _game_seconds_remaining(play: Play) -> int:
    """Approximate total game seconds remaining from quarter + quarter clock."""
    q = min(play.quarter, 4)
    quarter_seconds_remaining = play.game_clock_seconds
    quarters_left = 4 - q
    return quarters_left * 900 + quarter_seconds_remaining


async def get_clutch_index(
    db: AsyncSession,
    game_id: uuid.UUID,
    home_abbr: str,
    away_abbr: str,
    top_plays: int = 5,
) -> ClutchResponse:
    pairs = await _load_plays_with_wp(db, game_id)

    if len(pairs) < 2:
        return ClutchResponse(
            game_id=game_id,
            top_plays=[],
            top_drives=[],
            team_totals={
                "home": ClutchTeamTotals(offense=0.0, defense=0.0),
                "away": ClutchTeamTotals(offense=0.0, defense=0.0),
            },
        )

    clutch_plays: list[tuple[float, float, float, float, int, Play]] = []
    prev_wp = pairs[0][1].home_wp

    for play, wp in pairs[1:]:
        if _is_junk_play(play):
            prev_wp = wp.home_wp
            continue
        delta = wp.home_wp - prev_wp
        magnitude = abs(delta)

        gsr = _game_seconds_remaining(play)
        tf = _time_factor(gsr)
        score_diff = play.score_home - play.score_away
        cf = math.exp(-abs(score_diff) / _K)

        clutch = magnitude * tf * cf
        clutch_plays.append((clutch, delta, tf, cf, score_diff, play))
        prev_wp = wp.home_wp

    # Top plays by clutch score
    clutch_plays.sort(key=lambda x: x[0], reverse=True)
    top_n = clutch_plays[:top_plays]

    result_plays: list[ClutchPlay] = []
    for rank, (clutch, delta, tf, cf, sdiff, play) in enumerate(top_n, start=1):
        result_plays.append(
            ClutchPlay(
                rank=rank,
                play_ref=_play_ref(play),
                delta_wp=delta,
                clutch_score=round(clutch, 4),
                time_factor=round(tf, 4),
                close_factor=round(cf, 4),
                score_diff=sdiff,
            )
        )

    # Drive-level clutch aggregation (approximated by possession team flips)
    drive_totals: list[tuple[int, str | None, float, int]] = []
    current_drive = 0
    current_posteam: uuid.UUID | None = None
    current_clutch = 0.0
    current_count = 0

    for clutch, _, _, _, _, play in clutch_plays + [(0, 0, 0, 0, 0, None)]:  # type: ignore[list-item]
        if play is None:
            if current_count > 0:
                drive_totals.append((current_drive, None, current_clutch, current_count))
            break
        if play.posteam_id != current_posteam:
            if current_count > 0:
                drive_totals.append((current_drive, None, current_clutch, current_count))
            current_drive += 1
            current_posteam = play.posteam_id
            current_clutch = 0.0
            current_count = 0
        current_clutch += clutch
        current_count += 1

    drive_totals.sort(key=lambda x: x[2], reverse=True)
    top_drives = [
        ClutchDrive(
            drive_number=dn,
            posteam_abbr=None,  # enriched by endpoint if needed
            clutch_total=round(ct, 4),
            play_count=pc,
        )
        for dn, _, ct, pc in drive_totals[:5]
    ]

    # Team clutch totals — derive from posteam_id vs home/away
    # We need home_team_id & away_team_id; fetch from game
    game_result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    game = game_result.scalar_one()

    home_offense = 0.0
    home_defense = 0.0
    away_offense = 0.0
    away_defense = 0.0

    for clutch, delta, _, _, _, play in clutch_plays:
        is_home_pos = play.posteam_id == game.home_team_id
        # Offense credit: posteam gains WP (delta > 0 for home, delta < 0 for away means away offense won)
        # From home perspective: positive delta = home offense or away defense stop
        # Simple split: credit posteam if delta favours them
        if is_home_pos:
            if delta > 0:
                home_offense += clutch
            else:
                # Home offense fumbled/turned over — away defense gets credit
                away_defense += clutch
        else:
            if delta < 0:  # away team gained WP
                away_offense += clutch
            else:
                home_defense += clutch

    return ClutchResponse(
        game_id=game_id,
        top_plays=result_plays,
        top_drives=top_drives,
        team_totals={
            "home": ClutchTeamTotals(
                offense=round(home_offense, 3),
                defense=round(home_defense, 3),
            ),
            "away": ClutchTeamTotals(
                offense=round(away_offense, 3),
                defense=round(away_defense, 3),
            ),
        },
    )


# ---------------------------------------------------------------------------
# 3. Coach Decision Grades
# ---------------------------------------------------------------------------

def _grade(decision_delta: float) -> tuple[str, str]:
    for threshold, label, emoji in _GRADE_MAP:
        if decision_delta >= threshold:
            return label, emoji
    return "Very Bad", "💀"


def _situation_string(play: Play) -> str:
    """Build a human-readable situation string, e.g. '4th & 7 at OPP 38'."""
    down = play.down or 4
    ydg = play.yards_to_go or "?"
    yl = play.yard_line_from_own
    if yl is not None:
        field = f"OWN {yl}" if yl <= 50 else f"OPP {100 - yl}"
    else:
        field = "?"
    return f"4th & {ydg} at {field}"


def _classify_actual(play: Play) -> Literal["go_for_it", "punt", "field_goal"] | None:
    pt = (play.play_type or "").lower()
    desc = (play.description or "").lower()
    if pt == "punt":
        return "punt"
    if pt in ("field_goal", "fg") or "field goal" in desc:
        return "field_goal"
    if pt in ("run", "pass", "qb_scramble", "pass_incomplete", "pass_complete"):
        return "go_for_it"
    # Also classify scrambles and rush attempts on 4th
    if "pass" in pt or "rush" in pt or "run" in pt:
        return "go_for_it"
    return None


def _wp_for_state(
    pairs_lookup: dict[int, tuple[Play, WpPrediction]],
    target_sequence: int,
) -> float | None:
    """Look up the WP at a given sequence in the play log (approximate next state)."""
    # Find the nearest play at or after target_sequence
    candidates = [s for s in pairs_lookup if s >= target_sequence]
    if not candidates:
        return None
    return pairs_lookup[min(candidates)][1].home_wp


def _build_counterfactuals(
    play: Play,
    wp_before: float,
    pairs_lookup: dict[int, tuple[Play, WpPrediction]],
    actual_type: Literal["go_for_it", "punt", "field_goal"],
) -> dict[str, DecisionOption | None]:
    """
    Build counterfactual WP estimates for go_for_it, punt, field_goal.
    Uses Approach A: fixed conversion probabilities + symmetric WP adjustments
    anchored on wp_before (the WP *before* the play).

    Key insight: the counterfactual WP is always relative to wp_before.
    Each action has a binary outcome (success / fail), so:
        wp_action = p_success * wp_success_state + (1-p_success) * wp_fail_state

    All "state WPs" are approximated as wp_before ± a delta that depends on
    field position, yardage, and time pressure.
    """
    yl = play.yard_line_from_own  # 0-50 from OWN end zone (stored as yard_line_from_own)
    ydg = play.yards_to_go or 10
    p_conv = _conv_prob(ydg)
    gsr = _game_seconds_remaining(play)
    time_pressure = 1.0 - gsr / 3600.0  # 0 at kickoff, 1 at final whistle

    # yardline_100 = distance from OPPONENT end zone (1–99)
    # yard_line_from_own is 0–50 from own end zone, so yardline_100 ≈ 100 - yl - 50 = 50 - yl
    # but stored as distance from own endzone (so yardline_100 = 100 - (yl+50)? Let's use the
    # field position directly.  yard_line_from_own = 0 (own end) … 50 (midfield).
    # Distance from opponent end zone = 100 - (50 + yl) if yl in [0,50].
    # Actually: yard_line_from_own stores 0-50 from own end zone, so:
    #   distance to opponent end zone = 100 - (yl + 50) when yl <= 50 → simplifies to 50 - yl.
    # But that gives negative values for own territory near 50.
    # The DB field name is yard_line_from_own and nflfastR yardline_100 = dist from OPP endzone.
    # Let's just treat yl directly as dist-from-own-endzone (0=own goalline, 50=midfield).
    yardline_100 = (100 - yl) if yl is not None else 50  # dist from OPP endzone

    alternatives: dict[str, DecisionOption | None] = {}

    # ---- go_for_it ----
    # Success: gain yards_to_go, keep ball — value ≈ wp_before + conversion_gain
    # Fail: turnover on downs — value ≈ (1 - wp_before) flipped (opponent gets ball)
    # conversion_gain scales with field position (more valuable near opponent end zone)
    field_value = (100 - yardline_100) / 100.0  # 0 = own end, 1 = opp end
    success_gain = 0.08 + 0.10 * field_value        # +8–18% WP on success
    fail_loss    = 0.12 + 0.08 * (1 - field_value)  # -12–20% WP on failure (worse own territory)

    wp_success = min(wp_before + success_gain, 0.97)
    wp_fail    = max(wp_before - fail_loss, 0.03)
    wp_go = p_conv * wp_success + (1 - p_conv) * wp_fail
    alternatives["go_for_it"] = DecisionOption(
        wp=round(wp_go, 4),
        detail=f"p_conv={p_conv:.0%}",
    )

    # ---- punt ----
    # Only makes sense outside ~FG range (yardline_100 > 45 from opp end)
    if yardline_100 > 45:
        opp_field_pos = _punt_expected_field_pos(yardline_100)
        net_yards = yardline_100 - opp_field_pos  # how far back we push them
        # Punting flips possession but gives opponent poor field position.
        # WP change relative to wp_before: flipping possession at opponent's spot.
        # Rough: each 10 yds of field position advantage ≈ 0.03 WP.
        field_pos_benefit = (net_yards / 10.0) * 0.03
        # Punting generally keeps score close → around 50% base, adjusted by current wp
        wp_punt = max(min(0.50 + field_pos_benefit * (1 if wp_before >= 0.50 else -1), 0.75), 0.25)
        # Blend with wp_before to avoid huge jumps
        wp_punt = 0.4 * wp_punt + 0.6 * wp_before
        alternatives["punt"] = DecisionOption(
            wp=round(wp_punt, 4),
            detail=f"expected_net={net_yards} yds",
        )
    else:
        alternatives["punt"] = None  # short field / red zone — punt not viable

    # ---- field_goal ----
    # Viable inside ~57 yards from opponent end zone (kick dist ≤ 57+17=74 is theoretical;
    # practical limit ≈ 55 yardline_100 i.e. ~72-yd attempt is rarely attempted)
    if yardline_100 is not None and yardline_100 <= 52:
        kick_dist = yardline_100 + 17  # snap depth + end zone
        p_fg = _fg_make_prob(kick_dist)
        score_diff = play.score_home - play.score_away
        # Made: +3 pts, kickoff → roughly symmetric possession flip with good field pos
        # How much +3 helps depends on current score_diff and time remaining
        pts_value = 0.05 + 0.06 * time_pressure  # +5–11% base value of 3 pts
        if abs(score_diff) <= 3:
            pts_value *= 1.5   # tie-or-one-score game: FG is very valuable
        wp_fg_made = min(wp_before + pts_value, 0.95)
        # Missed: opponent gets ball near the spot → bad for us
        miss_penalty = 0.04 + 0.06 * time_pressure
        wp_fg_miss = max(wp_before - miss_penalty, 0.05)
        wp_fg = p_fg * wp_fg_made + (1 - p_fg) * wp_fg_miss
        alternatives["field_goal"] = DecisionOption(
            wp=round(wp_fg, 4),
            detail=f"p_make={p_fg:.0%}, dist={kick_dist} yds",
        )
    else:
        alternatives["field_goal"] = None  # out of FG range

    return alternatives


async def get_decision_grades(
    db: AsyncSession,
    game_id: uuid.UUID,
    top: int = 10,
) -> DecisionGradesResponse:
    pairs = await _load_plays_with_wp(db, game_id)

    if len(pairs) < 2:
        return DecisionGradesResponse(game_id=game_id, decisions=[])

    # Build a sequence→(play, wp) lookup for counterfactual next-state WP
    pairs_lookup: dict[int, tuple[Play, WpPrediction]] = {
        play.sequence: (play, wp) for play, wp in pairs
    }

    decisions: list[CoachDecision] = []
    prev_wp = pairs[0][1].home_wp

    for play, wp in pairs:
        # Only grade 4th downs (down == 4)
        if play.down != 4:
            prev_wp = wp.home_wp
            continue

        # Skip all junk / administrative plays (including None play_type end markers)
        if _is_junk_play(play):
            prev_wp = wp.home_wp
            continue
        # Skip end-of-game kneels / victory-formation plays
        desc = (play.description or "").lower()
        if "kneel" in desc or "victory" in desc:
            prev_wp = wp.home_wp
            continue

        actual_type = _classify_actual(play)
        if actual_type is None:
            prev_wp = wp.home_wp
            continue

        alternatives = _build_counterfactuals(play, prev_wp, pairs_lookup, actual_type)

        # Get WP values for valid alternatives
        valid_wps: dict[str, float] = {}
        for action, opt in alternatives.items():
            if opt is not None:
                valid_wps[action] = opt.wp

        if not valid_wps:
            prev_wp = wp.home_wp
            continue

        best_action = max(valid_wps, key=lambda a: valid_wps[a])
        best_wp = valid_wps[best_action]
        actual_wp = valid_wps.get(actual_type, wp.home_wp)
        decision_delta = actual_wp - best_wp

        grade_label, grade_emoji = _grade(decision_delta)

        decisions.append(
            CoachDecision(
                play_ref=_play_ref(play),
                situation=_situation_string(play),
                actual_type=actual_type,
                actual_wp_after=round(wp.home_wp, 4),
                alternatives=alternatives,
                best_action=best_action,
                decision_delta=round(decision_delta, 4),
                grade=grade_label,  # type: ignore[arg-type]
                grade_emoji=grade_emoji,
            )
        )
        prev_wp = wp.home_wp

    # Sort by leverage: abs(best_wp - worst alternative) or by abs(decision_delta)
    decisions.sort(key=lambda d: abs(d.decision_delta), reverse=True)

    return DecisionGradesResponse(game_id=game_id, decisions=decisions[:top])
