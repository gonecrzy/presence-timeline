from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session

from app.models.family import Device, Family, Member
from app.models.location import DailySummary, LocationPoint, SafetyEvent
from app.models.trip import Trip


class LocationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_family_by_slug(self, family_slug: str) -> Family | None:
        stmt: Select[tuple[Family]] = select(Family).where(Family.slug == family_slug)
        return self.db.scalar(stmt)

    def ensure_family(self, family_slug: str, family_name: str) -> Family:
        family = self.get_family_by_slug(family_slug)
        if family is None:
            family = Family(name=family_name, slug=family_slug)
            self.db.add(family)
            self.db.flush()
        else:
            family.name = family_name
        return family

    def ensure_member(
        self,
        family: Family,
        display_name: str,
        is_child: bool,
        avatar_color: str | None,
    ) -> Member:
        stmt: Select[tuple[Member]] = (
            select(Member)
            .where(Member.family_id == family.id)
            .where(Member.display_name == display_name)
        )
        member = self.db.scalar(stmt)
        if member is None:
            member = Member(
                family_id=family.id,
                display_name=display_name,
                is_child=is_child,
                avatar_color=avatar_color,
            )
            self.db.add(member)
            self.db.flush()
        else:
            member.is_child = is_child
            member.avatar_color = avatar_color
        return member

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

    def commit(self) -> None:
        self.db.commit()

    def delete_location_points_older_than(self, cutoff: datetime) -> int:
        result = self.db.execute(
            delete(LocationPoint).where(LocationPoint.observed_at < cutoff),
        )
        return int(result.rowcount or 0)

    def delete_safety_events_older_than(self, cutoff: datetime) -> int:
        result = self.db.execute(
            delete(SafetyEvent).where(SafetyEvent.observed_at < cutoff),
        )
        return int(result.rowcount or 0)

    def delete_daily_summaries_older_than(self, cutoff: datetime) -> int:
        result = self.db.execute(
            delete(DailySummary).where(DailySummary.summary_date < cutoff.date()),
        )
        return int(result.rowcount or 0)

    def delete_trips_older_than(self, cutoff: datetime) -> int:
        result = self.db.execute(
            delete(Trip).where(
                (Trip.ended_at.is_not(None) & (Trip.ended_at < cutoff))
                | (Trip.ended_at.is_(None) & (Trip.started_at < cutoff))
            ),
        )
        return int(result.rowcount or 0)

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
