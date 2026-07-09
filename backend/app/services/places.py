from __future__ import annotations

import math

import httpx

from app.core.config import get_settings


class PlaceMatcher:
    def match(self, places: list[dict], latitude: float, longitude: float) -> dict | None:
        best_match = None
        best_distance = None
        for place in places:
            distance = haversine_m(latitude, longitude, place["latitude"], place["longitude"])
            if distance <= place["radius_m"] and (best_distance is None or distance < best_distance):
                best_match = place
                best_distance = distance
        return best_match


class ReverseGeocoder:
    def __init__(
        self,
        *,
        enabled: bool | None = None,
        endpoint: str | None = None,
        user_agent: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        settings = get_settings()
        self.enabled = settings.enable_reverse_geocoding if enabled is None else enabled
        self.endpoint = settings.reverse_geocode_url if endpoint is None else endpoint
        self.user_agent = settings.reverse_geocode_user_agent if user_agent is None else user_agent
        self.timeout_seconds = (
            settings.reverse_geocode_timeout_seconds if timeout_seconds is None else timeout_seconds
        )

    def reverse(self, latitude: float, longitude: float) -> str | None:
        if not self.enabled:
            return None

        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = client.get(
                    self.endpoint,
                    params={
                        "format": "jsonv2",
                        "lat": latitude,
                        "lon": longitude,
                        "zoom": 18,
                        "addressdetails": 1,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError:
            return None

        return response.json().get("display_name")


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
