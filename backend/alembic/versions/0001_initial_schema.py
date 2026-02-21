"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── teams ─────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("abbr", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("conference", sa.String(), nullable=True),
        sa.Column("division", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("primary_color", sa.String(), nullable=True),
        sa.Column("secondary_color", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("abbr"),
    )
    op.create_index("ix_teams_abbr", "teams", ["abbr"])

    # ── games ─────────────────────────────────────────────
    # create_type=False tells SA not to auto-emit CREATE TYPE during create_table;
    # we create it once explicitly so we control the name.
    gamestatus_enum = postgresql.ENUM(
        "scheduled", "in_progress", "final", name="gamestatus", create_type=False
    )
    gamestatus_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("home_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("away_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "scheduled", "in_progress", "final",
                name="gamestatus", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_home_score", sa.Integer(), nullable=True),
        sa.Column("final_away_score", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_games_season", "games", ["season"])
    op.create_index("ix_games_status", "games", ["status"])
    op.create_index("ix_games_home_team_id", "games", ["home_team_id"])
    op.create_index("ix_games_away_team_id", "games", ["away_team_id"])

    # ── plays ─────────────────────────────────────────────
    op.create_table(
        "plays",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("play_number", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("game_clock_seconds", sa.Integer(), nullable=False),
        sa.Column("down", sa.Integer(), nullable=True),
        sa.Column("yards_to_go", sa.Integer(), nullable=True),
        sa.Column("yard_line_from_own", sa.Integer(), nullable=True),
        sa.Column("posteam_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("defteam_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("score_home", sa.Integer(), nullable=False),
        sa.Column("score_away", sa.Integer(), nullable=False),
        sa.Column("play_type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["defteam_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.ForeignKeyConstraint(["posteam_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plays_game_id", "plays", ["game_id"])

    # ── play_raw ──────────────────────────────────────────
    op.create_table(
        "play_raw",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("play_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["play_id"], ["plays.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("play_id"),
    )
    op.create_index("ix_play_raw_play_id", "play_raw", ["play_id"])

    # ── game_state_snapshots ──────────────────────────────
    op.create_table(
        "game_state_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("game_clock_seconds", sa.Integer(), nullable=False),
        sa.Column("situation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_game_state_snapshots_game_id", "game_state_snapshots", ["game_id"]
    )

    # ── model_versions ────────────────────────────────────
    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=False),
        sa.Column("brier_score", sa.Float(), nullable=True),
        sa.Column("log_loss_val", sa.Float(), nullable=True),
        sa.Column("trained_on_seasons", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_model_versions_name", "model_versions", ["name"])
    op.create_index("ix_model_versions_is_current", "model_versions", ["is_current"])

    # ── wp_predictions ────────────────────────────────────
    op.create_table(
        "wp_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("play_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("home_wp", sa.Float(), nullable=False),
        sa.Column("away_wp", sa.Float(), nullable=False),
        sa.Column(
            "predicted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["play_id"], ["plays.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wp_predictions_play_id", "wp_predictions", ["play_id"])
    op.create_index(
        "ix_wp_predictions_model_version_id", "wp_predictions", ["model_version_id"]
    )

    # ── shap_values ───────────────────────────────────────
    op.create_table(
        "shap_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wp_prediction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_name", sa.String(), nullable=False),
        sa.Column("shap_value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["wp_prediction_id"], ["wp_predictions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_shap_values_wp_prediction_id", "shap_values", ["wp_prediction_id"]
    )

    # ── odds_snapshots ────────────────────────────────────
    op.create_table(
        "odds_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("home_ml", sa.Float(), nullable=True),
        sa.Column("away_ml", sa.Float(), nullable=True),
        sa.Column("home_spread", sa.Float(), nullable=True),
        sa.Column(
            "snap_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_odds_snapshots_game_id", "odds_snapshots", ["game_id"])


def downgrade() -> None:
    op.drop_table("odds_snapshots")
    op.drop_table("shap_values")
    op.drop_table("wp_predictions")
    op.drop_table("model_versions")
    op.drop_table("game_state_snapshots")
    op.drop_table("play_raw")
    op.drop_table("plays")
    op.drop_table("games")
    postgresql.ENUM(name="gamestatus", create_type=False).drop(op.get_bind(), checkfirst=True)
    op.drop_table("teams")
