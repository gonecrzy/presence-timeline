"""Initial gpstrack schema.

Revision ID: 20260708_000001
Revises:
Create Date: 2026-07-08 00:00:01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


revision = "20260708_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "families",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_families"),
        sa.UniqueConstraint("slug", name="uq_families_slug"),
    )

    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("avatar_color", sa.String(length=32), nullable=True),
        sa.Column("is_child", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], name="fk_members_family_id_families", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_members"),
    )

    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_devices_member_id_members", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_devices"),
        sa.UniqueConstraint("external_id", name="uq_devices_external_id"),
    )

    op.create_table(
        "location_points",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude_m", sa.Float(), nullable=True),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("battery_level", sa.Integer(), nullable=True),
        sa.Column("is_charging", sa.Boolean(), nullable=True),
        sa.Column("geom", Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], name="fk_location_points_device_id_devices", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_location_points_member_id_members", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_location_points"),
    )
    op.create_index("ix_location_points_observed_at", "location_points", ["observed_at"], unique=False)
    op.create_index(
        "ix_location_points_geom",
        "location_points",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )

    op.create_table(
        "trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("point_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("distance_m", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("start_label", sa.String(length=255), nullable=True),
        sa.Column("end_label", sa.String(length=255), nullable=True),
        sa.Column("route_geom", Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_trips_member_id_members", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_trips"),
    )
    op.create_index("ix_trips_route_geom", "trips", ["route_geom"], unique=False, postgresql_using="gist")

    op.create_table(
        "daily_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary_date", sa.Date(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trip_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_distance_m", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_daily_summaries_member_id_members", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_daily_summaries"),
    )

    op.create_table(
        "safety_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default=sa.text("'info'")),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_safety_events_member_id_members", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_safety_events"),
    )


def downgrade() -> None:
    op.drop_table("safety_events")
    op.drop_table("daily_summaries")
    op.drop_index("ix_trips_route_geom", table_name="trips", postgresql_using="gist")
    op.drop_table("trips")
    op.drop_index("ix_location_points_geom", table_name="location_points", postgresql_using="gist")
    op.drop_index("ix_location_points_observed_at", table_name="location_points")
    op.drop_table("location_points")
    op.drop_table("devices")
    op.drop_table("members")
    op.drop_table("families")
