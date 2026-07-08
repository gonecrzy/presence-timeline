from types import SimpleNamespace
from datetime import UTC, datetime
from uuid import uuid4

from app.services.member_views import MemberViewService


class FakeMemberRepository:
    def __init__(self) -> None:
        self.committed = False
        self.member = SimpleNamespace(
            id=uuid4(),
            display_name="Sam",
            is_child=True,
            last_seen_at="2026-07-08T21:00:00Z",
            devices=[
                SimpleNamespace(
                    id=uuid4(),
                    provider="home_assistant",
                    external_id="device_tracker.sam_phone",
                    label="Sam Phone",
                    ignored=False,
                    last_seen_at="2026-07-08T21:00:00Z",
                )
            ],
        )
        self.device = self.member.devices[0]
        self.places = [
            SimpleNamespace(
                id=uuid4(),
                name="School",
                latitude=37.4210,
                longitude=-122.0840,
                radius_m=200.0,
                is_safe_zone=True,
            )
        ]
        self.points = [
            SimpleNamespace(
                member_id=self.member.id,
                observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
                latitude=37.42,
                longitude=-122.08,
                accuracy_m=10.0,
                battery_level=80,
                source_entity_id="device_tracker.sam_phone",
            )
        ]
        self.events = []
        self.trips = [
            SimpleNamespace(
                id=uuid4(),
                started_at=datetime(2026, 7, 8, 21, 10, tzinfo=UTC),
                ended_at=datetime(2026, 7, 8, 21, 30, tzinfo=UTC),
                point_count=3,
                distance_m=950.0,
                start_label=None,
                end_label=None,
            )
        ]

    def update_member_for_family_slug(
        self,
        family_slug: str,
        member_id,
        *,
        display_name,
        is_child,
        avatar_color,
    ):
        assert family_slug == "family-alpha"
        assert member_id == self.member.id
        assert display_name == "Samantha"
        assert is_child is False
        assert avatar_color == "#00AAFF"
        self.member.display_name = display_name
        self.member.is_child = is_child
        return self.member

    def update_device_for_family_slug(
        self,
        family_slug: str,
        member_id,
        device_id,
        *,
        label,
        ignored,
    ):
        assert family_slug == "family-alpha"
        assert member_id == self.member.id
        assert device_id == self.device.id
        assert label == "Family Phone"
        assert ignored is True
        self.device.label = label
        self.device.ignored = ignored
        return self.device

    def commit(self) -> None:
        self.committed = True

    def get_member(self, member_id):
        assert member_id == self.member.id
        return SimpleNamespace(id=self.member.id, family_id=uuid4())

    def list_places_for_family_id(self, family_id):
        return self.places

    def list_member_history(self, member_id, start, end):
        assert member_id == self.member.id
        assert start == datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
        assert end == datetime(2026, 7, 8, 22, 0, tzinfo=UTC)
        return self.points

    def replace_safety_events_for_range(self, member_id, start, end, events):
        self.events = [
            SimpleNamespace(
                id=uuid4(),
                event_type=event["event_type"],
                severity=event["severity"],
                observed_at=event["observed_at"],
                place_id=event["place_id"],
                payload=event["payload"],
            )
            for event in events
        ]

    def list_safety_events_for_range(self, member_id, start, end):
        return self.events

    def list_trips_for_member_range(self, member_id, start, end):
        assert member_id == self.member.id
        return self.trips


class FakeTripDerivation:
    def __init__(self) -> None:
        self.calls = []

    def rebuild_member_day(self, member_id, target_date) -> None:
        self.calls.append((member_id, target_date))


class FakeSafetyDerivation:
    def derive(self, *, points, places):
        assert len(points) == 1
        assert len(places) == 1
        return [
            {
                "event_type": "safe_zone_entered",
                "severity": "info",
                "observed_at": datetime(2026, 7, 8, 21, 5, tzinfo=UTC),
                "place_id": places[0]["id"],
                "payload": {"place_name": places[0]["name"]},
            }
        ]


def test_member_view_service_updates_member_profile(monkeypatch) -> None:
    repository = FakeMemberRepository()
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    updated = service.update_member(
        "family-alpha",
        repository.member.id,
        display_name="Samantha",
        is_child=False,
        avatar_color="#00AAFF",
    )

    assert updated is not None
    assert updated["display_name"] == "Samantha"
    assert updated["is_child"] is False
    assert updated["devices"][0]["label"] == "Sam Phone"
    assert repository.committed is True


def test_member_view_service_updates_device_metadata(monkeypatch) -> None:
    repository = FakeMemberRepository()
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    updated = service.update_device(
        "family-alpha",
        repository.member.id,
        repository.device.id,
        label="Family Phone",
        ignored=True,
    )

    assert updated is not None
    assert updated["label"] == "Family Phone"
    assert updated["ignored"] is True
    assert repository.committed is True


def test_member_view_service_builds_unified_timeline(monkeypatch) -> None:
    repository = FakeMemberRepository()
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    service.trip_derivation = FakeTripDerivation()
    service.safety_derivation = FakeSafetyDerivation()

    items = service.timeline(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
    )

    assert [item["kind"] for item in items] == [
        "location_point",
        "safety_event",
        "trip",
    ]
    assert items[0]["source_entity_id"] == "device_tracker.sam_phone"
    assert items[1]["event_type"] == "safe_zone_entered"
    assert items[2]["distance_m"] == 950.0
