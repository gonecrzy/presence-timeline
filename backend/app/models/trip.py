from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    point_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distance_m: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    start_label: Mapped[str | None] = mapped_column(String(255))
    end_label: Mapped[str | None] = mapped_column(String(255))
    route_geom: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
    )

    member: Mapped["Member"] = relationship(back_populates="trips")


from app.models.family import Member  # noqa: E402
