from __future__ import annotations

from http import HTTPStatus

from aiohttp import web
from homeassistant.components.http import KEY_HASS
from homeassistant.helpers.http import HomeAssistantView

from .api import IntegrationStatusSnapshot
from .const import DATA_COORDINATORS, DOMAIN, PANEL_MEMBER_API, PANEL_SUMMARY_API


class GpsTrackPanelSummaryView(HomeAssistantView):
    url = PANEL_SUMMARY_API
    name = "api:presence_timeline:panel:summary"

    async def get(self, request: web.Request) -> web.Response:
        coordinator = _get_primary_coordinator(request)
        payload = await coordinator.api.async_get_summary_payload()
        return self.json(
            {
                "items": payload.get("items", []),
                "integration_status": _serialize_integration_status(
                    coordinator.integration_status
                ),
            }
        )


class GpsTrackPanelMemberView(HomeAssistantView):
    url = PANEL_MEMBER_API
    name = "api:presence_timeline:panel:member"

    async def get(self, request: web.Request, member_id: str) -> web.Response:
        start = request.query.get("start")
        end = request.query.get("end")
        if not start or not end:
            return self.json_message(
                "Missing required start/end query parameters.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        coordinator = _get_primary_coordinator(request)
        payload = await coordinator.api.async_get_member_panel(
            member_id,
            start=start,
            end=end,
        )
        return self.json(payload)


def _get_primary_coordinator(request: web.Request):
    hass = request.app[KEY_HASS]
    domain_data = hass.data.get(DOMAIN, {})
    coordinators = domain_data.get(DATA_COORDINATORS, {})
    if not coordinators:
        coordinators = {
            key: value
            for key, value in domain_data.items()
            if key not in (DATA_COORDINATORS, DOMAIN) and hasattr(value, "api")
        }
    if not coordinators:
        raise web.HTTPServiceUnavailable(reason="Presence Timeline integration is not configured.")
    return next(iter(coordinators.values()))


def _serialize_integration_status(
    status: IntegrationStatusSnapshot,
) -> dict[str, str | int | None]:
    return {
        "provider": status.provider,
        "state": status.state,
        "last_snapshot_at": status.last_snapshot_at.isoformat() if status.last_snapshot_at else None,
        "last_connected_at": status.last_connected_at.isoformat() if status.last_connected_at else None,
        "last_event_at": status.last_event_at.isoformat() if status.last_event_at else None,
        "last_error_at": status.last_error_at.isoformat() if status.last_error_at else None,
        "last_error_message": status.last_error_message,
        "retry_delay_seconds": status.retry_delay_seconds,
    }
