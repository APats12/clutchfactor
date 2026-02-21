"""add nflfastr_game_id to games

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-19 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("nflfastr_game_id", sa.String(), nullable=True))
    op.create_index("ix_games_nflfastr_game_id", "games", ["nflfastr_game_id"])

    # Back-fill the one seeded sample game
    op.execute(
        "UPDATE games SET nflfastr_game_id = '2022_21_CIN_KC' "
        "WHERE id = '00000000-0000-0000-0000-000000000001'"
    )


def downgrade() -> None:
    op.drop_index("ix_games_nflfastr_game_id", table_name="games")
    op.drop_column("games", "nflfastr_game_id")
