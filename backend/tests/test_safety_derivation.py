from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.services.safety import SafetyDerivationService


def _point(member_id, observed_at, latitude, longitude):
    return {
        "member_id": member_id,
        "observed_at": observed_at,
        "latitude": latitude,
        "longitude": longitude,
    }


def test_safety_derivation_emits_enter_and_exit_events_for_safe_zone() -> None:
    member_id = uuid4()
    place_id = uuid4()
    start = datetime(2026, 7, 8, 8, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4300, -122.0900),
        _point(member_id, start + timedelta(minutes=10), 37.4211, -122.0841),
        _point(member_id, start + timedelta(minutes=20), 37.4301, -122.0901),
    ]
    places = [
        {
            "id": place_id,
            "name": "School",
            "latitude": 37.4210,
            "longitude": -122.0840,
            "radius_m": 200.0,
            "is_safe_zone": True,
        }
    ]

    events = SafetyDerivationService().derive(points=points, places=places)

    assert [event["event_type"] for event in events] == ["safe_zone_entered", "safe_zone_exited"]
    assert events[0]["place_id"] == place_id
    assert events[0]["payload"]["place_name"] == "School"


def test_safety_derivation_ignores_non_safe_places() -> None:
    member_id = uuid4()
    start = datetime(2026, 7, 8, 8, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4211, -122.0841),
        _point(member_id, start + timedelta(minutes=10), 37.4212, -122.0842),
    ]
    places = [
        {
            "id": uuid4(),
            "name": "Mall",
            "latitude": 37.4210,
            "longitude": -122.0840,
            "radius_m": 200.0,
            "is_safe_zone": False,
        }
    ]

    events = SafetyDerivationService().derive(points=points, places=places)

    assert events == []
