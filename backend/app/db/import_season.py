"""
Import all games from a nflfastR play-by-play CSV into the database.

Usage:
    docker compose exec backend python -m app.db.import_season --season 2025

Each game is inserted once (idempotent — skips games already present for the
same season + week + home/away team combination). Only game metadata is stored;
WP replay can be run separately per game on demand.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
import uuid

import pandas as pd
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db.models.game import Game, GameStatus
from app.db.models.team import Team

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parents[3] / "ml" / "data"

# nflfastR uses different abbreviations for some teams vs our teams table
ABBR_MAP: dict[str, str] = {
    "LA": "LAR",   # Los Angeles Rams
    "OAK": "LV",   # Oakland Raiders → Las Vegas Raiders
    "SD": "LAC",   # San Diego Chargers → LA Chargers
    "STL": "LAR",  # St. Louis Rams → LA Rams
}


def _normalize_abbr(abbr: str) -> str:
    return ABBR_MAP.get(abbr, abbr)


def _safe_int(val) -> int | None:
    try:
        v = float(val)
        return None if math.isnan(v) else int(v)
    except (TypeError, ValueError):
        return None


def _parse_date(val) -> datetime | None:
    """Parse a YYYY-MM-DD string into a UTC datetime at 13:00."""
    if not val or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        d = datetime.strptime(str(val)[:10], "%Y-%m-%d")
        return d.replace(hour=13)  # naive UTC — column is TIMESTAMP WITHOUT TIME ZONE
    except ValueError:
        return None


async def import_season(season: int) -> None:
    csv_path = DATA_DIR / f"play_by_play_{season}.csv"
    if not csv_path.exists():
        # Fall back to the mounted path inside Docker
        csv_path = Path("/ml/data") / f"play_by_play_{season}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found at {csv_path}. Run: python -m app.ml.train --skip-download "
            f"or download_season({season}) first."
        )

    logger.info("Reading %s ...", csv_path)
    cols = ["game_id", "home_team", "away_team", "week", "season",
            "game_date", "total_home_score", "total_away_score", "result", "stadium"]
    available_cols = pd.read_csv(csv_path, nrows=0).columns.tolist()
    use_cols = [c for c in cols if c in available_cols]
    df = pd.read_csv(csv_path, low_memory=False, usecols=use_cols)

    # One row per game (last row has final scores)
    games_df = df.groupby("game_id").last().reset_index()
    logger.info("Found %d unique games for season %d", len(games_df), season)

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Load all teams into a lookup dict
        teams_result = await session.execute(select(Team))
        teams: dict[str, Team] = {t.abbr: t for t in teams_result.scalars().all()}

        # Find already-existing games for this season to skip duplicates
        existing_result = await session.execute(
            select(Game.season, Game.week, Game.home_team_id, Game.away_team_id)
            .where(Game.season == season)
        )
        existing_set = set(existing_result.fetchall())

        inserted = 0
        skipped = 0
        unknown_teams: set[str] = set()

        for _, row in games_df.iterrows():
            home_abbr = _normalize_abbr(str(row.get("home_team", "") or ""))
            away_abbr = _normalize_abbr(str(row.get("away_team", "") or ""))

            home_team = teams.get(home_abbr)
            away_team = teams.get(away_abbr)

            if home_team is None:
                unknown_teams.add(home_abbr)
                continue
            if away_team is None:
                unknown_teams.add(away_abbr)
                continue

            week = _safe_int(row.get("week")) or 0

            # Skip if already in DB
            key = (season, week, home_team.id, away_team.id)
            if key in existing_set:
                skipped += 1
                continue

            result_val = row.get("result")
            has_result = result_val is not None and not (
                isinstance(result_val, float) and math.isnan(result_val)
            )
            status = GameStatus.final if has_result else GameStatus.scheduled

            home_score = _safe_int(row.get("total_home_score")) if has_result else None
            away_score = _safe_int(row.get("total_away_score")) if has_result else None
            scheduled_at = _parse_date(row.get("game_date"))
            venue = str(row.get("stadium", "") or "").strip() or None

            game = Game(
                id=uuid.uuid4(),
                season=season,
                week=week,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                status=status,
                scheduled_at=scheduled_at,
                final_home_score=home_score,
                final_away_score=away_score,
                venue=venue,
            )
            session.add(game)
            inserted += 1

        await session.commit()

    await engine.dispose()

    if unknown_teams:
        logger.warning("Skipped games with unknown team abbreviations: %s", unknown_teams)
    print(f"\n✓ Season {season}: {inserted} games inserted, {skipped} already existed.")
    if unknown_teams:
        print(f"  Unknown abbrs (add to ABBR_MAP if needed): {unknown_teams}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Import NFL season games into the database")
    parser.add_argument("--season", type=int, required=True, help="Season year (e.g. 2025)")
    args = parser.parse_args()
    asyncio.run(import_season(args.season))
