from __future__ import annotations

import math
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from app.models.location import DailySummary
from app.models.trip import Trip
from app.repositories.location_repository import LocationRepository


class TripDerivationService:
    def __init__(
        self,
        repository: LocationRepository | None = None,
        *,
        max_trip_gap_minutes: int = 30,
        min_trip_distance_m: float = 250.0,
    ) -> None:
        self.repository = repository
        self.max_trip_gap_minutes = max_trip_gap_minutes
        self.min_trip_distance_m = min_trip_distance_m

    def derive_day(self, points: list[dict], target_date: date) -> tuple[list[dict], dict]:
        ordered_points = sorted(points, key=lambda point: point["observed_at"])
        summary = {
            "summary_date": target_date,
            "first_seen_at": ordered_points[0]["observed_at"] if ordered_points else None,
            "last_seen_at": ordered_points[-1]["observed_at"] if ordered_points else None,
            "trip_count": 0,
            "total_distance_m": 0.0,
        }
        if len(ordered_points) < 2:
            return [], summary

        sessions: list[list[dict]] = []
        current_session = [ordered_points[0]]
        max_gap = timedelta(minutes=self.max_trip_gap_minutes)

        for point in ordered_points[1:]:
            if point["observed_at"] - current_session[-1]["observed_at"] > max_gap:
                sessions.append(current_session)
                current_session = [point]
            else:
                current_session.append(point)
        sessions.append(current_session)

        trips = []
        for session in sessions:
            distance_m = _session_distance_m(session)
            if len(session) < 2 or distance_m < self.min_trip_distance_m:
                continue
            trips.append(
                {
                    "started_at": session[0]["observed_at"],
                    "ended_at": session[-1]["observed_at"],
                    "point_count": len(session),
                    "distance_m": round(distance_m, 2),
                    "start_label": None,
                    "end_label": None,
                }
            )

        summary["trip_count"] = len(trips)
        summary["total_distance_m"] = round(sum(trip["distance_m"] for trip in trips), 2)
        return trips, summary

    def rebuild_member_day(
        self,
        member_id: UUID,
        target_date: date,
    ) -> tuple[list[Trip], DailySummary]:
        if self.repository is None:
            raise RuntimeError("TripDerivationService requires a repository for persistence.")

        day_start = datetime.combine(target_date, time.min, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        points = [
            {
                "member_id": point.member_id,
                "observed_at": point.observed_at,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "source_entity_id": point.source_entity_id,
            }
            for point in self.repository.list_points_for_member_on_date(member_id, day_start, day_end)
        ]
        derived_trips, derived_summary = self.derive_day(points, target_date)
        trips = self.repository.replace_member_day_trips(member_id, target_date, derived_trips)
        summary = self.repository.replace_daily_summary(member_id, derived_summary)
        self.repository.commit()
        return trips, summary


def _session_distance_m(points: list[dict]) -> float:
    total = 0.0
    for previous, current in zip(points, points[1:], strict=False):
        total += _haversine_m(
            previous["latitude"],
            previous["longitude"],
            current["latitude"],
            current["longitude"],
        )
    return total


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c
