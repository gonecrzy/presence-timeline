from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.members import get_member_view_service
from app.main import app


client = TestClient(app)


class StubMemberViews:
    def __init__(self) -> None:
        self.member_id = uuid4()
        self.device_id = uuid4()

    def list_members(self, family_slug: str):
        assert family_slug == "dev-family"
        return [
            {
                "id": str(self.member_id),
                "display_name": "Sam",
                "is_child": True,
                "last_seen_at": "2026-07-08T21:00:00Z",
                "devices": [
                    {
                        "id": str(self.device_id),
                        "provider": "home_assistant",
                        "external_id": "device_tracker.sam_phone",
                        "label": "Sam Phone",
                        "ignored": False,
                        "last_seen_at": "2026-07-08T21:00:00Z",
                    }
                ],
            }
        ]

    def latest_location(self, member_id):
        assert member_id == self.member_id
        return {
            "member_id": str(member_id),
            "observed_at": "2026-07-08T21:00:00Z",
            "latitude": 37.42,
            "longitude": -122.08,
            "battery_level": 80,
        }

    def history(self, member_id, start, end):
        assert member_id == self.member_id
        assert start == datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
        assert end == datetime(2026, 7, 8, 22, 0, tzinfo=UTC)
        return [
            {
                "member_id": str(member_id),
                "observed_at": "2026-07-08T21:00:00Z",
                "latitude": 37.42,
                "longitude": -122.08,
                "battery_level": 80,
            }
        ]

    def timeline(self, member_id, start, end):
        assert member_id == self.member_id
        assert start == datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
        assert end == datetime(2026, 7, 8, 22, 0, tzinfo=UTC)
        return [
            {
                "kind": "location_point",
                "observed_at": "2026-07-08T21:00:00Z",
                "latitude": 37.42,
                "longitude": -122.08,
                "battery_level": 80,
                "source_entity_id": "device_tracker.sam_phone",
            },
            {
                "kind": "safety_event",
                "observed_at": "2026-07-08T21:05:00Z",
                "event_type": "safe_zone_entered",
                "severity": "info",
                "place_id": str(uuid4()),
                "payload": {"place_name": "School"},
            },
            {
                "kind": "trip",
                "observed_at": "2026-07-08T21:10:00Z",
                "trip_id": str(uuid4()),
                "started_at": "2026-07-08T21:10:00Z",
                "ended_at": "2026-07-08T21:30:00Z",
                "distance_m": 950.0,
                "point_count": 3,
                "start_label": None,
                "end_label": None,
            },
        ]

    def stops(self, member_id, start, end, dwell_radius_m, minimum_duration):
        assert member_id == self.member_id
        assert start == datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
        assert end == datetime(2026, 7, 8, 22, 0, tzinfo=UTC)
        assert dwell_radius_m == 250.0
        assert minimum_duration.total_seconds() == 600
        return [
            {
                "started_at": "2026-07-08T20:00:00Z",
                "ended_at": "2026-07-08T20:12:00Z",
                "duration_seconds": 720,
                "latitude": 37.4210,
                "longitude": -122.0840,
                "point_count": 3,
                "place_id": str(uuid4()),
                "place_name": "School",
                "address": None,
                "label": "School",
            }
        ]

    def set_device_ignored(self, member_id, device_id, ignored: bool):
        raise AssertionError("legacy device ignore entrypoint should not be used")

    def update_member(self, family_slug: str, member_id, display_name, is_child, avatar_color):
        assert family_slug == "dev-family"
        assert member_id == self.member_id
        assert display_name == "Samantha"
        assert is_child is False
        assert avatar_color == "#00AAFF"
        return {
            "id": str(member_id),
            "display_name": "Samantha",
            "is_child": False,
            "last_seen_at": "2026-07-08T21:00:00Z",
            "devices": [
                {
                    "id": str(self.device_id),
                    "provider": "home_assistant",
                    "external_id": "device_tracker.sam_phone",
                    "label": "Family Phone",
                    "ignored": False,
                    "last_seen_at": "2026-07-08T21:00:00Z",
                }
            ],
        }

    def update_device(self, family_slug: str, member_id, device_id, label, ignored):
        assert family_slug == "dev-family"
        assert member_id == self.member_id
        assert device_id == self.device_id
        assert label == "Family Phone"
        assert ignored is True
        return {
            "id": str(device_id),
            "provider": "home_assistant",
            "external_id": "device_tracker.sam_phone",
            "label": "Family Phone",
            "ignored": True,
            "last_seen_at": "2026-07-08T21:00:00Z",
        }


def test_member_routes_return_real_shapes() -> None:
    stub = StubMemberViews()
    app.dependency_overrides[get_member_view_service] = lambda: stub
    try:
        members = client.get("/api/v1/members")
        updated_member = client.patch(
            f"/api/v1/members/{stub.member_id}",
            json={
                "display_name": "Samantha",
                "is_child": False,
                "avatar_color": "#00AAFF",
            },
        )
        latest = client.get(f"/api/v1/members/{stub.member_id}/latest-location")
        history = client.get(
            f"/api/v1/members/{stub.member_id}/history",
            params={"start": "2026-07-08T20:00:00Z", "end": "2026-07-08T22:00:00Z"},
        )
        timeline = client.get(
            f"/api/v1/members/{stub.member_id}/timeline",
            params={"start": "2026-07-08T20:00:00Z", "end": "2026-07-08T22:00:00Z"},
        )
        stops = client.get(
            f"/api/v1/members/{stub.member_id}/stops",
            params={"start": "2026-07-08T20:00:00Z", "end": "2026-07-08T22:00:00Z"},
        )
        device = client.patch(
            f"/api/v1/members/{stub.member_id}/devices/{stub.device_id}",
            json={"label": "Family Phone", "ignored": True},
        )

        assert members.status_code == 200
        assert members.json()["items"][0]["display_name"] == "Sam"
        assert members.json()["items"][0]["devices"][0]["external_id"] == "device_tracker.sam_phone"
        assert updated_member.status_code == 200
        assert updated_member.json()["display_name"] == "Samantha"
        assert updated_member.json()["is_child"] is False
        assert latest.status_code == 200
        assert latest.json()["member_id"] == str(stub.member_id)
        assert history.status_code == 200
        assert len(history.json()["items"]) == 1
        assert timeline.status_code == 200
        assert [item["kind"] for item in timeline.json()["items"]] == [
            "location_point",
            "safety_event",
            "trip",
        ]
        assert stops.status_code == 200
        assert stops.json()["items"][0]["label"] == "School"
        assert stops.json()["items"][0]["duration_seconds"] == 720
        assert device.status_code == 200
        assert device.json()["ignored"] is True
        assert device.json()["label"] == "Family Phone"
    finally:
        app.dependency_overrides.clear()
