from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.events import NormalizedLocationEvent, ProviderName
from app.services.locations import LocationService


class FakeLocationRepository:
    def __init__(self) -> None:
        self.family = None
        self.members = {}
        self.devices = {}
        self.points = []
        self.stays = []
        self.reverse_geocode_cache = {}

    def resolve_member_by_source_entity(self, source_entity_id: str):
        return self.members.get(source_entity_id)

    def get_device_by_external_id(self, external_id: str):
        return self.devices.get(external_id)

    def ensure_family(self, family_slug: str, family_name: str):
        self.family = {"id": "family-1", "slug": family_slug, "name": family_name}
        return self.family

    def ensure_member(self, family, display_name: str, is_child: bool, avatar_color: str | None):
        member = self.members.get(display_name)
        if member is None:
            member = {
                "id": uuid4(),
                "family": family,
                "display_name": display_name,
                "is_child": is_child,
                "avatar_color": avatar_color,
            }
            self.members[display_name] = member
        return member

    def upsert_device_for_member(
        self,
        member,
        provider: str,
        external_id: str,
        label: str | None,
        ignored: bool | None = None,
    ):
        device = {
            "id": external_id,
            "member_id": member["id"],
            "provider": provider,
            "external_id": external_id,
            "label": label,
            "ignored": ignored if ignored is not None else False,
        }
        self.devices[external_id] = device
        self.members[external_id] = member
        return device

    def add_location_point(self, point):
        self.points.append(point)
        return point

    def list_member_history(self, member_id, start, end):
        return [
            point
            for point in self.points
            if point.member_id == member_id and start <= point.observed_at <= end
        ]

    def list_points_for_member_on_date(self, member_id, start, end):
        return [
            point
            for point in self.points
            if point.member_id == member_id and start <= point.observed_at < end
        ]

    def replace_member_day_stays(self, member_id, target_date, stays):
        self.stays = list(stays)
        return self.stays

    def get_latest_point_for_member(self, member_id):
        matching = [point for point in self.points if point.member_id == member_id]
        if not matching:
            return None
        return sorted(matching, key=lambda item: item.observed_at, reverse=True)[0]

    def get_latest_point_for_source_entity(self, source_entity_id: str):
        matching = [point for point in self.points if point.source_entity_id == source_entity_id]
        if not matching:
            return None
        return sorted(matching, key=lambda item: item.observed_at, reverse=True)[0]

    def enqueue_reverse_geocode_cache(self, latitude_rounded: float, longitude_rounded: float):
        key = (latitude_rounded, longitude_rounded)
        created = key not in self.reverse_geocode_cache
        self.reverse_geocode_cache[key] = {
            "latitude_rounded": latitude_rounded,
            "longitude_rounded": longitude_rounded,
        }
        return self.reverse_geocode_cache[key], created

    def commit(self):
        return None


class FakeReverseGeocodeCache:
    def __init__(self) -> None:
        self.calls = []

    def queue_lookup(self, latitude: float, longitude: float) -> None:
        self.calls.append((latitude, longitude))


def test_ingest_location_event_persists_point_for_known_member() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    reverse_geocode_cache = FakeReverseGeocodeCache()

    event = NormalizedLocationEvent(
        provider=ProviderName.HOME_ASSISTANT,
        source_entity_id="device_tracker.sam_phone",
        source_device_id="pixel-8",
        source_device_name="Sam Phone",
        observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
        latitude=37.42,
        longitude=-122.08,
        battery_level=81,
        raw_payload={"event": "x"},
    )

    service = LocationService(repository, reverse_geocode_cache=reverse_geocode_cache)
    stored = service.ingest(event, received_at=datetime(2026, 7, 8, 21, 0, 2, tzinfo=UTC))

    assert stored.member_id == member_id
    assert stored.provider == "home_assistant"
    assert stored.battery_level == 81
    assert repository.devices["device_tracker.sam_phone"]["label"] == "Sam Phone"
    assert reverse_geocode_cache.calls == [(37.42, -122.08)]


def test_ingest_location_event_ignores_unknown_member_mapping() -> None:
    repository = FakeLocationRepository()
    service = LocationService(repository)

    event = NormalizedLocationEvent(
        provider=ProviderName.HOME_ASSISTANT,
        source_entity_id="device_tracker.unknown_phone",
        source_device_id="unknown-device",
        source_device_name="Unknown",
        observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
        latitude=37.42,
        longitude=-122.08,
    )

    assert service.ingest(event) is None
    assert repository.points == []


def test_ingest_location_event_auto_discovers_unknown_member() -> None:
    repository = FakeLocationRepository()
    service = LocationService(
        repository,
        auto_discovery_family_slug="family-alpha",
        auto_discovery_family_name="Family Alpha",
    )

    event = NormalizedLocationEvent(
        provider=ProviderName.HOME_ASSISTANT,
        source_entity_id="device_tracker.pixel_10_pro",
        source_device_name="Kristi",
        observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
        latitude=37.42,
        longitude=-122.08,
    )

    stored = service.ingest(event)

    assert stored is not None
    assert repository.family == {
        "id": "family-1",
        "slug": "family-alpha",
        "name": "Family Alpha",
    }
    assert repository.devices["device_tracker.pixel_10_pro"]["label"] == "Kristi"
    assert repository.points[0].source_entity_id == "device_tracker.pixel_10_pro"


def test_ingest_location_event_skips_ignored_device() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    repository.devices["device_tracker.sam_phone"] = {
        "id": "device_tracker.sam_phone",
        "member_id": member_id,
        "provider": "home_assistant",
        "external_id": "device_tracker.sam_phone",
        "label": "Sam Phone",
        "ignored": True,
    }
    service = LocationService(repository)

    event = NormalizedLocationEvent(
        provider=ProviderName.HOME_ASSISTANT,
        source_entity_id="device_tracker.sam_phone",
        observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
        latitude=37.42,
        longitude=-122.08,
    )

    assert service.ingest(event) is None
    assert repository.points == []


def test_latest_and_history_views_are_ordered_by_observed_at() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    service = LocationService(repository)
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)

    for minute in (0, 15, 45):
        service.ingest(
            NormalizedLocationEvent(
                provider=ProviderName.HOME_ASSISTANT,
                source_entity_id="device_tracker.sam_phone",
                observed_at=start + timedelta(minutes=minute),
                latitude=37.42 + minute / 1000,
                longitude=-122.08,
            ),
            received_at=start + timedelta(minutes=minute, seconds=2),
        )

    latest = service.get_latest_location(member_id)
    history = service.get_history(member_id, start, start + timedelta(hours=1))

    assert latest is not None
    assert latest.observed_at == start + timedelta(minutes=45)
    assert [point.observed_at for point in history] == [
        start,
        start + timedelta(minutes=15),
        start + timedelta(minutes=45),
    ]


def test_ingest_suppresses_near_duplicate_point_within_dedupe_window() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    service = LocationService(repository)
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)

    first = service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=start,
            latitude=37.4200,
            longitude=-122.0800,
            accuracy_m=10.0,
        ),
        received_at=start,
    )
    second = service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=start + timedelta(minutes=5),
            latitude=37.42003,
            longitude=-122.08003,
            accuracy_m=12.0,
        ),
        received_at=start + timedelta(minutes=5),
    )

    assert first is not None
    assert second is None
    assert len(repository.points) == 1


def test_ingest_keeps_point_when_member_actually_moved() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    service = LocationService(repository)
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)

    service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=start,
            latitude=37.4200,
            longitude=-122.0800,
            accuracy_m=10.0,
        ),
        received_at=start,
    )
    stored = service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=start + timedelta(minutes=5),
            latitude=37.4212,
            longitude=-122.0800,
            accuracy_m=10.0,
        ),
        received_at=start + timedelta(minutes=5),
    )

    assert stored is not None
    assert len(repository.points) == 2


def test_ingest_keeps_periodic_stationary_sample_after_dedupe_window() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    service = LocationService(repository)
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)

    service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=start,
            latitude=37.4200,
            longitude=-122.0800,
            accuracy_m=10.0,
        ),
        received_at=start,
    )
    stored = service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=start + timedelta(minutes=20),
            latitude=37.42003,
            longitude=-122.08003,
            accuracy_m=12.0,
        ),
        received_at=start + timedelta(minutes=20),
    )

    assert stored is not None
    assert len(repository.points) == 2


def test_ingest_rebuilds_member_day_stays_after_persisting_point(monkeypatch) -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    calls = []

    class FakeStayDerivationService:
        def __init__(self, repository_arg) -> None:
            assert repository_arg is repository

        def rebuild_member_day(self, member_id_arg, target_date) -> None:
            calls.append((member_id_arg, target_date))

    monkeypatch.setattr("app.services.locations.StayDerivationService", FakeStayDerivationService)

    service = LocationService(repository)
    observed_at = datetime(2026, 7, 8, 21, 0, tzinfo=UTC)
    stored = service.ingest(
        NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=observed_at,
            latitude=37.4200,
            longitude=-122.0800,
            accuracy_m=10.0,
        ),
        received_at=observed_at,
    )

    assert stored is not None
    assert calls == [(member_id, observed_at.date())]
