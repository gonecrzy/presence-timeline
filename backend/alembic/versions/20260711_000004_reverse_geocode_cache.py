"""Add reverse geocode cache table.

Revision ID: 20260711_000004
Revises: 20260708_000003
Create Date: 2026-07-11 00:00:04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260711_000004"
down_revision = "20260708_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reverse_geocode_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("latitude_rounded", sa.Float(), nullable=False),
        sa.Column("longitude_rounded", sa.Float(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_reverse_geocode_cache"),
        sa.UniqueConstraint(
            "latitude_rounded",
            "longitude_rounded",
            name="uq_reverse_geocode_cache_latitude_longitude",
        ),
    )


def downgrade() -> None:
    op.drop_table("reverse_geocode_cache")
