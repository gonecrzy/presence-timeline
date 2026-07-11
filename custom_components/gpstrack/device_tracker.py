from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import MemberSnapshot
from .const import DOMAIN
from .coordinator import GpsTrackCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GpsTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_member_ids: set[str] = set()

    @callback
    def async_sync_entities() -> None:
        new_entities = []
        for member_id in coordinator.data:
            if member_id in known_member_ids:
                continue
            known_member_ids.add(member_id)
            new_entities.append(GpsTrackMemberTrackerEntity(coordinator, member_id))
        if new_entities:
            async_add_entities(new_entities)

    async_sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(async_sync_entities))


class GpsTrackMemberTrackerEntity(CoordinatorEntity, TrackerEntity):
    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_icon = "mdi:map-marker-account"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: GpsTrackCoordinator, member_id: str) -> None:
        super().__init__(coordinator)
        self._member_id = member_id
        self._attr_unique_id = f"{member_id}_location"

    @property
    def device_info(self) -> DeviceInfo:
        member = self.member
        return DeviceInfo(
            identifiers={(DOMAIN, self._member_id)},
            name=member.display_name if member is not None else "GpsTrack Member",
            manufacturer="GpsTrack",
            model="Tracked Member",
        )

    @property
    def available(self) -> bool:
        member = self.member
        return bool(
            super().available
            and member is not None
            and member.latitude is not None
            and member.longitude is not None
        )

    @property
    def latitude(self) -> float | None:
        member = self.member
        return None if member is None else member.latitude

    @property
    def longitude(self) -> float | None:
        member = self.member
        return None if member is None else member.longitude

    @property
    def location_accuracy(self) -> float | None:
        member = self.member
        return None if member is None else member.accuracy_m

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        member = self.member
        if member is None:
            return {}

        attributes: dict[str, Any] = {"is_child": member.is_child}
        if member.current_location_label:
            attributes["current_location_label"] = member.current_location_label
        if member.source_entity_id:
            attributes["source_entity_id"] = member.source_entity_id
        if member.observed_at is not None:
            attributes["observed_at"] = member.observed_at.isoformat()
        return attributes

    @property
    def member(self) -> MemberSnapshot | None:
        return self.coordinator.data.get(self._member_id)
