from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.members import get_trip_view_service
from app.main import app


client = TestClient(app)


class StubTripViews:
    def __init__(self) -> None:
        self.member_id = uuid4()
        self.trip_id = uuid4()

    def trips(self, member_id, trip_date: date):
        assert member_id == self.member_id
        assert trip_date == date(2026, 7, 8)
        return [
            {
                "id": str(self.trip_id),
                "started_at": "2026-07-08T08:00:00Z",
                "ended_at": "2026-07-08T08:20:00Z",
                "point_count": 3,
                "distance_m": 950.0,
                "start_label": None,
                "end_label": None,
            }
        ]

    def daily_summary(self, member_id, summary_date: date):
        assert member_id == self.member_id
        assert summary_date == date(2026, 7, 8)
        return {
            "summary_date": "2026-07-08",
            "first_seen_at": "2026-07-08T08:00:00Z",
            "last_seen_at": "2026-07-08T18:00:00Z",
            "trip_count": 1,
            "total_distance_m": 950.0,
        }

    def trip_route(self, member_id, trip_id):
        assert member_id == self.member_id
        assert trip_id == self.trip_id
        return {
            "id": str(trip_id),
            "member_id": str(member_id),
            "started_at": "2026-07-08T08:00:00Z",
            "ended_at": "2026-07-08T08:20:00Z",
            "distance_m": 950.0,
            "point_count": 3,
            "points": [
                {
                    "member_id": str(member_id),
                    "observed_at": "2026-07-08T08:00:00Z",
                    "latitude": 37.42,
                    "longitude": -122.08,
                    "battery_level": 80,
                },
                {
                    "member_id": str(member_id),
                    "observed_at": "2026-07-08T08:20:00Z",
                    "latitude": 37.43,
                    "longitude": -122.09,
                    "battery_level": 79,
                },
            ],
        }


def test_trip_routes_return_derived_shapes() -> None:
    stub = StubTripViews()
    app.dependency_overrides[get_trip_view_service] = lambda: stub
    try:
        trips = client.get(
            f"/api/v1/members/{stub.member_id}/trips",
            params={"date": "2026-07-08"},
        )
        summary = client.get(
            f"/api/v1/members/{stub.member_id}/daily-summary",
            params={"date": "2026-07-08"},
        )
        route = client.get(f"/api/v1/members/{stub.member_id}/trips/{stub.trip_id}/route")

        assert trips.status_code == 200
        assert trips.json()["items"][0]["distance_m"] == 950.0
        assert summary.status_code == 200
        assert summary.json()["trip_count"] == 1
        assert route.status_code == 200
        assert len(route.json()["points"]) == 2
    finally:
        app.dependency_overrides.clear()
