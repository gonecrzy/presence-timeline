"""Add places and safety-event place links.

Revision ID: 20260708_000002
Revises: 20260708_000001
Create Date: 2026-07-08 00:00:02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260708_000002"
down_revision = "20260708_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "places",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("place_type", sa.String(length=64), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Float(), nullable=False, server_default=sa.text("150")),
        sa.Column("is_safe_zone", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], name="fk_places_family_id_families", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_places"),
    )
    op.add_column("safety_events", sa.Column("place_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_safety_events_place_id_places",
        "safety_events",
        "places",
        ["place_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_safety_events_place_id_places", "safety_events", type_="foreignkey")
    op.drop_column("safety_events", "place_id")
    op.drop_table("places")
