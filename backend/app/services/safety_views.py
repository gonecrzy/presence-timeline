from datetime import datetime
from uuid import UUID

from app.repositories.location_repository import LocationRepository
from app.services.safety import SafetyDerivationService


class SafetyViewService:
    def __init__(self, db) -> None:
        self.repository = LocationRepository(db)
        self.derivation = SafetyDerivationService()

    def events(self, member_id: UUID, start: datetime, end: datetime) -> list[dict]:
        member = self.repository.get_member(member_id)
        if member is None:
            return []
        places = [
            {
                "id": place.id,
                "name": place.name,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "radius_m": place.radius_m,
                "is_safe_zone": place.is_safe_zone,
            }
            for place in self.repository.list_places_for_family_id(member.family_id)
        ]
        points = [
            {
                "member_id": point.member_id,
                "observed_at": point.observed_at,
                "latitude": point.latitude,
                "longitude": point.longitude,
            }
            for point in self.repository.list_member_history(member_id, start, end)
        ]
        self.repository.replace_safety_events_for_range(
            member_id,
            start,
            end,
            self.derivation.derive(points=points, places=places),
        )
        self.repository.commit()
        events = self.repository.list_safety_events_for_range(member_id, start, end)
        return [
            {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "observed_at": event.observed_at,
                "place_id": event.place_id,
                "payload": event.payload,
            }
            for event in events
        ]
