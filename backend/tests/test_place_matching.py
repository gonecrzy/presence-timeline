from uuid import uuid4

from app.services.places import PlaceMatcher


def test_place_matcher_returns_matching_place_inside_radius() -> None:
    family_id = uuid4()
    place = {
        "id": uuid4(),
        "family_id": family_id,
        "name": "School",
        "latitude": 37.4210,
        "longitude": -122.0840,
        "radius_m": 200.0,
        "is_safe_zone": True,
    }

    matched = PlaceMatcher().match(
        places=[place],
        latitude=37.4215,
        longitude=-122.0838,
    )

    assert matched is not None
    assert matched["name"] == "School"


def test_place_matcher_returns_none_when_outside_all_places() -> None:
    family_id = uuid4()
    place = {
        "id": uuid4(),
        "family_id": family_id,
        "name": "School",
        "latitude": 37.4210,
        "longitude": -122.0840,
        "radius_m": 100.0,
        "is_safe_zone": True,
    }

    matched = PlaceMatcher().match(
        places=[place],
        latitude=37.4300,
        longitude=-122.0900,
    )

    assert matched is None
