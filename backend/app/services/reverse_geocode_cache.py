from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.services.places import ReverseGeocoder, format_reverse_geocode_label


class ReverseGeocodeCacheService:
    def __init__(
        self,
        repository,
        *,
        reverse_geocoder: ReverseGeocoder | None = None,
        precision: int | None = None,
        retry_after: timedelta | None = None,
    ) -> None:
        settings = get_settings()
        self.repository = repository
        self.reverse_geocoder = reverse_geocoder or ReverseGeocoder()
        self.precision = (
            settings.reverse_geocode_cache_precision if precision is None else precision
        )
        self.retry_after = (
            timedelta(minutes=settings.reverse_geocode_retry_minutes)
            if retry_after is None
            else retry_after
        )

    def lookup_label(self, latitude: float, longitude: float, *, granularity: str) -> str | None:
        payload = self.lookup_payload(latitude, longitude)
        if payload is None:
            return None
        return format_reverse_geocode_label(payload, granularity=granularity) or payload.get(
            "display_name"
        )

    def lookup_payload(self, latitude: float, longitude: float) -> dict | None:
        latitude_rounded, longitude_rounded = self._rounded_coordinates(latitude, longitude)
        row = self.repository.get_reverse_geocode_cache(latitude_rounded, longitude_rounded)
        if row is None or row.payload is None:
            return None
        return row.payload

    def queue_lookup(self, latitude: float, longitude: float) -> bool:
        latitude_rounded, longitude_rounded = self._rounded_coordinates(latitude, longitude)
        _, created = self.repository.enqueue_reverse_geocode_cache(
            latitude_rounded,
            longitude_rounded,
        )
        return created

    def backfill_recent_points(self, *, limit: int) -> int:
        queued = 0
        seen: set[tuple[float, float]] = set()
        for point in self.repository.list_recent_location_points(limit):
            coordinates = self._rounded_coordinates(point.latitude, point.longitude)
            if coordinates in seen:
                continue
            seen.add(coordinates)
            _, created = self.repository.enqueue_reverse_geocode_cache(*coordinates)
            queued += int(created)
        self.repository.commit()
        return queued

    def resolve_pending(
        self,
        *,
        limit: int,
        now: datetime | None = None,
    ) -> dict[str, int]:
        now = now or datetime.now(UTC)
        retry_before = now - self.retry_after
        resolved = 0
        failed = 0
        for row in self.repository.list_pending_reverse_geocode_cache(limit, retry_before):
            payload = self.reverse_geocoder.reverse_payload(
                row.latitude_rounded,
                row.longitude_rounded,
            )
            if payload is None:
                self.repository.mark_reverse_geocode_cache_failed(row, now)
                failed += 1
                continue
            self.repository.mark_reverse_geocode_cache_resolved(row, payload, now)
            resolved += 1
        self.repository.commit()
        return {"resolved": resolved, "failed": failed}

    def _rounded_coordinates(self, latitude: float, longitude: float) -> tuple[float, float]:
        return round(latitude, self.precision), round(longitude, self.precision)
