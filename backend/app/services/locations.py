from datetime import UTC, datetime
from uuid import UUID

from app.core.config import get_settings
from app.domain.events import NormalizedLocationEvent
from app.models.location import LocationPoint
from app.repositories.location_repository import LocationRepository
from app.services.places import haversine_m
from app.services.reverse_geocode_cache import ReverseGeocodeCacheService


class LocationService:
    def __init__(
        self,
        repository: LocationRepository,
        auto_discovery_family_slug: str | None = None,
        auto_discovery_family_name: str | None = None,
        reverse_geocode_cache: ReverseGeocodeCacheService | None = None,
        dedupe_window_seconds: int | None = None,
        dedupe_min_distance_m: float | None = None,
        dedupe_max_distance_m: float | None = None,
    ) -> None:
        settings = get_settings()
        self.repository = repository
        self.auto_discovery_family_slug = auto_discovery_family_slug
        self.auto_discovery_family_name = auto_discovery_family_name
        self.reverse_geocode_cache = reverse_geocode_cache or ReverseGeocodeCacheService(repository)
        self.dedupe_window_seconds = (
            settings.location_dedupe_window_seconds if dedupe_window_seconds is None else dedupe_window_seconds
        )
        self.dedupe_min_distance_m = (
            settings.location_dedupe_min_distance_m if dedupe_min_distance_m is None else dedupe_min_distance_m
        )
        self.dedupe_max_distance_m = (
            settings.location_dedupe_max_distance_m if dedupe_max_distance_m is None else dedupe_max_distance_m
        )

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

        previous_point = self._latest_source_point(event.source_entity_id, member)
        if self._should_suppress_duplicate(previous_point, event):
            if hasattr(self.repository, "commit"):
                self.repository.commit()
            return None

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
        if self.reverse_geocode_cache is not None:
            self.reverse_geocode_cache.queue_lookup(event.latitude, event.longitude)
        if hasattr(self.repository, "commit"):
            self.repository.commit()
        return stored

    def get_latest_location(self, member_id: UUID):
        return self.repository.get_latest_point_for_member(member_id)

    def get_history(self, member_id: UUID, start: datetime, end: datetime):
        return self.repository.list_member_history(member_id, start, end)

    def _latest_source_point(self, source_entity_id: str, member):
        if source_entity_id and hasattr(self.repository, "get_latest_point_for_source_entity"):
            return self.repository.get_latest_point_for_source_entity(source_entity_id)
        member_id = member["id"] if isinstance(member, dict) else member.id
        return self.repository.get_latest_point_for_member(member_id)

    def _should_suppress_duplicate(
        self,
        previous_point,
        event: NormalizedLocationEvent,
    ) -> bool:
        if previous_point is None:
            return False

        interval_seconds = (event.observed_at - previous_point.observed_at).total_seconds()
        if interval_seconds <= 0 or interval_seconds > self.dedupe_window_seconds:
            return False

        distance_m = haversine_m(
            previous_point.latitude,
            previous_point.longitude,
            event.latitude,
            event.longitude,
        )
        threshold_m = self._dedupe_distance_threshold(
            event.accuracy_m,
            getattr(previous_point, "accuracy_m", None),
        )
        return distance_m <= threshold_m

    def _dedupe_distance_threshold(
        self,
        current_accuracy_m: float | None,
        previous_accuracy_m: float | None,
    ) -> float:
        candidate = max(
            self.dedupe_min_distance_m,
            current_accuracy_m or 0.0,
            previous_accuracy_m or 0.0,
        )
        return min(self.dedupe_max_distance_m, candidate)

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
