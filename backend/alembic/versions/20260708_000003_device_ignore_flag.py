"""Add ignored flag to devices.

Revision ID: 20260708_000003
Revises: 20260708_000002
Create Date: 2026-07-08 00:00:03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260708_000003"
down_revision = "20260708_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("ignored", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("devices", "ignored")
