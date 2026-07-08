from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.members import get_safety_view_service
from app.main import app


client = TestClient(app)


class StubSafetyViews:
    def __init__(self) -> None:
        self.member_id = uuid4()

    def events(self, member_id, start, end):
        assert member_id == self.member_id
        assert start == datetime(2026, 7, 8, 8, 0, tzinfo=UTC)
        assert end == datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
        return [
            {
                "id": str(uuid4()),
                "event_type": "safe_zone_entered",
                "severity": "info",
                "observed_at": "2026-07-08T08:10:00Z",
                "place_id": str(uuid4()),
                "payload": {"place_name": "School"},
            }
        ]


def test_safety_events_route_returns_member_events() -> None:
    stub = StubSafetyViews()
    app.dependency_overrides[get_safety_view_service] = lambda: stub
    try:
        response = client.get(
            f"/api/v1/members/{stub.member_id}/safety-events",
            params={"start": "2026-07-08T08:00:00Z", "end": "2026-07-08T20:00:00Z"},
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["event_type"] == "safe_zone_entered"
    finally:
        app.dependency_overrides.clear()
