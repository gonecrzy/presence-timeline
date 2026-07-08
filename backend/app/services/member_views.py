from datetime import datetime
from uuid import UUID

from app.repositories.location_repository import LocationRepository


class MemberViewService:
    def __init__(self, db) -> None:
        self.repository = LocationRepository(db)

    def list_members(self, family_slug: str) -> list[dict]:
        members = self.repository.list_members_for_family_slug(family_slug)
        return [
            {
                "id": member.id,
                "display_name": member.display_name,
                "is_child": member.is_child,
                "last_seen_at": member.last_seen_at,
            }
            for member in members
        ]

    def latest_location(self, member_id: UUID) -> dict | None:
        point = self.repository.get_latest_point_for_member(member_id)
        if point is None:
            return None
        return _serialize_point(point)

    def history(self, member_id: UUID, start: datetime, end: datetime) -> list[dict]:
        points = self.repository.list_member_history(member_id, start, end)
        return [_serialize_point(point) for point in points]


def _serialize_point(point) -> dict:
    return {
        "member_id": point.member_id,
        "observed_at": point.observed_at,
        "latitude": point.latitude,
        "longitude": point.longitude,
        "accuracy_m": point.accuracy_m,
        "battery_level": point.battery_level,
        "source_entity_id": point.source_entity_id,
    }
