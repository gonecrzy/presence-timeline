from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.family import Device, Family, Member
from app.models.location import LocationPoint


class LocationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_members_for_family_slug(self, family_slug: str) -> list[Member]:
        stmt: Select[tuple[Member]] = (
            select(Member)
            .join(Family, Member.family_id == Family.id)
            .where(Family.slug == family_slug)
            .order_by(Member.display_name.asc())
        )
        return list(self.db.scalars(stmt))

    def resolve_member_by_source_entity(self, source_entity_id: str) -> Member | None:
        stmt: Select[tuple[Member]] = (
            select(Member)
            .join(Device, Device.member_id == Member.id)
            .where(Device.external_id == source_entity_id)
        )
        return self.db.scalar(stmt)

    def upsert_device_for_member(
        self,
        member: Member,
        provider: str,
        external_id: str,
        label: str | None,
    ) -> Device:
        stmt: Select[tuple[Device]] = select(Device).where(Device.external_id == external_id)
        device = self.db.scalar(stmt)
        if device is None:
            device = Device(
                member_id=member.id,
                provider=provider,
                external_id=external_id,
            )
            self.db.add(device)

        device.label = label
        device.last_seen_at = member.last_seen_at
        return device

    def add_location_point(self, point: LocationPoint) -> LocationPoint:
        self.db.add(point)
        self.db.flush()
        self.db.refresh(point)
        return point

    def get_latest_point_for_member(self, member_id: UUID) -> LocationPoint | None:
        stmt: Select[tuple[LocationPoint]] = (
            select(LocationPoint)
            .where(LocationPoint.member_id == member_id)
            .order_by(LocationPoint.observed_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_member_history(
        self,
        member_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[LocationPoint]:
        stmt: Select[tuple[LocationPoint]] = (
            select(LocationPoint)
            .where(LocationPoint.member_id == member_id)
            .where(LocationPoint.observed_at >= start)
            .where(LocationPoint.observed_at <= end)
            .order_by(LocationPoint.observed_at.asc())
        )
        return list(self.db.scalars(stmt))
