from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.home_assistant import get_home_assistant_view_service
from app.main import app


client = TestClient(app)


class StubHomeAssistantViews:
    def summary(self, family_slug: str):
        assert family_slug == "dev-family"
        return [
            {
                "member_id": str(uuid4()),
                "display_name": "Sam",
                "is_child": True,
                "last_seen_at": "2026-07-11T09:00:00Z",
                "current_location_label": "School",
                "latitude": 37.42,
                "longitude": -122.08,
                "accuracy_m": 12.5,
                "battery_level": 82,
                "observed_at": "2026-07-11T09:00:00Z",
                "source_entity_id": "device_tracker.sam_phone",
            }
        ]


def test_home_assistant_summary_returns_current_member_snapshot() -> None:
    app.dependency_overrides[get_home_assistant_view_service] = lambda: StubHomeAssistantViews()
    try:
        response = client.get("/api/v1/home-assistant/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "member_id": response.json()["items"][0]["member_id"],
                "display_name": "Sam",
                "is_child": True,
                "last_seen_at": "2026-07-11T09:00:00Z",
                "current_location_label": "School",
                "latitude": 37.42,
                "longitude": -122.08,
                "accuracy_m": 12.5,
                "battery_level": 82,
                "observed_at": "2026-07-11T09:00:00Z",
                "source_entity_id": "device_tracker.sam_phone",
            }
        ]
    }
