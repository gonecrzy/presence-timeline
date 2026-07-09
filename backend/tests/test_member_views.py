from types import SimpleNamespace
from datetime import UTC, datetime, timedelta
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
        self.family = SimpleNamespace(id=uuid4())

    def list_members_for_family_slug(self, family_slug: str):
        assert family_slug == "family-alpha"
        return [self.member]

    def get_latest_point_for_member(self, member_id):
        assert member_id == self.member.id
        return self.points[-1] if self.points else None

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
        return SimpleNamespace(id=self.member.id, family_id=self.family.id)

    def list_places_for_family_id(self, family_id):
        return self.places

    def list_member_history(self, member_id, start, end):
        assert member_id == self.member.id
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


class FakeReverseGeocoder:
    def __init__(self) -> None:
        self.calls = []

    def reverse(self, latitude: float, longitude: float, *, granularity: str = "full") -> str | None:
        self.calls.append((latitude, longitude))
        return "500 Elm St, Springfield"


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


def test_member_view_service_lists_members_with_place_aware_current_location_label(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.points = [
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0840,
            accuracy_m=10.0,
            battery_level=90,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4211,
            longitude=-122.0841,
            accuracy_m=11.0,
            battery_level=89,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0841,
            accuracy_m=12.0,
            battery_level=88,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)

    members = service.list_members("family-alpha")

    assert members[0]["current_location_label"] == "School"


def test_member_view_service_lists_members_with_block_label_when_place_missing(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.places = []
    repository.points = [
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.4300,
            longitude=-122.0900,
            accuracy_m=18.0,
            battery_level=82,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4301,
            longitude=-122.0901,
            accuracy_m=19.0,
            battery_level=81,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 16, tzinfo=UTC),
            latitude=37.4301,
            longitude=-122.0901,
            accuracy_m=18.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    service.reverse_geocoder = SimpleNamespace(
        reverse=lambda latitude, longitude, granularity="full": {
            "full": "129 Sundance Court, Sangaree, South Carolina 29486",
            "block": "100 block of Sundance Court, Sangaree",
            "street": "Sundance Court, Sangaree",
            "locality": "Sangaree",
        }[granularity],
    )

    members = service.list_members("family-alpha")

    assert members[0]["current_location_label"] == "100 block of Sundance Court, Sangaree"


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
        "safety_event",
        "trip",
    ]
    assert items[0]["event_type"] == "safe_zone_entered"
    assert items[1]["distance_m"] == 950.0


def test_member_view_service_deduplicates_trip_entries(monkeypatch) -> None:
    repository = FakeMemberRepository()
    duplicate_trip = repository.trips[0]
    repository.trips = [duplicate_trip, duplicate_trip, duplicate_trip]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    service.trip_derivation = FakeTripDerivation()
    service.safety_derivation = SimpleNamespace(derive=lambda **_: [])

    items = service.timeline(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
    )

    trip_items = [item for item in items if item["kind"] == "trip"]
    assert len(trip_items) == 1
    assert trip_items[0]["trip_id"] == duplicate_trip.id


def test_member_view_service_condenses_nearby_points_into_location_stay(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.trips = []
    repository.points = [
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0840,
            accuracy_m=10.0,
            battery_level=90,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4211,
            longitude=-122.0841,
            accuracy_m=11.0,
            battery_level=89,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0841,
            accuracy_m=12.0,
            battery_level=88,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    service.trip_derivation = FakeTripDerivation()
    service.safety_derivation = SimpleNamespace(derive=lambda **_: [])

    items = service.timeline(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
    )

    assert [item["kind"] for item in items] == ["location_stay"]
    assert items[0]["label"] == "School"
    assert items[0]["started_at"] == datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
    assert items[0]["ended_at"] == datetime(2026, 7, 8, 20, 12, tzinfo=UTC)
    assert items[0]["duration_seconds"] == 12 * 60
    assert items[0]["is_current"] is True
    assert items[0]["point_count"] == 3


def test_member_view_service_derives_stops_with_place_first_then_reverse_geocode(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.points = [
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0840,
            accuracy_m=10.0,
            battery_level=90,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4211,
            longitude=-122.0841,
            accuracy_m=10.0,
            battery_level=89,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0841,
            accuracy_m=10.0,
            battery_level=88,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 30, tzinfo=UTC),
            latitude=37.4305,
            longitude=-122.0900,
            accuracy_m=10.0,
            battery_level=82,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 36, tzinfo=UTC),
            latitude=37.4306,
            longitude=-122.0901,
            accuracy_m=10.0,
            battery_level=81,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 42, tzinfo=UTC),
            latitude=37.4305,
            longitude=-122.0900,
            accuracy_m=10.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    reverse_geocoder = FakeReverseGeocoder()
    service.reverse_geocoder = reverse_geocoder

    stops = service.stops(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
        dwell_radius_m=250.0,
        minimum_duration=timedelta(minutes=10),
    )

    assert len(stops) == 2
    assert stops[0]["place_name"] == "School"
    assert stops[0]["label"] == "School"
    assert stops[0]["address"] is None
    assert stops[0]["duration_seconds"] == 12 * 60
    assert stops[1]["place_name"] is None
    assert stops[1]["address"] == "500 Elm St, Springfield"
    assert stops[1]["label"] == "500 Elm St, Springfield"
    assert stops[1]["duration_seconds"] == 12 * 60
    assert reverse_geocoder.calls == [(stops[1]["latitude"], stops[1]["longitude"])]


def test_member_view_service_uses_representative_stop_point_for_reverse_geocode(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.places = []
    repository.points = [
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.4300,
            longitude=-122.0900,
            accuracy_m=18.0,
            battery_level=82,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4310,
            longitude=-122.0910,
            accuracy_m=90.0,
            battery_level=81,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4301,
            longitude=-122.0901,
            accuracy_m=10.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    reverse_geocoder = FakeReverseGeocoder()
    service.reverse_geocoder = reverse_geocoder

    stops = service.stops(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
        dwell_radius_m=250.0,
        minimum_duration=timedelta(minutes=10),
    )

    assert len(stops) == 1
    assert reverse_geocoder.calls == [(37.4301, -122.0901)]
    assert stops[0]["latitude"] == 37.4301
    assert stops[0]["longitude"] == -122.0901
