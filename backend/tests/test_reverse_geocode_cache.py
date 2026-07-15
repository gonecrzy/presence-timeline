from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.reverse_geocode_cache import ReverseGeocodeCacheService


class FakeReverseGeocodeRepository:
    def __init__(self) -> None:
        self.cache = {}
        self.recent_points = []
        self.pending = []
        self.committed = False

    def get_reverse_geocode_cache(self, latitude_rounded: float, longitude_rounded: float):
        return self.cache.get((latitude_rounded, longitude_rounded))

    def enqueue_reverse_geocode_cache(self, latitude_rounded: float, longitude_rounded: float):
        key = (latitude_rounded, longitude_rounded)
        row = self.cache.get(key)
        if row is None:
            row = SimpleNamespace(
                latitude_rounded=latitude_rounded,
                longitude_rounded=longitude_rounded,
                payload=None,
                last_attempted_at=None,
                failure_count=0,
                resolved_at=None,
            )
            self.cache[key] = row
            self.pending.append(row)
            return row, True
        return row, False

    def list_recent_location_points(self, limit: int):
        return self.recent_points[:limit]

    def list_pending_reverse_geocode_cache(self, limit: int, retry_before: datetime):
        return [
            row
            for row in self.pending
            if row.payload is None
            and (row.last_attempted_at is None or row.last_attempted_at <= retry_before)
        ][:limit]

    def mark_reverse_geocode_cache_resolved(self, row, payload: dict, resolved_at: datetime):
        row.payload = payload
        row.resolved_at = resolved_at
        row.last_attempted_at = resolved_at

    def mark_reverse_geocode_cache_failed(self, row, attempted_at: datetime):
        row.last_attempted_at = attempted_at
        row.failure_count += 1

    def commit(self) -> None:
        self.committed = True


class FakePayloadGeocoder:
    def __init__(self, payloads: dict[tuple[float, float], dict | None]) -> None:
        self.payloads = payloads
        self.calls = []

    def reverse_payload(self, latitude: float, longitude: float) -> dict | None:
        self.calls.append((latitude, longitude))
        return self.payloads.get((latitude, longitude))


def test_reverse_geocode_cache_service_backfills_recent_points_with_unique_rounded_coordinates() -> None:
    repository = FakeReverseGeocodeRepository()
    repository.recent_points = [
        SimpleNamespace(latitude=37.43004, longitude=-122.09004),
        SimpleNamespace(latitude=37.43001, longitude=-122.09001),
        SimpleNamespace(latitude=37.43111, longitude=-122.09111),
    ]
    service = ReverseGeocodeCacheService(repository, reverse_geocoder=FakePayloadGeocoder({}))

    queued = service.backfill_recent_points(limit=10)

    assert queued == 2
    assert sorted(repository.cache) == [
        (37.43, -122.09),
        (37.4311, -122.0911),
    ]
    assert repository.committed is True


def test_reverse_geocode_cache_service_resolves_pending_payloads_and_formats_cached_labels() -> None:
    repository = FakeReverseGeocodeRepository()
    row, _ = repository.enqueue_reverse_geocode_cache(37.4301, -122.0901)
    geocoder = FakePayloadGeocoder(
        {
            (37.4301, -122.0901): {
                "display_name": "129 Sundance Court, Sangaree, South Carolina 29486",
                "address": {
                    "house_number": "129",
                    "road": "Sundance Court",
                    "suburb": "Sangaree",
                    "state": "South Carolina",
                    "postcode": "29486",
                },
            }
        }
    )
    service = ReverseGeocodeCacheService(repository, reverse_geocoder=geocoder)

    results = service.resolve_pending(
        limit=10,
        now=datetime(2026, 7, 11, 5, 0, tzinfo=UTC),
    )

    assert results == {"resolved": 1, "failed": 0}
    assert row.payload is not None
    assert service.lookup_label(37.4301, -122.0901, granularity="block") == "100 block of Sundance Court, Sangaree"
    assert geocoder.calls == [(37.4301, -122.0901)]


def test_reverse_geocode_cache_service_defers_retry_after_failure() -> None:
    repository = FakeReverseGeocodeRepository()
    row, _ = repository.enqueue_reverse_geocode_cache(37.4301, -122.0901)
    geocoder = FakePayloadGeocoder({(37.4301, -122.0901): None})
    service = ReverseGeocodeCacheService(repository, reverse_geocoder=geocoder)

    first = service.resolve_pending(limit=10, now=datetime(2026, 7, 11, 5, 0, tzinfo=UTC))
    second = service.resolve_pending(limit=10, now=datetime(2026, 7, 11, 5, 5, tzinfo=UTC))
    third = service.resolve_pending(limit=10, now=datetime(2026, 7, 11, 5, 20, tzinfo=UTC))

    assert first == {"resolved": 0, "failed": 1}
    assert second == {"resolved": 0, "failed": 0}
    assert third == {"resolved": 0, "failed": 1}
    assert row.failure_count == 2
    assert geocoder.calls == [(37.4301, -122.0901), (37.4301, -122.0901)]
