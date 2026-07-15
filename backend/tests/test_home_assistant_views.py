from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.services.home_assistant_views import HomeAssistantViewService


class FakeHomeAssistantRepository:
    def __init__(self) -> None:
        self.member = SimpleNamespace(
            id=uuid4(),
            family_id=uuid4(),
            display_name="Sam",
            is_child=True,
            last_seen_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            devices=[],
        )
        self.points = [
            SimpleNamespace(
                member_id=self.member.id,
                observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
                latitude=37.4300,
                longitude=-122.0900,
                accuracy_m=18.0,
                battery_level=82,
                source_entity_id="device_tracker.sam_phone",
            ),
            SimpleNamespace(
                member_id=self.member.id,
                observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
                latitude=37.4301,
                longitude=-122.0901,
                accuracy_m=19.0,
                battery_level=81,
                source_entity_id="device_tracker.sam_phone",
            ),
            SimpleNamespace(
                member_id=self.member.id,
                observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
                latitude=37.4301,
                longitude=-122.0901,
                accuracy_m=18.0,
                battery_level=80,
                source_entity_id="device_tracker.sam_phone",
            ),
        ]
        self.events = []
        self.trips = []
        self.mirrored_member = SimpleNamespace(
            id=uuid4(),
            family_id=self.member.family_id,
            display_name="Sam Location",
            is_child=False,
            last_seen_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            devices=[
                SimpleNamespace(
                    id=uuid4(),
                    provider="home_assistant",
                    external_id="device_tracker.sam_location",
                    label="Sam Location",
                    ignored=False,
                    last_seen_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
                )
            ],
        )
        self.mirrored_points = [
            SimpleNamespace(
                member_id=self.mirrored_member.id,
                observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
                latitude=37.4301,
                longitude=-122.0901,
                accuracy_m=18.0,
                battery_level=80,
                source_entity_id="device_tracker.sam_location",
            )
        ]
        self.provider_status = SimpleNamespace(
            provider="home_assistant",
            state="connected",
            last_snapshot_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            last_connected_at=datetime(2026, 7, 8, 20, 1, tzinfo=UTC),
            last_event_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            last_error_at=None,
            last_error_message=None,
            retry_delay_seconds=None,
        )
        self.stays = [
            SimpleNamespace(
                member_id=self.member.id,
                started_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
                ended_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
                latitude=37.4301,
                longitude=-122.0901,
                point_count=3,
                accuracy_m=18.0,
            )
        ]

    def list_members_for_family_slug(self, family_slug: str):
        assert family_slug == "family-alpha"
        return [self.member, self.mirrored_member]

    def get_latest_point_for_member(self, member_id):
        if member_id == self.member.id:
            return self.points[-1]
        assert member_id == self.mirrored_member.id
        return self.mirrored_points[-1]

    def get_member(self, member_id):
        if member_id == self.member.id:
            return self.member
        assert member_id == self.mirrored_member.id
        return self.mirrored_member

    def list_places_for_family_id(self, family_id):
        assert family_id == self.member.family_id
        return []

    def list_member_history(self, member_id, start, end):
        if member_id == self.member.id:
            return [point for point in self.points if start <= point.observed_at < end]
        assert member_id == self.mirrored_member.id
        return [point for point in self.mirrored_points if start <= point.observed_at < end]

    def list_stays_for_member_range(self, member_id, start, end):
        assert member_id == self.member.id
        return [
            stay
            for stay in self.stays
            if stay.started_at < end and stay.ended_at >= start
        ]

    def get_reverse_geocode_cache(self, latitude_rounded: float, longitude_rounded: float):
        return None

    def enqueue_reverse_geocode_cache(self, latitude_rounded: float, longitude_rounded: float):
        row = SimpleNamespace(payload=None)
        return row, True

    def replace_safety_events_for_range(self, member_id, start, end, events):
        assert member_id == self.member.id
        self.events = []

    def commit(self) -> None:
        return None

    def list_safety_events_for_range(self, member_id, start, end):
        assert member_id == self.member.id
        return self.events

    def list_trips_for_member_range(self, member_id, start, end):
        assert member_id == self.member.id
        return self.trips

    def get_provider_status(self, provider: str):
        assert provider == "home_assistant"
        return self.provider_status


class ExplodingReverseGeocoder:
    def reverse(self, latitude: float, longitude: float, *, granularity: str = "full") -> str | None:
        raise AssertionError("reverse geocoder should not be called")


class FakeReverseGeocodeCache:
    def __init__(self, labels: dict[tuple[float, float, str], str] | None = None) -> None:
        self.labels = labels or {}
        self.calls = []

    def lookup_label(self, latitude: float, longitude: float, *, granularity: str) -> str | None:
        rounded = (round(latitude, 4), round(longitude, 4), granularity)
        self.calls.append(rounded)
        return self.labels.get(rounded)

    def lookup_payload(self, latitude: float, longitude: float) -> dict | None:
        return None

    def queue_lookup(self, latitude: float, longitude: float) -> bool:
        return True


def test_home_assistant_summary_does_not_block_on_reverse_geocoding(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)
    service.member_views.reverse_geocoder = ExplodingReverseGeocoder()
    service.member_views.reverse_geocode_cache = FakeReverseGeocodeCache(
        labels={
            (37.4301, -122.0901, "block"): "100 block of Sundance Court, Sangaree",
        }
    )

    items = service.summary("family-alpha")

    assert len(items) == 1
    assert items[0]["status"] == "stopped"
    assert items[0]["current_location_label"] == "100 block of Sundance Court, Sangaree"
    assert items[0]["status_detail"] == "100 block of Sundance Court, Sangaree"


def test_home_assistant_member_panel_does_not_block_on_reverse_geocoding(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)
    service.member_views.reverse_geocoder = ExplodingReverseGeocoder()
    service.member_views.reverse_geocode_cache = FakeReverseGeocodeCache(
        labels={
            (37.4301, -122.0901, "block"): "100 block of Sundance Court, Sangaree",
        }
    )
    service.member_views.trip_derivation = SimpleNamespace(
        rebuild_member_day=lambda member_id, target_date: None
    )
    service.member_views.safety_derivation = SimpleNamespace(derive=lambda **_: [])

    panel = service.member_panel(
        "family-alpha",
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
    )

    assert panel is not None
    assert panel["member"]["current_location_label"] == "100 block of Sundance Court, Sangaree"
    assert panel["stops"][0]["label"] == "100 block of Sundance Court, Sangaree"
    assert panel["timeline"][0]["label"] == "100 block of Sundance Court, Sangaree"
    assert panel["timeline"][0]["kind"] == "location_stay"


def test_home_assistant_summary_hides_presence_timeline_mirror_members(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)

    items = service.summary("family-alpha")

    assert [item["display_name"] for item in items] == ["Sam"]


def test_home_assistant_summary_marks_member_stopped_when_persisted_stay_ends_at_latest_point(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    repository.stays = [
        SimpleNamespace(
            member_id=repository.member.id,
            started_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            ended_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4301,
            longitude=-122.0901,
            point_count=3,
            accuracy_m=18.0,
        )
    ]
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)
    service.member_views.reverse_geocode_cache = FakeReverseGeocodeCache(
        labels={
            (37.4301, -122.0901, "block"): "100 block of Sundance Court, Sangaree",
        }
    )

    items = service.summary("family-alpha")

    assert items[0]["status"] == "stopped"
    assert items[0]["status_detail"] == "100 block of Sundance Court, Sangaree"


def test_home_assistant_ingestion_status_returns_provider_diagnostics(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)

    status = service.ingestion_status()

    assert status == {
        "provider": "home_assistant",
        "state": "connected",
        "last_snapshot_at": datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        "last_connected_at": datetime(2026, 7, 8, 20, 1, tzinfo=UTC),
        "last_event_at": datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
        "last_error_at": None,
        "last_error_message": None,
        "retry_delay_seconds": None,
    }
