from uuid import UUID, uuid4

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Place(TimestampMixin, Base):
    __tablename__ = "places"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    place_type: Mapped[str | None] = mapped_column(String(64))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[float] = mapped_column(Float, nullable=False, default=150.0)
    is_safe_zone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    family: Mapped["Family"] = relationship(back_populates="places")
    safety_events: Mapped[list["SafetyEvent"]] = relationship(back_populates="place")


from app.models.family import Family  # noqa: E402
from app.models.location import SafetyEvent  # noqa: E402
