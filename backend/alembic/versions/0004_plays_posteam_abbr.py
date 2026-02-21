"""add posteam_abbr string column to plays

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-19 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("plays", sa.Column("posteam_abbr", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("plays", "posteam_abbr")
