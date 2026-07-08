from datetime import UTC, datetime
from uuid import UUID

from app.domain.events import NormalizedLocationEvent
from app.models.location import LocationPoint
from app.repositories.location_repository import LocationRepository


class LocationService:
    def __init__(self, repository: LocationRepository) -> None:
        self.repository = repository

    def ingest(
        self,
        event: NormalizedLocationEvent,
        received_at: datetime | None = None,
    ) -> LocationPoint | dict | None:
        member = self.repository.resolve_member_by_source_entity(event.source_entity_id)
        if member is None:
            return None

        device = None
        device_external_id = event.source_entity_id
        if device_external_id:
            device = self.repository.upsert_device_for_member(
                member=member,
                provider=event.provider.value,
                external_id=device_external_id,
                label=event.source_device_name,
            )

        received_at = received_at or datetime.now(UTC)
        if hasattr(member, "last_seen_at"):
            member.last_seen_at = event.observed_at
        if device is not None and hasattr(device, "last_seen_at"):
            device.last_seen_at = event.observed_at

        point = LocationPoint(
            member_id=member["id"] if isinstance(member, dict) else member.id,
            device_id=device.get("id") if isinstance(device, dict) else getattr(device, "id", None),
            provider=event.provider.value,
            source_entity_id=event.source_entity_id,
            observed_at=event.observed_at,
            received_at=received_at,
            latitude=event.latitude,
            longitude=event.longitude,
            altitude_m=event.altitude_m,
            accuracy_m=event.accuracy_m,
            battery_level=event.battery_level,
            is_charging=event.is_charging,
        )
        stored = self.repository.add_location_point(point)
        if hasattr(self.repository, "commit"):
            self.repository.commit()
        return stored

    def get_latest_location(self, member_id: UUID):
        return self.repository.get_latest_point_for_member(member_id)

    def get_history(self, member_id: UUID, start: datetime, end: datetime):
        return self.repository.list_member_history(member_id, start, end)
