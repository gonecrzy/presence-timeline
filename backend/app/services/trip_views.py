from datetime import date
from uuid import UUID

from app.repositories.location_repository import LocationRepository
from app.services.trip_derivation import TripDerivationService


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
        return {
            "id": trip.id,
            "member_id": member_id,
            "started_at": trip.started_at,
            "ended_at": trip.ended_at,
            "distance_m": trip.distance_m,
            "point_count": trip.point_count,
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
                for point in points
            ],
        }
