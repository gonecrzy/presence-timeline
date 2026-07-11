from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.stops import derive_stops


def test_derive_stops_uses_cluster_centroid_coordinates() -> None:
    points = [
        SimpleNamespace(
            observed_at=datetime(2026, 7, 8, 20, 0, tzinfo=UTC),
            latitude=37.43,
            longitude=-122.09,
            accuracy_m=18.0,
        ),
        SimpleNamespace(
            observed_at=datetime(2026, 7, 8, 20, 6, tzinfo=UTC),
            latitude=37.4303,
            longitude=-122.0903,
            accuracy_m=12.0,
        ),
        SimpleNamespace(
            observed_at=datetime(2026, 7, 8, 20, 12, tzinfo=UTC),
            latitude=37.4306,
            longitude=-122.0906,
            accuracy_m=10.0,
        ),
    ]

    stops = derive_stops(
        points,
        dwell_radius_m=250.0,
        minimum_duration=timedelta(minutes=10),
    )

    assert len(stops) == 1
    assert stops[0].latitude == pytest.approx(37.4303)
    assert stops[0].longitude == pytest.approx(-122.0903)
    assert stops[0].accuracy_m == pytest.approx(10.0)
