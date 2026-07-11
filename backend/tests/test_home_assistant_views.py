from datetime import UTC, datetime, timedelta
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

    def list_members_for_family_slug(self, family_slug: str):
        assert family_slug == "family-alpha"
        return [self.member]

    def get_latest_point_for_member(self, member_id):
        assert member_id == self.member.id
        return self.points[-1]

    def get_member(self, member_id):
        assert member_id == self.member.id
        return self.member

    def list_places_for_family_id(self, family_id):
        assert family_id == self.member.family_id
        return []

    def list_member_history(self, member_id, start, end):
        assert member_id == self.member.id
        return self.points

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


class ExplodingReverseGeocoder:
    def reverse(self, latitude: float, longitude: float, *, granularity: str = "full") -> str | None:
        raise AssertionError("reverse geocoder should not be called")


def test_home_assistant_summary_does_not_block_on_reverse_geocoding(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)
    service.member_views.reverse_geocoder = ExplodingReverseGeocoder()

    items = service.summary("family-alpha")

    assert len(items) == 1
    assert items[0]["status"] == "stopped"
    assert items[0]["current_location_label"] == "37.4301, -122.0901"
    assert items[0]["status_detail"] == "37.4301, -122.0901"


def test_home_assistant_member_panel_does_not_block_on_reverse_geocoding(monkeypatch) -> None:
    repository = FakeHomeAssistantRepository()
    monkeypatch.setattr(
        "app.services.member_views.LocationRepository",
        lambda db: repository,
    )

    service = HomeAssistantViewService(db=None)
    service.member_views.reverse_geocoder = ExplodingReverseGeocoder()
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
    assert panel["member"]["current_location_label"] == "37.4301, -122.0901"
    assert panel["stops"][0]["label"] == "37.4301, -122.0901"
    assert panel["timeline"][0]["label"] == "37.4301, -122.0901"
    assert panel["timeline"][0]["kind"] == "location_stay"
