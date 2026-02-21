"""
Seed script: inserts all 32 NFL teams into the database.
Run with: uv run python -m app.db.seed
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import get_settings
from app.db.base import init_db, get_session_factory
from app.db.models.team import Team
from app.db.models.game import Game, GameStatus
from app.db.models.model_version import ModelVersion

NFL_TEAMS = [
    # AFC East
    {"abbr": "BUF", "name": "Buffalo Bills", "conference": "AFC", "division": "AFC East", "primary_color": "#00338D", "secondary_color": "#C60C30"},
    {"abbr": "MIA", "name": "Miami Dolphins", "conference": "AFC", "division": "AFC East", "primary_color": "#008E97", "secondary_color": "#FC4C02"},
    {"abbr": "NE",  "name": "New England Patriots", "conference": "AFC", "division": "AFC East", "primary_color": "#002244", "secondary_color": "#C60C30"},
    {"abbr": "NYJ", "name": "New York Jets", "conference": "AFC", "division": "AFC East", "primary_color": "#125740", "secondary_color": "#FFFFFF"},
    # AFC North
    {"abbr": "BAL", "name": "Baltimore Ravens", "conference": "AFC", "division": "AFC North", "primary_color": "#241773", "secondary_color": "#000000"},
    {"abbr": "CIN", "name": "Cincinnati Bengals", "conference": "AFC", "division": "AFC North", "primary_color": "#FB4F14", "secondary_color": "#000000"},
    {"abbr": "CLE", "name": "Cleveland Browns", "conference": "AFC", "division": "AFC North", "primary_color": "#311D00", "secondary_color": "#FF3C00"},
    {"abbr": "PIT", "name": "Pittsburgh Steelers", "conference": "AFC", "division": "AFC North", "primary_color": "#101820", "secondary_color": "#FFB612"},
    # AFC South
    {"abbr": "HOU", "name": "Houston Texans", "conference": "AFC", "division": "AFC South", "primary_color": "#03202F", "secondary_color": "#A71930"},
    {"abbr": "IND", "name": "Indianapolis Colts", "conference": "AFC", "division": "AFC South", "primary_color": "#002C5F", "secondary_color": "#A2AAAD"},
    {"abbr": "JAX", "name": "Jacksonville Jaguars", "conference": "AFC", "division": "AFC South", "primary_color": "#006778", "secondary_color": "#D7A22A"},
    {"abbr": "TEN", "name": "Tennessee Titans", "conference": "AFC", "division": "AFC South", "primary_color": "#0C2340", "secondary_color": "#4B92DB"},
    # AFC West
    {"abbr": "DEN", "name": "Denver Broncos", "conference": "AFC", "division": "AFC West", "primary_color": "#002244", "secondary_color": "#FC4C02"},
    {"abbr": "KC",  "name": "Kansas City Chiefs", "conference": "AFC", "division": "AFC West", "primary_color": "#E31837", "secondary_color": "#FFB81C"},
    {"abbr": "LV",  "name": "Las Vegas Raiders", "conference": "AFC", "division": "AFC West", "primary_color": "#000000", "secondary_color": "#A5ACAF"},
    {"abbr": "LAC", "name": "Los Angeles Chargers", "conference": "AFC", "division": "AFC West", "primary_color": "#0080C6", "secondary_color": "#FFC20E"},
    # NFC East
    {"abbr": "DAL", "name": "Dallas Cowboys", "conference": "NFC", "division": "NFC East", "primary_color": "#003594", "secondary_color": "#041E42"},
    {"abbr": "NYG", "name": "New York Giants", "conference": "NFC", "division": "NFC East", "primary_color": "#0B2265", "secondary_color": "#A71930"},
    {"abbr": "PHI", "name": "Philadelphia Eagles", "conference": "NFC", "division": "NFC East", "primary_color": "#004C54", "secondary_color": "#A5ACAF"},
    {"abbr": "WAS", "name": "Washington Commanders", "conference": "NFC", "division": "NFC East", "primary_color": "#5A1414", "secondary_color": "#FFB612"},
    # NFC North
    {"abbr": "CHI", "name": "Chicago Bears", "conference": "NFC", "division": "NFC North", "primary_color": "#0B162A", "secondary_color": "#C83803"},
    {"abbr": "DET", "name": "Detroit Lions", "conference": "NFC", "division": "NFC North", "primary_color": "#0076B6", "secondary_color": "#B0B7BC"},
    {"abbr": "GB",  "name": "Green Bay Packers", "conference": "NFC", "division": "NFC North", "primary_color": "#203731", "secondary_color": "#FFB612"},
    {"abbr": "MIN", "name": "Minnesota Vikings", "conference": "NFC", "division": "NFC North", "primary_color": "#4F2683", "secondary_color": "#FFC62F"},
    # NFC South
    {"abbr": "ATL", "name": "Atlanta Falcons", "conference": "NFC", "division": "NFC South", "primary_color": "#A71930", "secondary_color": "#000000"},
    {"abbr": "CAR", "name": "Carolina Panthers", "conference": "NFC", "division": "NFC South", "primary_color": "#0085CA", "secondary_color": "#101820"},
    {"abbr": "NO",  "name": "New Orleans Saints", "conference": "NFC", "division": "NFC South", "primary_color": "#D3BC8D", "secondary_color": "#101820"},
    {"abbr": "TB",  "name": "Tampa Bay Buccaneers", "conference": "NFC", "division": "NFC South", "primary_color": "#D50A0A", "secondary_color": "#FF7900"},
    # NFC West
    {"abbr": "ARI", "name": "Arizona Cardinals", "conference": "NFC", "division": "NFC West", "primary_color": "#97233F", "secondary_color": "#FFB612"},
    {"abbr": "LAR", "name": "Los Angeles Rams", "conference": "NFC", "division": "NFC West", "primary_color": "#003594", "secondary_color": "#FFA300"},
    {"abbr": "SF",  "name": "San Francisco 49ers", "conference": "NFC", "division": "NFC West", "primary_color": "#AA0000", "secondary_color": "#B3995D"},
    {"abbr": "SEA", "name": "Seattle Seahawks", "conference": "NFC", "division": "NFC West", "primary_color": "#002244", "secondary_color": "#69BE28"},
]


async def seed() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    factory = get_session_factory()

    async with factory() as session:
        # Seed teams (idempotent — skip if abbr already exists)
        existing = (await session.execute(select(Team.abbr))).scalars().all()
        existing_set = set(existing)

        new_teams = []
        for t in NFL_TEAMS:
            if t["abbr"] not in existing_set:
                new_teams.append(Team(id=uuid.uuid4(), **t))

        if new_teams:
            session.add_all(new_teams)
            await session.commit()
            print(f"Seeded {len(new_teams)} teams.")
        else:
            print("Teams already seeded.")

        # Refresh to get IDs
        all_teams = {t.abbr: t for t in (await session.execute(select(Team))).scalars().all()}

        # Seed one sample game (2022 AFC Championship: KC vs CIN)
        sample_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        existing_game = (
            await session.execute(select(Game).where(Game.id == sample_id))
        ).scalar_one_or_none()

        if existing_game is None and "KC" in all_teams and "CIN" in all_teams:
            sample_game = Game(
                id=sample_id,
                season=2022,
                week=20,  # AFC Championship
                home_team_id=all_teams["KC"].id,
                away_team_id=all_teams["CIN"].id,
                status=GameStatus.final,
                nflfastr_game_id="2022_21_CIN_KC",
                scheduled_at=datetime(2023, 1, 29, 18, 30),
                started_at=datetime(2023, 1, 29, 18, 35),
                final_home_score=23,
                final_away_score=20,
                venue="Arrowhead Stadium",
            )
            session.add(sample_game)
            await session.commit()
            print(f"Seeded sample game: KC vs CIN (id={sample_id})")
        else:
            print("Sample game already seeded.")

        # Seed demo game: DAL @ WAS, Week 18 2023
        demo_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        existing_demo = (
            await session.execute(select(Game).where(Game.id == demo_id))
        ).scalar_one_or_none()

        if existing_demo is None and "DAL" in all_teams and "WAS" in all_teams:
            demo_game = Game(
                id=demo_id,
                season=2023,
                week=18,
                home_team_id=all_teams["WAS"].id,
                away_team_id=all_teams["DAL"].id,
                status=GameStatus.in_progress,
                nflfastr_game_id="2023_18_DAL_WAS",
                scheduled_at=datetime(2024, 1, 7, 13, 0),
                started_at=datetime(2024, 1, 7, 13, 5),
                venue="FedExField",
            )
            session.add(demo_game)
            await session.commit()
            print(f"Seeded demo game: DAL @ WAS (id={demo_id})")
        else:
            print("Demo game already seeded.")

        # Seed model version
        existing_mv = (
            await session.execute(select(ModelVersion).where(ModelVersion.is_current.is_(True)))
        ).scalar_one_or_none()

        if existing_mv is None:
            mv = ModelVersion(
                id=uuid.uuid4(),
                name="xgb_20260219_082135",
                artifact_path="xgb_20260219_082135.joblib",
                is_current=True,
                trained_on_seasons=["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"],
            )
            session.add(mv)
            await session.commit()
            print(f"Seeded model version: {mv.name}")
        else:
            print(f"Model version already seeded: {existing_mv.name}")


if __name__ == "__main__":
    asyncio.run(seed())
