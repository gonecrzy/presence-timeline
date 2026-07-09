from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.places import get_place_view_service
from app.main import app


client = TestClient(app)


class StubPlaceViews:
    def __init__(self) -> None:
        self.place_id = uuid4()

    def list_places(self, family_slug: str):
        assert family_slug == "dev-family"
        return [
            {
                "id": str(self.place_id),
                "name": "School",
                "latitude": 37.4210,
                "longitude": -122.0840,
                "radius_m": 200.0,
                "is_safe_zone": True,
                "place_type": "school",
            }
        ]

    def create_place(self, family_slug: str, name, place_type, latitude, longitude, radius_m, is_safe_zone):
        assert family_slug == "dev-family"
        assert name == "Home"
        assert place_type == "home"
        assert latitude == 37.42
        assert longitude == -122.08
        assert radius_m == 150.0
        assert is_safe_zone is True
        return {
            "id": str(self.place_id),
            "name": "Home",
            "latitude": 37.42,
            "longitude": -122.08,
            "radius_m": 150.0,
            "is_safe_zone": True,
            "place_type": "home",
        }

    def update_place(self, family_slug: str, place_id, name, place_type, latitude, longitude, radius_m, is_safe_zone):
        assert family_slug == "dev-family"
        assert place_id == self.place_id
        assert name == "School West"
        assert place_type == "school"
        assert latitude == 37.422
        assert longitude == -122.085
        assert radius_m == 225.0
        assert is_safe_zone is False
        return {
            "id": str(place_id),
            "name": "School West",
            "latitude": 37.422,
            "longitude": -122.085,
            "radius_m": 225.0,
            "is_safe_zone": False,
            "place_type": "school",
        }

    def delete_place(self, family_slug: str, place_id) -> bool:
        assert family_slug == "dev-family"
        assert place_id == self.place_id
        return True

    def search_addresses(self, query: str):
        assert query == "129 Sundance Ct"
        return [
            {
                "label": "129 Sundance Ct, Sangaree",
                "latitude": 33.0311,
                "longitude": -80.1313,
            }
        ]


def test_places_route_returns_family_places() -> None:
    stub = StubPlaceViews()
    app.dependency_overrides[get_place_view_service] = lambda: stub
    try:
        response = client.get("/api/v1/places")
        created = client.post(
            "/api/v1/places",
            json={
                "name": "Home",
                "place_type": "home",
                "latitude": 37.42,
                "longitude": -122.08,
                "radius_m": 150.0,
                "is_safe_zone": True,
            },
        )
        updated = client.patch(
            f"/api/v1/places/{stub.place_id}",
            json={
                "name": "School West",
                "place_type": "school",
                "latitude": 37.422,
                "longitude": -122.085,
                "radius_m": 225.0,
                "is_safe_zone": False,
            },
        )
        deleted = client.delete(f"/api/v1/places/{stub.place_id}")
        searched = client.get("/api/v1/places/search", params={"q": "129 Sundance Ct"})

        assert response.status_code == 200
        assert response.json()["items"][0]["name"] == "School"
        assert created.status_code == 200
        assert created.json()["name"] == "Home"
        assert created.json()["is_safe_zone"] is True
        assert updated.status_code == 200
        assert updated.json()["name"] == "School West"
        assert updated.json()["is_safe_zone"] is False
        assert deleted.status_code == 204
        assert searched.status_code == 200
        assert searched.json()["items"][0]["label"] == "129 Sundance Ct, Sangaree"
    finally:
        app.dependency_overrides.clear()
