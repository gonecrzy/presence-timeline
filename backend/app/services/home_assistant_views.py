from datetime import timedelta
from uuid import UUID

from app.services.member_views import MemberViewService

STATUS_MOVING = "moving"
STATUS_STOPPED = "stopped"
STATUS_UNKNOWN = "unknown"

STATUS_WINDOW = timedelta(days=1)


class HomeAssistantViewService:
    def __init__(self, db) -> None:
        self.member_views = MemberViewService(db)

    def summary(self, family_slug: str) -> list[dict]:
        items = []
        for member in self.member_views.list_members(family_slug):
            latest_point = self.member_views.latest_location(member["id"])
            current_stop = self._current_stop(member["id"], latest_point)
            status = STATUS_UNKNOWN
            status_detail = None
            if current_stop is not None:
                status = STATUS_STOPPED
                status_detail = current_stop["label"]
            elif latest_point is not None:
                status = STATUS_MOVING
            items.append(
                {
                    "member_id": member["id"],
                    "display_name": member["display_name"],
                    "is_child": member["is_child"],
                    "last_seen_at": member["last_seen_at"],
                    "current_location_label": member["current_location_label"],
                    "status": status,
                    "status_detail": status_detail,
                    "latitude": latest_point["latitude"] if latest_point is not None else None,
                    "longitude": latest_point["longitude"] if latest_point is not None else None,
                    "accuracy_m": latest_point["accuracy_m"] if latest_point is not None else None,
                    "battery_level": latest_point["battery_level"] if latest_point is not None else None,
                    "observed_at": latest_point["observed_at"] if latest_point is not None else None,
                    "source_entity_id": latest_point["source_entity_id"] if latest_point is not None else None,
                }
            )
        return items

    def member_panel(
        self,
        family_slug: str,
        member_id: UUID,
        start,
        end,
    ) -> dict | None:
        member = next(
            (item for item in self.summary(family_slug) if item["member_id"] == member_id),
            None,
        )
        if member is None:
            return None

        return {
            "member": member,
            "history": self.member_views.history(member_id, start, end),
            "timeline": self.member_views.timeline(member_id, start, end),
            "stops": self.member_views.stops(member_id, start, end),
        }

    def _current_stop(self, member_id: UUID, latest_point: dict | None) -> dict | None:
        if latest_point is None:
            return None

        stops = self.member_views.stops(
            member_id,
            latest_point["observed_at"] - STATUS_WINDOW,
            latest_point["observed_at"],
        )
        return next((stop for stop in reversed(stops) if stop.get("is_current")), None)
