from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.places import get_place_view_service
from app.main import app


client = TestClient(app)


class StubPlaceViews:
    def list_places(self, family_slug: str):
        assert family_slug == "dev-family"
        return [
            {
                "id": str(uuid4()),
                "name": "School",
                "latitude": 37.4210,
                "longitude": -122.0840,
                "radius_m": 200.0,
                "is_safe_zone": True,
                "place_type": "school",
            }
        ]


def test_places_route_returns_family_places() -> None:
    app.dependency_overrides[get_place_view_service] = lambda: StubPlaceViews()
    try:
        response = client.get("/api/v1/places")
        assert response.status_code == 200
        assert response.json()["items"][0]["name"] == "School"
    finally:
        app.dependency_overrides.clear()
