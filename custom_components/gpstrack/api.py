from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aiohttp import ClientSession, ContentTypeError
from homeassistant.util import dt as dt_util

from .const import API_TIMEOUT_SECONDS


class GpsTrackApiError(Exception):
    """Base API error."""


class GpsTrackApiAuthError(GpsTrackApiError):
    """Raised when the backend rejects authentication."""


@dataclass(slots=True)
class MemberSnapshot:
    member_id: str
    display_name: str
    is_child: bool
    last_seen_at: datetime | None
    current_location_label: str | None
    latitude: float | None
    longitude: float | None
    accuracy_m: float | None
    battery_level: int | None
    observed_at: datetime | None
    source_entity_id: str | None


class GpsTrackApiClient:
    def __init__(self, session: ClientSession, base_url: str, access_token: str | None = None) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._access_token = (access_token or "").strip()

    async def async_validate_connection(self) -> None:
        await self.async_get_summary()

    async def async_get_summary(self) -> dict[str, MemberSnapshot]:
        payload = await self._async_get_json("/api/v1/home-assistant/summary")
        items = payload.get("items", [])
        return {
            snapshot.member_id: snapshot
            for snapshot in (self._parse_member(item) for item in items)
        }

    async def _async_get_json(self, path: str) -> dict:
        headers = {}
        if self._access_token:
            headers["Authorization"] = _authorization_header(self._access_token)

        async with self._session.get(
            f"{self._base_url}{path}",
            headers=headers,
            timeout=API_TIMEOUT_SECONDS,
        ) as response:
            if response.status in (401, 403):
                raise GpsTrackApiAuthError("GpsTrack backend rejected authentication.")
            if response.status >= 400:
                body = await response.text()
                raise GpsTrackApiError(f"GpsTrack backend request failed: {response.status} {body}")
            try:
                return await response.json()
            except (ContentTypeError, ValueError) as err:
                raise GpsTrackApiError("GpsTrack backend returned invalid JSON.") from err

    def _parse_member(self, item: dict) -> MemberSnapshot:
        return MemberSnapshot(
            member_id=str(item["member_id"]),
            display_name=item["display_name"],
            is_child=item["is_child"],
            last_seen_at=_parse_datetime(item.get("last_seen_at")),
            current_location_label=item.get("current_location_label"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            accuracy_m=item.get("accuracy_m"),
            battery_level=item.get("battery_level"),
            observed_at=_parse_datetime(item.get("observed_at")),
            source_entity_id=item.get("source_entity_id"),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return dt_util.parse_datetime(value)


def _authorization_header(access_token: str) -> str:
    lowered = access_token.lower()
    if lowered.startswith("bearer ") or lowered.startswith("basic "):
        return access_token
    return f"Bearer {access_token}"
