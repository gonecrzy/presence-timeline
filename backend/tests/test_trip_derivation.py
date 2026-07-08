from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from app.services.trip_derivation import TripDerivationService


def _point(member_id, observed_at, latitude, longitude):
    return {
        "member_id": member_id,
        "observed_at": observed_at,
        "latitude": latitude,
        "longitude": longitude,
        "source_entity_id": "device_tracker.sam_phone",
    }


def test_derivation_builds_trip_for_meaningful_movement_session() -> None:
    member_id = uuid4()
    service = TripDerivationService(
        max_trip_gap_minutes=30,
        min_trip_distance_m=250,
    )
    start = datetime(2026, 7, 8, 8, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4200, -122.0800),
        _point(member_id, start + timedelta(minutes=10), 37.4230, -122.0840),
        _point(member_id, start + timedelta(minutes=20), 37.4270, -122.0900),
    ]

    trips, summary = service.derive_day(points, date(2026, 7, 8))

    assert len(trips) == 1
    assert trips[0]["point_count"] == 3
    assert trips[0]["started_at"] == start
    assert trips[0]["ended_at"] == start + timedelta(minutes=20)
    assert trips[0]["distance_m"] > 250
    assert summary["trip_count"] == 1
    assert summary["total_distance_m"] == trips[0]["distance_m"]


def test_derivation_ignores_short_stationary_jitter_sessions() -> None:
    member_id = uuid4()
    service = TripDerivationService(
        max_trip_gap_minutes=30,
        min_trip_distance_m=250,
    )
    start = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4200, -122.0800),
        _point(member_id, start + timedelta(minutes=3), 37.4201, -122.0801),
        _point(member_id, start + timedelta(minutes=6), 37.4200, -122.0800),
    ]

    trips, summary = service.derive_day(points, date(2026, 7, 8))

    assert trips == []
    assert summary["trip_count"] == 0
    assert summary["total_distance_m"] == 0
    assert summary["first_seen_at"] == start
    assert summary["last_seen_at"] == start + timedelta(minutes=6)


def test_derivation_splits_sessions_on_large_time_gap() -> None:
    member_id = uuid4()
    service = TripDerivationService(
        max_trip_gap_minutes=30,
        min_trip_distance_m=250,
    )
    start = datetime(2026, 7, 8, 8, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4200, -122.0800),
        _point(member_id, start + timedelta(minutes=10), 37.4230, -122.0840),
        _point(member_id, start + timedelta(hours=2), 37.4300, -122.0950),
        _point(member_id, start + timedelta(hours=2, minutes=10), 37.4340, -122.1000),
    ]

    trips, summary = service.derive_day(points, date(2026, 7, 8))

    assert len(trips) == 2
    assert summary["trip_count"] == 2
    assert summary["total_distance_m"] == pytest.approx(
        trips[0]["distance_m"] + trips[1]["distance_m"],
    )
