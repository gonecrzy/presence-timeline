from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.home_assistant import get_home_assistant_view_service
from app.main import app


client = TestClient(app)


class StubHomeAssistantViews:
    def __init__(self) -> None:
        self.member_id = uuid4()

    def summary(self, family_slug: str):
        assert family_slug == "dev-family"
        return [
            {
                "member_id": str(self.member_id),
                "display_name": "Sam",
                "is_child": True,
                "last_seen_at": "2026-07-11T09:00:00Z",
                "current_location_label": "School",
                "status": "stopped",
                "status_detail": "School",
                "latitude": 37.42,
                "longitude": -122.08,
                "accuracy_m": 12.5,
                "battery_level": 82,
                "observed_at": "2026-07-11T09:00:00Z",
                "source_entity_id": "device_tracker.sam_phone",
            }
        ]

    def member_panel(self, family_slug: str, member_id, start, end):
        assert family_slug == "dev-family"
        assert member_id == self.member_id
        assert start == datetime(2026, 7, 10, 9, 0, tzinfo=UTC)
        assert end == datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
        return {
            "member": {
                "member_id": str(self.member_id),
                "display_name": "Sam",
                "is_child": True,
                "last_seen_at": "2026-07-11T09:00:00Z",
                "current_location_label": "School",
                "status": "stopped",
                "status_detail": "School",
                "latitude": 37.42,
                "longitude": -122.08,
                "accuracy_m": 12.5,
                "battery_level": 82,
                "observed_at": "2026-07-11T09:00:00Z",
                "source_entity_id": "device_tracker.sam_phone",
            },
            "history": [
                {
                    "member_id": str(self.member_id),
                    "observed_at": "2026-07-11T08:55:00Z",
                    "latitude": 37.419,
                    "longitude": -122.081,
                    "accuracy_m": 14.0,
                    "battery_level": 82,
                    "source_entity_id": "device_tracker.sam_phone",
                }
            ],
            "timeline": [
                {
                    "kind": "location_stay",
                    "observed_at": "2026-07-11T08:40:00Z",
                    "started_at": "2026-07-11T08:40:00Z",
                    "ended_at": "2026-07-11T09:00:00Z",
                    "duration_seconds": 1200,
                    "latitude": 37.42,
                    "longitude": -122.08,
                    "label": "School",
                    "is_current": True,
                }
            ],
            "stops": [
                {
                    "started_at": "2026-07-11T08:40:00Z",
                    "ended_at": "2026-07-11T09:00:00Z",
                    "duration_seconds": 1200,
                    "latitude": 37.42,
                    "longitude": -122.08,
                    "point_count": 4,
                    "place_name": "School",
                    "label": "School",
                    "is_current": True,
                }
            ],
        }


def test_home_assistant_summary_returns_current_member_snapshot() -> None:
    stub = StubHomeAssistantViews()
    app.dependency_overrides[get_home_assistant_view_service] = lambda: stub
    try:
        response = client.get("/api/v1/home-assistant/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "member_id": str(stub.member_id),
                "display_name": "Sam",
                "is_child": True,
                "last_seen_at": "2026-07-11T09:00:00Z",
                "current_location_label": "School",
                "status": "stopped",
                "status_detail": "School",
                "latitude": 37.42,
                "longitude": -122.08,
                "accuracy_m": 12.5,
                "battery_level": 82,
                "observed_at": "2026-07-11T09:00:00Z",
                "source_entity_id": "device_tracker.sam_phone",
            }
        ]
    }


def test_home_assistant_member_panel_returns_history_timeline_and_stops() -> None:
    stub = StubHomeAssistantViews()
    app.dependency_overrides[get_home_assistant_view_service] = lambda: stub
    try:
        response = client.get(
            f"/api/v1/home-assistant/members/{stub.member_id}/panel",
            params={
                "start": "2026-07-10T09:00:00Z",
                "end": "2026-07-11T09:00:00Z",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "member": {
            "member_id": str(stub.member_id),
            "display_name": "Sam",
            "is_child": True,
            "last_seen_at": "2026-07-11T09:00:00Z",
            "current_location_label": "School",
            "status": "stopped",
            "status_detail": "School",
            "latitude": 37.42,
            "longitude": -122.08,
            "accuracy_m": 12.5,
            "battery_level": 82,
            "observed_at": "2026-07-11T09:00:00Z",
            "source_entity_id": "device_tracker.sam_phone",
        },
        "history": [
            {
                "member_id": str(stub.member_id),
                "observed_at": "2026-07-11T08:55:00Z",
                "latitude": 37.419,
                "longitude": -122.081,
                "accuracy_m": 14.0,
                "battery_level": 82,
                "source_entity_id": "device_tracker.sam_phone",
            }
        ],
        "timeline": [
            {
                "kind": "location_stay",
                "observed_at": "2026-07-11T08:40:00Z",
                "trip_id": None,
                "started_at": "2026-07-11T08:40:00Z",
                "ended_at": "2026-07-11T09:00:00Z",
                "duration_seconds": 1200,
                "latitude": 37.42,
                "longitude": -122.08,
                "label": "School",
                "is_current": True,
                "battery_level": None,
                "source_entity_id": None,
                "distance_m": None,
                "point_count": None,
                "start_label": None,
                "end_label": None,
                "event_type": None,
                "severity": None,
                "place_id": None,
                "payload": None,
            }
        ],
        "stops": [
            {
                "started_at": "2026-07-11T08:40:00Z",
                "ended_at": "2026-07-11T09:00:00Z",
                "duration_seconds": 1200,
                "latitude": 37.42,
                "longitude": -122.08,
                "point_count": 4,
                "place_id": None,
                "place_name": "School",
                "address": None,
                "label": "School",
                "is_current": True,
            }
        ],
    }
