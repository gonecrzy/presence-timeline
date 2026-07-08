from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_returns_service_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["name"] == "GpsTrack API"


def test_health_route_reports_retention_window() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "GpsTrack API",
        "retention_days": 7,
    }


def test_members_route_starts_with_empty_collection() -> None:
    response = client.get("/api/v1/members")

    assert response.status_code == 200
    assert response.json() == {"items": []}
