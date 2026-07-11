from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.stay_derivation import StayDerivationService


def _point(member_id, observed_at, latitude, longitude, accuracy_m=10.0):
    return {
        "member_id": member_id,
        "observed_at": observed_at,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy_m": accuracy_m,
    }


class FakeStayRepository:
    def __init__(self, member_id, points) -> None:
        self.member_id = member_id
        self.points = [
            SimpleNamespace(
                member_id=member_id,
                observed_at=item["observed_at"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                accuracy_m=item["accuracy_m"],
            )
            for item in points
        ]
        self.replaced = None
        self.committed = False

    def list_points_for_member_on_date(self, member_id, start, end):
        assert member_id == self.member_id
        return self.points

    def replace_member_day_stays(self, member_id, target_date, stays):
        assert member_id == self.member_id
        assert target_date == date(2026, 7, 8)
        self.replaced = stays
        return stays

    def commit(self):
        self.committed = True


def test_derivation_builds_stay_for_stationary_cluster() -> None:
    member_id = uuid4()
    service = StayDerivationService(
        dwell_radius_m=250.0,
        minimum_duration_minutes=10,
    )
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4300, -122.0900, 18.0),
        _point(member_id, start + timedelta(minutes=6), 37.4303, -122.0903, 12.0),
        _point(member_id, start + timedelta(minutes=12), 37.4306, -122.0906, 10.0),
    ]

    stays = service.derive_day(points)

    assert len(stays) == 1
    assert stays[0]["started_at"] == start
    assert stays[0]["ended_at"] == start + timedelta(minutes=12)
    assert stays[0]["point_count"] == 3
    assert stays[0]["latitude"] == pytest.approx(37.4303)
    assert stays[0]["longitude"] == pytest.approx(-122.0903)
    assert stays[0]["accuracy_m"] == pytest.approx(10.0)


def test_rebuild_member_day_persists_derived_stays() -> None:
    member_id = uuid4()
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
    points = [
        _point(member_id, start, 37.4300, -122.0900, 18.0),
        _point(member_id, start + timedelta(minutes=6), 37.4303, -122.0903, 12.0),
        _point(member_id, start + timedelta(minutes=12), 37.4306, -122.0906, 10.0),
    ]
    repository = FakeStayRepository(member_id, points)
    service = StayDerivationService(repository=repository)

    stays = service.rebuild_member_day(member_id, date(2026, 7, 8))

    assert len(stays) == 1
    assert repository.replaced is not None
    assert repository.replaced[0]["point_count"] == 3
    assert repository.committed is True
