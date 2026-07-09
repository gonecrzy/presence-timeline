from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.services.trip_views import TripViewService


class FakeTripRepository:
    def __init__(self) -> None:
        self.member_id = uuid4()
        self.trip = SimpleNamespace(
            id=uuid4(),
            member_id=self.member_id,
            started_at=datetime(2026, 7, 8, 8, 0, tzinfo=UTC),
            ended_at=datetime(2026, 7, 8, 8, 20, tzinfo=UTC),
            point_count=3,
            distance_m=950.0,
        )
        self.points = [
            SimpleNamespace(
                member_id=self.member_id,
                observed_at=datetime(2026, 7, 8, 8, 0, tzinfo=UTC),
                latitude=37.42,
                longitude=-122.08,
                accuracy_m=12.0,
                battery_level=80,
                source_entity_id="device_tracker.sam_phone",
            ),
            SimpleNamespace(
                member_id=self.member_id,
                observed_at=datetime(2026, 7, 8, 8, 20, tzinfo=UTC),
                latitude=37.43,
                longitude=-122.09,
                accuracy_m=10.0,
                battery_level=79,
                source_entity_id="device_tracker.sam_phone",
            ),
        ]

    def get_trip_for_member(self, member_id, trip_id):
        assert member_id == self.member_id
        assert trip_id == self.trip.id
        return self.trip

    def list_member_history(self, member_id, start, end):
        assert member_id == self.member_id
        assert start == self.trip.started_at
        assert end == self.trip.ended_at
        return self.points


def test_trip_view_service_returns_route_playback(monkeypatch) -> None:
    repository = FakeTripRepository()
    monkeypatch.setattr("app.services.trip_views.LocationRepository", lambda db: repository)

    service = TripViewService(db=None)
    route = service.trip_route(repository.member_id, repository.trip.id)

    assert route is not None
    assert route["distance_m"] == 950.0
    assert len(route["points"]) == 2
    assert route["points"][0]["source_entity_id"] == "device_tracker.sam_phone"


def test_trip_view_service_simplifies_stationary_jitter_but_keeps_travel_shape(monkeypatch) -> None:
    repository = FakeTripRepository()
    repository.trip.ended_at = datetime(2026, 7, 8, 8, 22, tzinfo=UTC)
    repository.trip.point_count = 6
    repository.points = [
        SimpleNamespace(
            member_id=repository.member_id,
            observed_at=datetime(2026, 7, 8, 8, 0, tzinfo=UTC),
            latitude=37.4200,
            longitude=-122.0800,
            accuracy_m=12.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member_id,
            observed_at=datetime(2026, 7, 8, 8, 2, tzinfo=UTC),
            latitude=37.4201,
            longitude=-122.0801,
            accuracy_m=11.0,
            battery_level=80,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member_id,
            observed_at=datetime(2026, 7, 8, 8, 10, tzinfo=UTC),
            latitude=37.4240,
            longitude=-122.0840,
            accuracy_m=10.0,
            battery_level=79,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member_id,
            observed_at=datetime(2026, 7, 8, 8, 15, tzinfo=UTC),
            latitude=37.4270,
            longitude=-122.0870,
            accuracy_m=10.0,
            battery_level=78,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member_id,
            observed_at=datetime(2026, 7, 8, 8, 20, tzinfo=UTC),
            latitude=37.4300,
            longitude=-122.0900,
            accuracy_m=10.0,
            battery_level=77,
            source_entity_id="device_tracker.sam_phone",
        ),
        SimpleNamespace(
            member_id=repository.member_id,
            observed_at=datetime(2026, 7, 8, 8, 22, tzinfo=UTC),
            latitude=37.4301,
            longitude=-122.0901,
            accuracy_m=10.0,
            battery_level=77,
            source_entity_id="device_tracker.sam_phone",
        ),
    ]
    monkeypatch.setattr("app.services.trip_views.LocationRepository", lambda db: repository)

    service = TripViewService(db=None)
    route = service.trip_route(repository.member_id, repository.trip.id)

    assert route is not None
    assert [point["observed_at"] for point in route["points"]] == [
        datetime(2026, 7, 8, 8, 2, tzinfo=UTC),
        datetime(2026, 7, 8, 8, 10, tzinfo=UTC),
        datetime(2026, 7, 8, 8, 15, tzinfo=UTC),
        datetime(2026, 7, 8, 8, 22, tzinfo=UTC),
    ]
