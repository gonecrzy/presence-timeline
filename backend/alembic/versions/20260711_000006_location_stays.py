"""Add persisted location stays.

Revision ID: 20260711_000006
Revises: 20260711_000005
Create Date: 2026-07-11 00:00:06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260711_000006"
down_revision = "20260711_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "location_stays",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("point_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_location_stays_member_id_members", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_location_stays"),
    )
    op.create_index("ix_location_stays_started_at", "location_stays", ["started_at"], unique=False)
    op.create_index("ix_location_stays_ended_at", "location_stays", ["ended_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_location_stays_ended_at", table_name="location_stays")
    op.drop_index("ix_location_stays_started_at", table_name="location_stays")
    op.drop_table("location_stays")
