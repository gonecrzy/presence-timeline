from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    PANEL_MEMBER_API,
    PANEL_FRONTEND_URL_PATH,
    PANEL_ICON,
    PANEL_MODULE_STATIC_URL,
    PANEL_MODULE_URL,
    PANEL_SUMMARY_API,
    PANEL_STATIC_PATH,
    PANEL_TITLE,
    PANEL_WEB_COMPONENT,
)


async def async_register_panel(hass: HomeAssistant) -> None:
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                PANEL_MODULE_STATIC_URL,
                str(Path(__file__).parent / PANEL_STATIC_PATH),
                cache_headers=False,
            )
        ]
    )
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_FRONTEND_URL_PATH,
        webcomponent_name=PANEL_WEB_COMPONENT,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url=PANEL_MODULE_URL,
        config={
            "summaryApi": PANEL_SUMMARY_API,
            "memberApiTemplate": PANEL_MEMBER_API,
            "defaultHistoryHours": 24,
        },
    )


def async_unregister_panel(hass: HomeAssistant) -> None:
    frontend.async_remove_panel(hass, PANEL_FRONTEND_URL_PATH, warn_if_unknown=False)
