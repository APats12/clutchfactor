from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.game import Game, GameStatus
from app.db.models.play import Play
from app.db.models.shap_value import ShapValue
from app.db.models.wp_prediction import WpPrediction
from app.ml.features import FEATURE_DISPLAY_NAMES
from app.schemas.game import GameDetail, GameRead
from app.schemas.play import PlayRead, PlayWpRead
from app.schemas.shap import ShapFeature


class GameService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_games(
        self,
        game_date: date | None = None,
        status: str | None = None,
        season: int | None = None,
        week: int | None = None,
        playoffs: bool = False,
    ) -> list[GameRead]:
        stmt = (
            select(Game)
            .options(selectinload(Game.home_team), selectinload(Game.away_team))
            .order_by(Game.scheduled_at.desc())
        )

        if game_date is not None:
            day_start = datetime(game_date.year, game_date.month, game_date.day, tzinfo=timezone.utc)
            day_end = datetime(game_date.year, game_date.month, game_date.day, 23, 59, 59, tzinfo=timezone.utc)
            stmt = stmt.where(Game.scheduled_at.between(day_start, day_end))

        if status is not None:
            try:
                gs = GameStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status '{status}'")
            stmt = stmt.where(Game.status == gs)

        if season is not None:
            stmt = stmt.where(Game.season == season)

        if playoffs:
            stmt = stmt.where(Game.week >= 19)
        elif week is not None:
            stmt = stmt.where(Game.week == week)

        result = await self._db.execute(stmt)
        games = result.scalars().all()
        return [GameRead.model_validate(g) for g in games]

    async def get_game(self, game_id: UUID) -> GameDetail:
        stmt = (
            select(Game)
            .where(Game.id == game_id)
            .options(selectinload(Game.home_team), selectinload(Game.away_team))
        )
        result = await self._db.execute(stmt)
        game = result.scalar_one_or_none()
        if game is None:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

        # Count plays
        count_result = await self._db.execute(
            select(func.count()).where(Play.game_id == game_id)
        )
        play_count = count_result.scalar_one()

        detail = GameDetail.model_validate(game)
        detail.play_count = play_count
        return detail

    async def list_plays(self, game_id: UUID) -> list[PlayRead]:
        # Verify game exists
        game_result = await self._db.execute(select(Game).where(Game.id == game_id))
        if game_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

        stmt = select(Play).where(Play.game_id == game_id).order_by(Play.sequence)
        result = await self._db.execute(stmt)
        plays = result.scalars().all()
        return [PlayRead.model_validate(p) for p in plays]

    async def list_plays_with_wp(self, game_id: UUID) -> list[PlayWpRead]:
        """Return plays joined with their WP predictions and SHAP values, sorted by sequence."""
        game_result = await self._db.execute(select(Game).where(Game.id == game_id))
        if game_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

        # Load plays with their latest WP prediction and that prediction's SHAP values
        stmt = (
            select(Play)
            .where(Play.game_id == game_id)
            .options(
                selectinload(Play.wp_predictions).selectinload(WpPrediction.shap_values),
            )
            .order_by(Play.sequence)
        )
        result = await self._db.execute(stmt)
        plays = result.scalars().all()

        out: list[PlayWpRead] = []
        for play in plays:
            if not play.wp_predictions:
                continue
            # Use the most recent prediction for this play
            wp = max(play.wp_predictions, key=lambda p: p.predicted_at)

            home_wp = wp.home_wp
            away_wp = wp.away_wp

            # Clamp to certainty only at true game-end: Q4/OT at 0:00 with a
            # non-zero score diff.  Quarter-end rows in Q1–Q3 also have
            # game_clock_seconds=0 but the game is not over — do not clamp those.
            score_diff = play.score_home - play.score_away
            if play.game_clock_seconds == 0 and play.quarter >= 4 and score_diff != 0:
                home_wp = 1.0 if score_diff > 0 else 0.0
                away_wp = 1.0 - home_wp

            top_shap = sorted(
                [
                    ShapFeature.from_raw(
                        feature_name=sv.feature_name,
                        shap_value=sv.shap_value,
                        display_name=FEATURE_DISPLAY_NAMES.get(sv.feature_name, sv.feature_name),
                    )
                    for sv in wp.shap_values
                ],
                key=lambda f: abs(f.shap_value),
                reverse=True,
            )

            base = PlayRead.model_validate(play).model_dump()
            base['posteam_abbr'] = play.posteam_abbr
            out.append(
                PlayWpRead(
                    **base,
                    home_wp=home_wp,
                    away_wp=away_wp,
                    top_shap=top_shap,
                )
            )
        return out
