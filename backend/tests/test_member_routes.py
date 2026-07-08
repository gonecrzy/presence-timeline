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

    def set_device_ignored(self, member_id, device_id, ignored: bool):
        assert member_id == self.member_id
        assert device_id == self.device_id
        return {
            "id": str(device_id),
            "provider": "home_assistant",
            "external_id": "device_tracker.sam_phone",
            "label": "Sam Phone",
            "ignored": ignored,
            "last_seen_at": "2026-07-08T21:00:00Z",
        }


def test_member_routes_return_real_shapes() -> None:
    stub = StubMemberViews()
    app.dependency_overrides[get_member_view_service] = lambda: stub
    try:
        members = client.get("/api/v1/members")
        latest = client.get(f"/api/v1/members/{stub.member_id}/latest-location")
        history = client.get(
            f"/api/v1/members/{stub.member_id}/history",
            params={"start": "2026-07-08T20:00:00Z", "end": "2026-07-08T22:00:00Z"},
        )
        device = client.patch(
            f"/api/v1/members/{stub.member_id}/devices/{stub.device_id}",
            json={"ignored": True},
        )

        assert members.status_code == 200
        assert members.json()["items"][0]["display_name"] == "Sam"
        assert members.json()["items"][0]["devices"][0]["external_id"] == "device_tracker.sam_phone"
        assert latest.status_code == 200
        assert latest.json()["member_id"] == str(stub.member_id)
        assert history.status_code == 200
        assert len(history.json()["items"]) == 1
        assert device.status_code == 200
        assert device.json()["ignored"] is True
    finally:
        app.dependency_overrides.clear()
