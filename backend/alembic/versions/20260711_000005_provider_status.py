"""Add provider status table.

Revision ID: 20260711_000005
Revises: 20260711_000004
Create Date: 2026-07-11 00:00:05
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260711_000005"
down_revision = "20260711_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_status",
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("last_snapshot_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("provider", name="pk_provider_status"),
    )


def downgrade() -> None:
    op.drop_table("provider_status")
