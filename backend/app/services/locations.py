from datetime import UTC, datetime
from uuid import UUID

from app.domain.events import NormalizedLocationEvent
from app.models.location import LocationPoint
from app.repositories.location_repository import LocationRepository


class LocationService:
    def __init__(
        self,
        repository: LocationRepository,
        auto_discovery_family_slug: str | None = None,
        auto_discovery_family_name: str | None = None,
    ) -> None:
        self.repository = repository
        self.auto_discovery_family_slug = auto_discovery_family_slug
        self.auto_discovery_family_name = auto_discovery_family_name

    def ingest(
        self,
        event: NormalizedLocationEvent,
        received_at: datetime | None = None,
    ) -> LocationPoint | dict | None:
        device = self.repository.get_device_by_external_id(event.source_entity_id)
        if _is_ignored(device):
            return None

        member = self.repository.resolve_member_by_source_entity(event.source_entity_id)
        if member is None:
            member, device = self._auto_discover_member_device(event)
            if member is None:
                return None

        device_external_id = event.source_entity_id
        if device is None and device_external_id:
            device = self.repository.upsert_device_for_member(
                member=member,
                provider=event.provider.value,
                external_id=device_external_id,
                label=event.source_device_name,
            )
        if _is_ignored(device):
            return None

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

    def _auto_discover_member_device(
        self,
        event: NormalizedLocationEvent,
    ):
        if not self.auto_discovery_family_slug or not self.auto_discovery_family_name:
            return None, None

        family = self.repository.ensure_family(
            family_slug=self.auto_discovery_family_slug,
            family_name=self.auto_discovery_family_name,
        )
        display_name = event.source_device_name or _display_name_from_entity_id(event.source_entity_id)
        member = self.repository.ensure_member(
            family=family,
            display_name=display_name,
            is_child=False,
            avatar_color=None,
        )
        device = self.repository.upsert_device_for_member(
            member=member,
            provider=event.provider.value,
            external_id=event.source_entity_id,
            label=event.source_device_name or display_name,
            ignored=False,
        )
        return member, device


def _display_name_from_entity_id(entity_id: str) -> str:
    slug = entity_id.split(".", 1)[-1]
    return slug.replace("_", " ").replace("-", " ").title()


def _is_ignored(device) -> bool:
    if device is None:
        return False
    if isinstance(device, dict):
        return bool(device.get("ignored", False))
    return bool(getattr(device, "ignored", False))
