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

    def reverse_payload(self, latitude: float, longitude: float) -> dict | None:
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

        return response.json()

    def reverse(self, latitude: float, longitude: float, *, granularity: str = "full") -> str | None:
        payload = self.reverse_payload(latitude, longitude)
        if payload is None:
            return None
        return format_reverse_geocode_label(payload, granularity=granularity)


class SearchGeocoder:
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
        self.endpoint = settings.search_geocode_url if endpoint is None else endpoint
        self.user_agent = settings.reverse_geocode_user_agent if user_agent is None else user_agent
        self.timeout_seconds = (
            settings.reverse_geocode_timeout_seconds if timeout_seconds is None else timeout_seconds
        )

    def search(self, query: str) -> list[dict]:
        if not self.enabled or not query.strip():
            return []

        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = client.get(
                    self.endpoint,
                    params={
                        "format": "jsonv2",
                        "q": query,
                        "limit": 5,
                        "addressdetails": 1,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError:
            return []

        results = []
        for item in response.json():
            label = format_reverse_geocode_label(item) or item.get("display_name")
            latitude = item.get("lat")
            longitude = item.get("lon")
            if label is None or latitude is None or longitude is None:
                continue
            results.append(
                {
                    "label": label,
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                }
            )
        return results


def format_reverse_geocode_place_name(payload: dict) -> str | None:
    namedetails = payload.get("namedetails") or {}
    if namedetails.get("name"):
        return namedetails["name"]
    if payload.get("name"):
        return payload["name"]

    address = payload.get("address") or {}
    for key in (
        "amenity",
        "shop",
        "tourism",
        "leisure",
        "office",
        "building",
        "attraction",
    ):
        value = address.get(key)
        if value:
            return str(value)
    return None


def choose_address_granularity(
    *,
    accuracy_m: float | None,
    duration_seconds: int | None = None,
    point_count: int | None = None,
    moving: bool = False,
) -> str:
    if moving:
        if accuracy_m is not None and accuracy_m <= 60.0:
            return "street"
        return "locality"

    if (
        accuracy_m is not None
        and accuracy_m <= 10.0
        and (duration_seconds or 0) >= 10 * 60
        and (point_count or 0) >= 3
    ):
        return "full"
    if (
        accuracy_m is not None
        and accuracy_m <= 25.0
        and (duration_seconds or 0) >= 10 * 60
        and (point_count or 0) >= 2
    ):
        return "block"
    if accuracy_m is None or accuracy_m <= 120.0:
        return "street"
    return "locality"


def format_reverse_geocode_label(payload: dict, *, granularity: str = "full") -> str | None:
    address = payload.get("address") or {}
    road = address.get("road") or address.get("pedestrian")
    locality = (
        address.get("suburb")
        or address.get("neighbourhood")
        or address.get("village")
        or address.get("town")
        or address.get("city")
        or address.get("hamlet")
    )
    region = address.get("state")
    postcode = address.get("postcode")
    house_number = address.get("house_number")

    if granularity == "locality":
        parts = [locality, region]
        label = ", ".join(part for part in parts if part)
        return label or payload.get("display_name")

    if granularity == "street":
        parts = [road, locality]
        label = ", ".join(part for part in parts if part)
        return label or payload.get("display_name")

    if granularity == "block":
        block = _house_number_block_label(house_number, road)
        parts = [block, locality]
        label = ", ".join(part for part in parts if part)
        return label or format_reverse_geocode_label(payload, granularity="street")

    street_bits = [house_number, road]
    street = " ".join(bit for bit in street_bits if bit)

    parts = [street or None, locality, " ".join(bit for bit in [region, postcode] if bit) or None]
    label = ", ".join(part for part in parts if part)
    return label or payload.get("display_name")


def _house_number_block_label(house_number: str | None, road: str | None) -> str | None:
    if road is None:
        return None
    try:
        number = int("".join(char for char in (house_number or "") if char.isdigit()))
    except ValueError:
        number = None
    if number is None:
        return road
    block_start = (number // 100) * 100
    return f"{block_start} block of {road}"


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
