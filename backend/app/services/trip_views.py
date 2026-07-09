from datetime import date
from uuid import UUID

from app.repositories.location_repository import LocationRepository
from app.services.places import haversine_m
from app.services.trip_derivation import TripDerivationService

ROUTE_DWELL_RADIUS_M = 250.0
ROUTE_MINIMUM_SEGMENT_M = 25.0
ROUTE_MAXIMUM_DISPLAY_ACCURACY_M = 50.0


class TripViewService:
    def __init__(self, db) -> None:
        self.repository = LocationRepository(db)
        self.derivation = TripDerivationService(self.repository)

    def trips(self, member_id: UUID, trip_date: date) -> list[dict]:
        self.derivation.rebuild_member_day(member_id, trip_date)
        trips = self.repository.list_trips_for_member_on_date(member_id, trip_date)
        return [
            {
                "id": trip.id,
                "started_at": trip.started_at,
                "ended_at": trip.ended_at,
                "point_count": trip.point_count,
                "distance_m": trip.distance_m,
                "start_label": trip.start_label,
                "end_label": trip.end_label,
            }
            for trip in trips
        ]

    def daily_summary(self, member_id: UUID, summary_date: date) -> dict | None:
        self.derivation.rebuild_member_day(member_id, summary_date)
        summary = self.repository.get_daily_summary_for_member(member_id, summary_date)
        if summary is None:
            return None
        return {
            "summary_date": summary.summary_date,
            "first_seen_at": summary.first_seen_at,
            "last_seen_at": summary.last_seen_at,
            "trip_count": summary.trip_count,
            "total_distance_m": summary.total_distance_m,
        }

    def trip_route(self, member_id: UUID, trip_id: UUID) -> dict | None:
        trip = self.repository.get_trip_for_member(member_id, trip_id)
        if trip is None:
            return None
        points = self.repository.list_member_history(
            member_id,
            trip.started_at,
            trip.ended_at or trip.started_at,
        )
        simplified_points = _simplify_route_points(points)
        return {
            "id": trip.id,
            "member_id": member_id,
            "started_at": trip.started_at,
            "ended_at": trip.ended_at,
            "distance_m": trip.distance_m,
            "point_count": len(simplified_points),
            "points": [
                {
                    "member_id": point.member_id,
                    "observed_at": point.observed_at,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "accuracy_m": point.accuracy_m,
                    "battery_level": point.battery_level,
                    "source_entity_id": point.source_entity_id,
                }
                for point in simplified_points
            ],
        }


def _simplify_route_points(points: list[object]) -> list[object]:
    if not points:
        return []

    filtered_points = _filter_display_points(points)
    if len(filtered_points) < 2:
        return filtered_points

    simplified: list[object] = []
    for point in filtered_points:
        last_kept = simplified[-1] if simplified else None
        if last_kept is None:
            simplified.append(point)
            continue

        distance_from_last = haversine_m(
            last_kept.latitude,
            last_kept.longitude,
            point.latitude,
            point.longitude,
        )
        if distance_from_last <= ROUTE_DWELL_RADIUS_M or distance_from_last < ROUTE_MINIMUM_SEGMENT_M:
            simplified[-1] = point
            continue

        simplified.append(point)

    return simplified


def _filter_display_points(points: list[object]) -> list[object]:
    if not points:
        return []

    filtered = [
        point
        for index, point in enumerate(points)
        if index == 0
        or index == len(points) - 1
        or point.accuracy_m is None
        or point.accuracy_m <= ROUTE_MAXIMUM_DISPLAY_ACCURACY_M
    ]

    deduped: list[object] = []
    for point in filtered:
        previous = deduped[-1] if deduped else None
        if (
            previous is None
            or previous.latitude != point.latitude
            or previous.longitude != point.longitude
            or previous.observed_at != point.observed_at
        ):
            deduped.append(point)
    return deduped
