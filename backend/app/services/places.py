from __future__ import annotations

import math


class PlaceMatcher:
    def match(self, places: list[dict], latitude: float, longitude: float) -> dict | None:
        best_match = None
        best_distance = None
        for place in places:
            distance = _haversine_m(latitude, longitude, place["latitude"], place["longitude"])
            if distance <= place["radius_m"] and (best_distance is None or distance < best_distance):
                best_match = place
                best_distance = distance
        return best_match


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
