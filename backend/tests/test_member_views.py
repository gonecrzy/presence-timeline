from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

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
        self.stays = []

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

    def list_stays_for_member_range(self, member_id, start, end):
        assert member_id == self.member.id
        return self.stays


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


class FakeReverseGeocodeCache:
    def __init__(
        self,
        labels: dict[tuple[float, float, str], str] | None = None,
        payloads: dict[tuple[float, float], dict] | None = None,
    ) -> None:
        self.labels = labels or {}
        self.payloads = payloads or {}
        self.calls = []
        self.queued = []

    def lookup_label(self, latitude: float, longitude: float, *, granularity: str) -> str | None:
        rounded = (round(latitude, 4), round(longitude, 4), granularity)
        self.calls.append(rounded)
        return self.labels.get(rounded)

    def lookup_payload(self, latitude: float, longitude: float) -> dict | None:
        return self.payloads.get((round(latitude, 4), round(longitude, 4)))

    def queue_lookup(self, latitude: float, longitude: float) -> bool:
        self.queued.append((round(latitude, 4), round(longitude, 4)))
        return True


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


def test_member_view_service_uses_persisted_stay_for_current_location_label(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.points = [
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
    repository.stays = [
        SimpleNamespace(
            member_id=repository.member.id,
            started_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            ended_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0841,
            point_count=3,
            accuracy_m=10.0,
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)

    members = service.list_members("family-alpha")

    assert members[0]["current_location_label"] == "School"


def test_member_view_service_lists_members_with_cached_block_label_when_place_missing(monkeypatch) -> None:
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
    reverse_geocode_cache = FakeReverseGeocodeCache(
        labels={
            (37.4301, -122.0901, "block"): "100 block of Sundance Court, Sangaree",
        }
    )
    service.reverse_geocode_cache = reverse_geocode_cache

    members = service.list_members("family-alpha")

    assert members[0]["current_location_label"] == "100 block of Sundance Court, Sangaree"
    assert reverse_geocode_cache.calls == [(37.4301, -122.0901, "block")]


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


def test_member_view_service_timeline_uses_persisted_stays(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.points = [
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
    repository.stays = [
        SimpleNamespace(
            member_id=repository.member.id,
            started_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            ended_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4210,
            longitude=-122.0841,
            point_count=3,
            accuracy_m=10.0,
        ),
    ]
    repository.trips = []
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
    assert items[0]["point_count"] == 3


def test_member_view_service_derives_stops_with_place_first_then_cached_label(monkeypatch) -> None:
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
    reverse_geocode_cache = FakeReverseGeocodeCache(
        labels={
            (37.4305, -122.09, "full"): "500 Elm St, Springfield",
        }
    )
    service.reverse_geocode_cache = reverse_geocode_cache

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
    assert reverse_geocode_cache.calls == [
        (round(stops[1]["latitude"], 4), round(stops[1]["longitude"], 4), "full")
    ]


def test_member_view_service_uses_averaged_stop_point_for_cached_label(monkeypatch) -> None:
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
            latitude=37.4303,
            longitude=-122.0903,
            accuracy_m=12.0,
            battery_level=81,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4306,
            longitude=-122.0906,
            accuracy_m=10.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    reverse_geocode_cache = FakeReverseGeocodeCache(
        labels={
            (37.4303, -122.0903, "full"): "500 Elm St, Springfield",
        }
    )
    service.reverse_geocode_cache = reverse_geocode_cache

    stops = service.stops(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
        dwell_radius_m=250.0,
        minimum_duration=timedelta(minutes=10),
    )

    assert len(stops) == 1
    assert reverse_geocode_cache.calls == [(37.4303, -122.0903, "full")]
    assert stops[0]["latitude"] == pytest.approx(37.4303)
    assert stops[0]["longitude"] == pytest.approx(-122.0903)


def test_member_view_service_prefers_business_name_and_keeps_exact_address(monkeypatch) -> None:
    repository = FakeMemberRepository()
    repository.places = []
    repository.points = [
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.4300,
            longitude=-122.0900,
            accuracy_m=8.0,
            battery_level=82,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4303,
            longitude=-122.0903,
            accuracy_m=7.0,
            battery_level=81,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member.id,
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4306,
            longitude=-122.0906,
            accuracy_m=6.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.member_views.LocationRepository", lambda db: repository)

    service = MemberViewService(db=None)
    reverse_geocode_cache = FakeReverseGeocodeCache(
        payloads={
            (37.4303, -122.0903): {
                "name": "Target",
                "display_name": "Target, 129, Sundance Court, Sangaree, Berkeley County, South Carolina, 29486, United States",
                "address": {
                    "shop": "Target",
                    "house_number": "129",
                    "road": "Sundance Court",
                    "suburb": "Sangaree",
                    "state": "South Carolina",
                    "postcode": "29486",
                },
            }
        }
    )
    service.reverse_geocode_cache = reverse_geocode_cache

    stops = service.stops(
        repository.member.id,
        datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 8, 22, 0, tzinfo=UTC),
        dwell_radius_m=250.0,
        minimum_duration=timedelta(minutes=10),
    )

    assert len(stops) == 1
    assert stops[0]["place_name"] == "Target"
    assert stops[0]["address"] == "129 Sundance Court, Sangaree, South Carolina 29486"
    assert stops[0]["label"] == "Target"
