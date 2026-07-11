from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace
from uuid import UUID

from app.repositories.location_repository import LocationRepository
from app.services.stops import derive_stops


class StayDerivationService:
    def __init__(
        self,
        repository: LocationRepository | None = None,
        *,
        dwell_radius_m: float = 250.0,
        minimum_duration_minutes: int = 10,
    ) -> None:
        self.repository = repository
        self.dwell_radius_m = dwell_radius_m
        self.minimum_duration = timedelta(minutes=minimum_duration_minutes)

    def derive_day(self, points: list[dict | object]) -> list[dict]:
        normalized_points = [_normalize_point(point) for point in points]
        derived_stays = derive_stops(
            normalized_points,
            dwell_radius_m=self.dwell_radius_m,
            minimum_duration=self.minimum_duration,
        )
        return [
            {
                "started_at": stay.started_at,
                "ended_at": stay.ended_at,
                "latitude": stay.latitude,
                "longitude": stay.longitude,
                "point_count": stay.point_count,
                "accuracy_m": stay.accuracy_m,
            }
            for stay in derived_stays
        ]

    def rebuild_member_day(
        self,
        member_id: UUID,
        target_date: date,
    ):
        if self.repository is None:
            raise RuntimeError("StayDerivationService requires a repository for persistence.")

        day_start = datetime.combine(target_date, time.min, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        points = self.repository.list_points_for_member_on_date(member_id, day_start, day_end)
        derived_stays = self.derive_day(points)
        stays = self.repository.replace_member_day_stays(member_id, target_date, derived_stays)
        self.repository.commit()
        return stays


def _normalize_point(point: dict | object):
    if isinstance(point, dict):
        return SimpleNamespace(
            observed_at=point["observed_at"],
            latitude=point["latitude"],
            longitude=point["longitude"],
            accuracy_m=point.get("accuracy_m"),
        )
    return point
