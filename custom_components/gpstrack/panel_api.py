from __future__ import annotations

from http import HTTPStatus

from aiohttp import web
from homeassistant.components.http import KEY_HASS
from homeassistant.helpers.http import HomeAssistantView

from .const import DATA_COORDINATORS, DOMAIN, PANEL_MEMBER_API, PANEL_SUMMARY_API


class GpsTrackPanelSummaryView(HomeAssistantView):
    url = PANEL_SUMMARY_API
    name = "api:gpstrack:panel:summary"

    async def get(self, request: web.Request) -> web.Response:
        coordinator = _get_primary_coordinator(request)
        payload = await coordinator.api.async_get_summary_payload()
        return self.json(payload)


class GpsTrackPanelMemberView(HomeAssistantView):
    url = PANEL_MEMBER_API
    name = "api:gpstrack:panel:member"

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
        raise web.HTTPServiceUnavailable(reason="GpsTrack integration is not configured.")
    return next(iter(coordinators.values()))
