from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GpsTrackApiClient
from .const import CONF_ACCESS_TOKEN, CONF_BASE_URL, DOMAIN, PLATFORMS
from .coordinator import GpsTrackCoordinator
from .panel import async_register_panel, async_unregister_panel
from .panel_api import GpsTrackPanelMemberView, GpsTrackPanelSummaryView


async def async_setup(hass: HomeAssistant, _config) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await _async_ensure_panel_registered(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = GpsTrackApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_BASE_URL],
        entry.data.get(CONF_ACCESS_TOKEN),
    )
    coordinator = GpsTrackCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await _async_ensure_panel_registered(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        active_entries = [
            key
            for key in hass.data[DOMAIN]
            if isinstance(key, str) and not key.startswith("__")
        ]
        if not active_entries and hass.data[DOMAIN].get("__panel_registered__"):
            async_unregister_panel(hass)
            hass.data[DOMAIN].pop("__panel_registered__", None)
    return unload_ok


async def _async_ensure_panel_registered(hass: HomeAssistant) -> None:
    if hass.data[DOMAIN].get("__panel_registered__"):
        return

    hass.http.register_view(GpsTrackPanelSummaryView())
    hass.http.register_view(GpsTrackPanelMemberView())
    await async_register_panel(hass)
    hass.data[DOMAIN]["__panel_registered__"] = True
