from app.services.member_views import MemberViewService


class HomeAssistantViewService:
    def __init__(self, db) -> None:
        self.member_views = MemberViewService(db)

    def summary(self, family_slug: str) -> list[dict]:
        items = []
        for member in self.member_views.list_members(family_slug):
            latest_point = self.member_views.latest_location(member["id"])
            items.append(
                {
                    "member_id": member["id"],
                    "display_name": member["display_name"],
                    "is_child": member["is_child"],
                    "last_seen_at": member["last_seen_at"],
                    "current_location_label": member["current_location_label"],
                    "latitude": latest_point["latitude"] if latest_point is not None else None,
                    "longitude": latest_point["longitude"] if latest_point is not None else None,
                    "accuracy_m": latest_point["accuracy_m"] if latest_point is not None else None,
                    "battery_level": latest_point["battery_level"] if latest_point is not None else None,
                    "observed_at": latest_point["observed_at"] if latest_point is not None else None,
                    "source_entity_id": latest_point["source_entity_id"] if latest_point is not None else None,
                }
            )
        return items
