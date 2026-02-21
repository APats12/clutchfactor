from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.deps import DbSession
from app.schemas.analytics import (
    ClutchResponse,
    DecisionGradesResponse,
    MomentumSwingsResponse,
)
from app.schemas.game import GameDetail, GameRead
from app.schemas.play import PlayRead, PlayWpRead
from app.services.analytics_service import get_clutch_index, get_decision_grades, get_momentum_swings
from app.services.game_service import GameService

router = APIRouter(tags=["games"])


@router.get("/games", response_model=list[GameRead])
async def list_games(
    db: DbSession,
    game_date: date | None = Query(None, alias="date", description="Filter by scheduled date (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status: scheduled|in_progress|final"),
    season: int | None = Query(None, description="Filter by season year (e.g. 2025)"),
    week: int | None = Query(None, description="Filter by week number (1-18 for regular season)"),
    playoffs: bool = Query(False, description="If true, return only playoff games (week >= 19)"),
) -> list[GameRead]:
    svc = GameService(db)
    games = await svc.list_games(game_date=game_date, status=status, season=season, week=week, playoffs=playoffs)
    return games


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(game_id: UUID, db: DbSession) -> GameDetail:
    svc = GameService(db)
    return await svc.get_game(game_id)


@router.get("/games/{game_id}/plays", response_model=list[PlayRead])
async def list_plays(game_id: UUID, db: DbSession) -> list[PlayRead]:
    svc = GameService(db)
    return await svc.list_plays(game_id)


@router.get("/games/{game_id}/wp-history", response_model=list[PlayWpRead])
async def wp_history(game_id: UUID, db: DbSession) -> list[PlayWpRead]:
    """Return all plays for a game with their win-probability and SHAP data.
    Used to seed the WpChart when opening the game detail page after a replay."""
    svc = GameService(db)
    return await svc.list_plays_with_wp(game_id)


@router.get("/games/{game_id}/momentum-swings", response_model=MomentumSwingsResponse)
async def momentum_swings(
    game_id: UUID,
    db: DbSession,
    top: int = Query(3, ge=1, le=10, description="Number of top swings to return"),
) -> MomentumSwingsResponse:
    """Return the top N plays by win-probability swing magnitude."""
    return await get_momentum_swings(db, game_id, top=top)


@router.get("/games/{game_id}/clutch", response_model=ClutchResponse)
async def clutch_index(
    game_id: UUID,
    db: DbSession,
    top: int = Query(5, ge=1, le=20, description="Number of top clutch plays to return"),
) -> ClutchResponse:
    """Return clutch play rankings and team totals for a game."""
    svc = GameService(db)
    game = await svc.get_game(game_id)
    return await get_clutch_index(
        db,
        game_id,
        home_abbr=game.home_team.abbr,
        away_abbr=game.away_team.abbr,
        top_plays=top,
    )


@router.get("/games/{game_id}/decision-grades", response_model=DecisionGradesResponse)
async def decision_grades(
    game_id: UUID,
    db: DbSession,
    top: int = Query(10, ge=1, le=50, description="Number of top decisions to return"),
) -> DecisionGradesResponse:
    """Grade coaching decisions on 4th downs using counterfactual win probability."""
    return await get_decision_grades(db, game_id, top=top)
