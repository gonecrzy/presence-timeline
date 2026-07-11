from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import Select, delete, or_, select
from sqlalchemy.orm import Session

from app.models.family import Device, Family, Member
from app.models.location import DailySummary, LocationPoint, ProviderStatus, ReverseGeocodeCache, SafetyEvent
from app.models.place import Place
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

    def get_member(self, member_id: UUID) -> Member | None:
        stmt: Select[tuple[Member]] = select(Member).where(Member.id == member_id)
        return self.db.scalar(stmt)

    def get_member_for_family_slug(self, family_slug: str, member_id: UUID) -> Member | None:
        stmt: Select[tuple[Member]] = (
            select(Member)
            .join(Family, Member.family_id == Family.id)
            .where(Family.slug == family_slug)
            .where(Member.id == member_id)
        )
        return self.db.scalar(stmt)

    def list_places_for_family_slug(self, family_slug: str) -> list[Place]:
        stmt: Select[tuple[Place]] = (
            select(Place)
            .join(Family, Place.family_id == Family.id)
            .where(Family.slug == family_slug)
            .order_by(Place.name.asc())
        )
        return list(self.db.scalars(stmt))

    def list_places_for_family_id(self, family_id: UUID) -> list[Place]:
        stmt: Select[tuple[Place]] = (
            select(Place)
            .where(Place.family_id == family_id)
            .order_by(Place.name.asc())
        )
        return list(self.db.scalars(stmt))

    def create_place(
        self,
        family_id: UUID,
        *,
        name: str,
        place_type: str | None,
        latitude: float,
        longitude: float,
        radius_m: float,
        is_safe_zone: bool,
    ) -> Place:
        place = Place(
            family_id=family_id,
            name=name,
            place_type=place_type,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            is_safe_zone=is_safe_zone,
        )
        self.db.add(place)
        self.db.flush()
        return place

    def get_place_for_family_slug(self, family_slug: str, place_id: UUID) -> Place | None:
        stmt: Select[tuple[Place]] = (
            select(Place)
            .join(Family, Place.family_id == Family.id)
            .where(Family.slug == family_slug)
            .where(Place.id == place_id)
        )
        return self.db.scalar(stmt)

    def update_place_for_family_slug(
        self,
        family_slug: str,
        place_id: UUID,
        *,
        name: str,
        place_type: str | None,
        latitude: float,
        longitude: float,
        radius_m: float,
        is_safe_zone: bool,
    ) -> Place | None:
        place = self.get_place_for_family_slug(family_slug, place_id)
        if place is None:
            return None
        place.name = name
        place.place_type = place_type
        place.latitude = latitude
        place.longitude = longitude
        place.radius_m = radius_m
        place.is_safe_zone = is_safe_zone
        self.db.flush()
        return place

    def delete_place_for_family_slug(self, family_slug: str, place_id: UUID) -> bool:
        place = self.get_place_for_family_slug(family_slug, place_id)
        if place is None:
            return False
        self.db.delete(place)
        self.db.flush()
        return True

    def resolve_member_by_source_entity(self, source_entity_id: str) -> Member | None:
        stmt: Select[tuple[Member]] = (
            select(Member)
            .join(Device, Device.member_id == Member.id)
            .where(Device.external_id == source_entity_id)
        )
        return self.db.scalar(stmt)

    def get_device_by_external_id(self, external_id: str) -> Device | None:
        stmt: Select[tuple[Device]] = select(Device).where(Device.external_id == external_id)
        return self.db.scalar(stmt)

    def get_device_for_member(self, member_id: UUID, device_id: UUID) -> Device | None:
        stmt: Select[tuple[Device]] = (
            select(Device)
            .where(Device.member_id == member_id)
            .where(Device.id == device_id)
        )
        return self.db.scalar(stmt)

    def get_device_for_family_slug(
        self,
        family_slug: str,
        member_id: UUID,
        device_id: UUID,
    ) -> Device | None:
        stmt: Select[tuple[Device]] = (
            select(Device)
            .join(Member, Device.member_id == Member.id)
            .join(Family, Member.family_id == Family.id)
            .where(Family.slug == family_slug)
            .where(Member.id == member_id)
            .where(Device.id == device_id)
        )
        return self.db.scalar(stmt)

    def upsert_device_for_member(
        self,
        member: Member,
        provider: str,
        external_id: str,
        label: str | None,
        ignored: bool | None = None,
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
        if ignored is not None:
            device.ignored = ignored
        device.last_seen_at = member.last_seen_at
        return device

    def set_device_ignored(self, member_id: UUID, device_id: UUID, ignored: bool) -> Device | None:
        device = self.get_device_for_member(member_id, device_id)
        if device is None:
            return None
        device.ignored = ignored
        self.db.flush()
        return device

    def update_member_for_family_slug(
        self,
        family_slug: str,
        member_id: UUID,
        *,
        display_name: str | None,
        is_child: bool | None,
        avatar_color: str | None,
    ) -> Member | None:
        member = self.get_member_for_family_slug(family_slug, member_id)
        if member is None:
            return None
        if display_name is not None:
            member.display_name = display_name
        if is_child is not None:
            member.is_child = is_child
        if avatar_color is not None:
            member.avatar_color = avatar_color
        self.db.flush()
        return member

    def update_device_for_family_slug(
        self,
        family_slug: str,
        member_id: UUID,
        device_id: UUID,
        *,
        label: str | None,
        ignored: bool | None,
    ) -> Device | None:
        device = self.get_device_for_family_slug(family_slug, member_id, device_id)
        if device is None:
            return None
        if label is not None:
            device.label = label
        if ignored is not None:
            device.ignored = ignored
        self.db.flush()
        return device

    def commit(self) -> None:
        self.db.commit()

    def get_provider_status(self, provider: str) -> ProviderStatus | None:
        stmt: Select[tuple[ProviderStatus]] = select(ProviderStatus).where(ProviderStatus.provider == provider)
        return self.db.scalar(stmt)

    def upsert_provider_status(
        self,
        provider: str,
        *,
        state: str | None = None,
        last_snapshot_at: datetime | None = None,
        last_connected_at: datetime | None = None,
        last_event_at: datetime | None = None,
        last_error_at: datetime | None = None,
        last_error_message: str | None = None,
        retry_delay_seconds: int | None = None,
    ) -> ProviderStatus:
        row = self.get_provider_status(provider)
        if row is None:
            row = ProviderStatus(provider=provider)
            self.db.add(row)

        if state is not None:
            row.state = state
        if last_snapshot_at is not None:
            row.last_snapshot_at = last_snapshot_at
        if last_connected_at is not None:
            row.last_connected_at = last_connected_at
        if last_event_at is not None:
            row.last_event_at = last_event_at
        row.last_error_at = last_error_at
        row.last_error_message = last_error_message
        row.retry_delay_seconds = retry_delay_seconds
        self.db.flush()
        return row

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

    def replace_safety_events_for_range(
        self,
        member_id: UUID,
        start: datetime,
        end: datetime,
        events: list[dict],
    ) -> None:
        self.db.execute(
            delete(SafetyEvent)
            .where(SafetyEvent.member_id == member_id)
            .where(SafetyEvent.observed_at >= start)
            .where(SafetyEvent.observed_at <= end),
        )
        for event in events:
            self.db.add(
                SafetyEvent(
                    member_id=member_id,
                    place_id=event.get("place_id"),
                    event_type=event["event_type"],
                    severity=event["severity"],
                    observed_at=event["observed_at"],
                    payload=event["payload"],
                )
            )
        self.db.flush()

    def list_safety_events_for_range(
        self,
        member_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[SafetyEvent]:
        stmt: Select[tuple[SafetyEvent]] = (
            select(SafetyEvent)
            .where(SafetyEvent.member_id == member_id)
            .where(SafetyEvent.observed_at >= start)
            .where(SafetyEvent.observed_at <= end)
            .order_by(SafetyEvent.observed_at.asc())
        )
        return list(self.db.scalars(stmt))

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

    def list_recent_location_points(self, limit: int) -> list[LocationPoint]:
        stmt: Select[tuple[LocationPoint]] = (
            select(LocationPoint)
            .order_by(LocationPoint.observed_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def get_reverse_geocode_cache(
        self,
        latitude_rounded: float,
        longitude_rounded: float,
    ) -> ReverseGeocodeCache | None:
        stmt: Select[tuple[ReverseGeocodeCache]] = (
            select(ReverseGeocodeCache)
            .where(ReverseGeocodeCache.latitude_rounded == latitude_rounded)
            .where(ReverseGeocodeCache.longitude_rounded == longitude_rounded)
        )
        return self.db.scalar(stmt)

    def enqueue_reverse_geocode_cache(
        self,
        latitude_rounded: float,
        longitude_rounded: float,
    ) -> tuple[ReverseGeocodeCache, bool]:
        row = self.get_reverse_geocode_cache(latitude_rounded, longitude_rounded)
        if row is not None:
            return row, False

        row = ReverseGeocodeCache(
            latitude_rounded=latitude_rounded,
            longitude_rounded=longitude_rounded,
        )
        self.db.add(row)
        self.db.flush()
        return row, True

    def list_pending_reverse_geocode_cache(
        self,
        limit: int,
        retry_before: datetime,
    ) -> list[ReverseGeocodeCache]:
        stmt: Select[tuple[ReverseGeocodeCache]] = (
            select(ReverseGeocodeCache)
            .where(ReverseGeocodeCache.payload.is_(None))
            .where(
                or_(
                    ReverseGeocodeCache.last_attempted_at.is_(None),
                    ReverseGeocodeCache.last_attempted_at <= retry_before,
                )
            )
            .order_by(ReverseGeocodeCache.created_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def mark_reverse_geocode_cache_resolved(
        self,
        row: ReverseGeocodeCache,
        payload: dict,
        resolved_at: datetime,
    ) -> None:
        row.payload = payload
        row.resolved_at = resolved_at
        row.last_attempted_at = resolved_at
        row.failure_count = 0
        self.db.flush()

    def mark_reverse_geocode_cache_failed(
        self,
        row: ReverseGeocodeCache,
        attempted_at: datetime,
    ) -> None:
        row.last_attempted_at = attempted_at
        row.failure_count += 1
        self.db.flush()

    def get_latest_point_for_member(self, member_id: UUID) -> LocationPoint | None:
        stmt: Select[tuple[LocationPoint]] = (
            select(LocationPoint)
            .where(LocationPoint.member_id == member_id)
            .order_by(LocationPoint.observed_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_latest_point_for_source_entity(self, source_entity_id: str) -> LocationPoint | None:
        stmt: Select[tuple[LocationPoint]] = (
            select(LocationPoint)
            .where(LocationPoint.source_entity_id == source_entity_id)
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
            .where(LocationPoint.observed_at < end)
            .order_by(LocationPoint.observed_at.asc())
        )
        return list(self.db.scalars(stmt))

    def list_points_for_member_on_date(self, member_id: UUID, start: datetime, end: datetime) -> list[LocationPoint]:
        stmt: Select[tuple[LocationPoint]] = (
            select(LocationPoint)
            .where(LocationPoint.member_id == member_id)
            .where(LocationPoint.observed_at >= start)
            .where(LocationPoint.observed_at < end)
            .order_by(LocationPoint.observed_at.asc())
        )
        return list(self.db.scalars(stmt))

    def replace_member_day_trips(self, member_id: UUID, trip_date: date, trips: list[dict]) -> list[Trip]:
        day_start = datetime.combine(trip_date, time.min, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        self.db.execute(
            delete(Trip)
            .where(Trip.member_id == member_id)
            .where(Trip.started_at >= day_start)
            .where(Trip.started_at < day_end),
        )
        stored = []
        for trip in trips:
            row = Trip(
                member_id=member_id,
                started_at=trip["started_at"],
                ended_at=trip["ended_at"],
                point_count=trip["point_count"],
                distance_m=trip["distance_m"],
                start_label=trip.get("start_label"),
                end_label=trip.get("end_label"),
            )
            self.db.add(row)
            stored.append(row)
        self.db.flush()
        return stored

    def list_trips_for_member_on_date(self, member_id: UUID, trip_date: date) -> list[Trip]:
        day_start = datetime.combine(trip_date, time.min, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        stmt: Select[tuple[Trip]] = (
            select(Trip)
            .where(Trip.member_id == member_id)
            .where(Trip.started_at >= day_start)
            .where(Trip.started_at < day_end)
            .order_by(Trip.started_at.asc())
        )
        return list(self.db.scalars(stmt))

    def list_trips_for_member_range(
        self,
        member_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[Trip]:
        stmt: Select[tuple[Trip]] = (
            select(Trip)
            .where(Trip.member_id == member_id)
            .where(Trip.started_at >= start)
            .where(Trip.started_at < end)
            .order_by(Trip.started_at.asc())
        )
        return list(self.db.scalars(stmt))

    def get_trip_for_member(self, member_id: UUID, trip_id: UUID) -> Trip | None:
        stmt: Select[tuple[Trip]] = (
            select(Trip)
            .where(Trip.member_id == member_id)
            .where(Trip.id == trip_id)
        )
        return self.db.scalar(stmt)

    def replace_daily_summary(self, member_id: UUID, summary: dict) -> DailySummary:
        self.db.execute(
            delete(DailySummary)
            .where(DailySummary.member_id == member_id)
            .where(DailySummary.summary_date == summary["summary_date"]),
        )
        row = DailySummary(
            member_id=member_id,
            summary_date=summary["summary_date"],
            first_seen_at=summary["first_seen_at"],
            last_seen_at=summary["last_seen_at"],
            trip_count=summary["trip_count"],
            total_distance_m=summary["total_distance_m"],
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_daily_summary_for_member(self, member_id: UUID, summary_date: date) -> DailySummary | None:
        stmt: Select[tuple[DailySummary]] = (
            select(DailySummary)
            .where(DailySummary.member_id == member_id)
            .where(DailySummary.summary_date == summary_date)
        )
        return self.db.scalar(stmt)
