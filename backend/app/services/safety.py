from __future__ import annotations

from app.services.places import PlaceMatcher


class SafetyDerivationService:
    def __init__(self) -> None:
        self.matcher = PlaceMatcher()

    def derive(self, points: list[dict], places: list[dict]) -> list[dict]:
        safe_places = [place for place in places if place["is_safe_zone"]]
        events = []
        previous_safe_place = None

        for point in sorted(points, key=lambda item: item["observed_at"]):
            matched_place = self.matcher.match(
                places=safe_places,
                latitude=point["latitude"],
                longitude=point["longitude"],
            )

            if previous_safe_place is None and matched_place is not None:
                events.append(
                    {
                        "event_type": "safe_zone_entered",
                        "severity": "info",
                        "observed_at": point["observed_at"],
                        "place_id": matched_place["id"],
                        "payload": {"place_name": matched_place["name"]},
                    }
                )
            elif previous_safe_place is not None and matched_place is None:
                events.append(
                    {
                        "event_type": "safe_zone_exited",
                        "severity": "info",
                        "observed_at": point["observed_at"],
                        "place_id": previous_safe_place["id"],
                        "payload": {"place_name": previous_safe_place["name"]},
                    }
                )
            elif (
                previous_safe_place is not None
                and matched_place is not None
                and previous_safe_place["id"] != matched_place["id"]
            ):
                events.append(
                    {
                        "event_type": "safe_zone_exited",
                        "severity": "info",
                        "observed_at": point["observed_at"],
                        "place_id": previous_safe_place["id"],
                        "payload": {"place_name": previous_safe_place["name"]},
                    }
                )
                events.append(
                    {
                        "event_type": "safe_zone_entered",
                        "severity": "info",
                        "observed_at": point["observed_at"],
                        "place_id": matched_place["id"],
                        "payload": {"place_name": matched_place["name"]},
                    }
                )

            previous_safe_place = matched_place

        return events
