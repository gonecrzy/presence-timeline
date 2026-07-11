from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Family(TimestampMixin, Base):
    __tablename__ = "families"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    members: Mapped[list["Member"]] = relationship(back_populates="family")
    places: Mapped[list["Place"]] = relationship(back_populates="family")


class Member(TimestampMixin, Base):
    __tablename__ = "members"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_color: Mapped[str | None] = mapped_column(String(32))
    is_child: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    family: Mapped[Family] = relationship(back_populates="members")
    devices: Mapped[list["Device"]] = relationship(back_populates="member")
    location_points: Mapped[list["LocationPoint"]] = relationship(back_populates="member")
    location_stays: Mapped[list["LocationStay"]] = relationship(back_populates="member")
    trips: Mapped[list["Trip"]] = relationship(back_populates="member")


class Device(TimestampMixin, Base):
    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String(255))
    ignored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    member: Mapped[Member] = relationship(back_populates="devices")
    location_points: Mapped[list["LocationPoint"]] = relationship(back_populates="device")


from app.models.location import LocationPoint, LocationStay  # noqa: E402
from app.models.place import Place  # noqa: E402
from app.models.trip import Trip  # noqa: E402
