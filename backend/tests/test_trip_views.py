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
