from __future__ import annotations

from datetime import timedelta
import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GpsTrackApiAuthError, GpsTrackApiClient, GpsTrackApiError, MemberSnapshot
from .api import IntegrationStatusSnapshot
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN

LOGGER = logging.getLogger(__name__)


class GpsTrackCoordinator(DataUpdateCoordinator[dict[str, MemberSnapshot]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: GpsTrackApiClient) -> None:
        self.api = api
        self.entry_id = entry.entry_id
        self.integration_status = IntegrationStatusSnapshot.unknown()
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=int(entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS))
            ),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, MemberSnapshot]:
        try:
            summary = await self.api.async_get_summary()
        except GpsTrackApiAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (GpsTrackApiError, ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Unable to fetch Presence Timeline summary: {err}") from err

        try:
            self.integration_status = await self.api.async_get_ingestion_status()
        except (GpsTrackApiError, ClientError, TimeoutError) as err:
            LOGGER.warning("Unable to fetch Presence Timeline ingestion status: %s", err)
            self.integration_status = IntegrationStatusSnapshot.unknown()

        return summary
