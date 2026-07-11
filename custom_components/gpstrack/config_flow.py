from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GpsTrackApiAuthError, GpsTrackApiClient, GpsTrackApiError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)


class GpsTrackConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input = _normalize_user_input(user_input)
            if _is_duplicate_base_url(self._async_current_entries(), normalized_input[CONF_BASE_URL]):
                return self.async_abort(reason="already_configured")

            try:
                info = await _validate_input(self.hass, normalized_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=normalized_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )


def _user_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_BASE_URL, default=user_input.get(CONF_BASE_URL, "http://localhost:8000")): str,
            vol.Optional(CONF_ACCESS_TOKEN, default=user_input.get(CONF_ACCESS_TOKEN, "")): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS),
            ): vol.All(vol.Coerce(int), vol.Range(min=15, max=3600)),
        }
    )


async def _validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    client = GpsTrackApiClient(
        async_get_clientsession(hass),
        user_input[CONF_BASE_URL],
        user_input.get(CONF_ACCESS_TOKEN),
    )
    try:
        await client.async_validate_connection()
    except GpsTrackApiAuthError as err:
        raise InvalidAuth from err
    except (GpsTrackApiError, ClientError, TimeoutError) as err:
        raise CannotConnect from err

    parsed = urlparse(user_input[CONF_BASE_URL])
    title = parsed.hostname or "GpsTrack"
    return {"title": title}


def _normalize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_BASE_URL: user_input[CONF_BASE_URL].strip().rstrip("/"),
        CONF_ACCESS_TOKEN: user_input.get(CONF_ACCESS_TOKEN, "").strip(),
        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
    }


def _is_duplicate_base_url(entries: list, base_url: str) -> bool:
    return any(entry.data.get(CONF_BASE_URL) == base_url for entry in entries)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
