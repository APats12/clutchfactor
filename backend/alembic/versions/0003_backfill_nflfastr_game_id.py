"""backfill nflfastr_game_id for all games

Derives the nflfastR game_id string from season, week, and team abbreviations.
Format: {season}_{week:02d}_{away_abbr}_{home_abbr}

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-19 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE games
        SET nflfastr_game_id = CONCAT(
            season, '_',
            LPAD(week::text, 2, '0'), '_',
            (SELECT abbr FROM teams WHERE teams.id = games.away_team_id), '_',
            (SELECT abbr FROM teams WHERE teams.id = games.home_team_id)
        )
        WHERE nflfastr_game_id IS NULL
    """)


def downgrade() -> None:
    # Can't safely undo a back-fill; leave as-is
    pass
