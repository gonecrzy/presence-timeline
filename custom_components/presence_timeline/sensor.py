from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import IntegrationStatusSnapshot, MemberSnapshot
from .const import DOMAIN
from .coordinator import GpsTrackCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GpsTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_member_ids: set[str] = set()
    status_entities_added = False

    @callback
    def async_sync_entities() -> None:
        nonlocal status_entities_added
        new_entities = []
        if not status_entities_added:
            status_entities_added = True
            new_entities.extend(
                [
                    GpsTrackIntegrationStateSensor(coordinator),
                    GpsTrackIntegrationLastSnapshotSensor(coordinator),
                    GpsTrackIntegrationLastConnectedSensor(coordinator),
                    GpsTrackIntegrationLastEventSensor(coordinator),
                    GpsTrackIntegrationRetryDelaySensor(coordinator),
                    GpsTrackIntegrationLastErrorSensor(coordinator),
                ]
            )
        for member_id in coordinator.data:
            if member_id in known_member_ids:
                continue
            known_member_ids.add(member_id)
            new_entities.extend(
                [
                    GpsTrackMemberBatterySensor(coordinator, member_id),
                    GpsTrackMemberPlaceSensor(coordinator, member_id),
                    GpsTrackMemberLastSeenSensor(coordinator, member_id),
                ]
            )
        if new_entities:
            async_add_entities(new_entities)

    async_sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(async_sync_entities))


class GpsTrackMemberSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GpsTrackCoordinator, member_id: str) -> None:
        super().__init__(coordinator)
        self._member_id = member_id

    @property
    def device_info(self) -> DeviceInfo:
        member = self.member
        return DeviceInfo(
            identifiers={(DOMAIN, self._member_id)},
            name=member.display_name if member is not None else "Presence Timeline Member",
            manufacturer="Presence Timeline",
            model="Tracked Member",
        )

    @property
    def member(self) -> MemberSnapshot | None:
        return self.coordinator.data.get(self._member_id)


class GpsTrackIntegrationSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GpsTrackCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_{unique_suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.entry_id}_integration")},
            name="Presence Timeline",
            manufacturer="Presence Timeline",
            model="Home Assistant Integration",
        )

    @property
    def integration_status(self) -> IntegrationStatusSnapshot:
        return self.coordinator.integration_status


class GpsTrackIntegrationStateSensor(GpsTrackIntegrationSensor):
    _attr_name = "Ingestion Status"
    _attr_icon = "mdi:connection"

    def __init__(self, coordinator: GpsTrackCoordinator) -> None:
        super().__init__(coordinator, "integration_status")

    @property
    def native_value(self) -> str:
        return self.integration_status.state


class GpsTrackIntegrationLastSnapshotSensor(GpsTrackIntegrationSensor):
    _attr_name = "Last Snapshot"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: GpsTrackCoordinator) -> None:
        super().__init__(coordinator, "integration_last_snapshot")

    @property
    def available(self) -> bool:
        return bool(super().available and self.integration_status.last_snapshot_at is not None)

    @property
    def native_value(self) -> datetime | None:
        return self.integration_status.last_snapshot_at


class GpsTrackIntegrationLastConnectedSensor(GpsTrackIntegrationSensor):
    _attr_name = "Last Connected"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: GpsTrackCoordinator) -> None:
        super().__init__(coordinator, "integration_last_connected")

    @property
    def available(self) -> bool:
        return bool(super().available and self.integration_status.last_connected_at is not None)

    @property
    def native_value(self) -> datetime | None:
        return self.integration_status.last_connected_at


class GpsTrackIntegrationLastEventSensor(GpsTrackIntegrationSensor):
    _attr_name = "Last Event"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: GpsTrackCoordinator) -> None:
        super().__init__(coordinator, "integration_last_event")

    @property
    def available(self) -> bool:
        return bool(super().available and self.integration_status.last_event_at is not None)

    @property
    def native_value(self) -> datetime | None:
        return self.integration_status.last_event_at


class GpsTrackIntegrationRetryDelaySensor(GpsTrackIntegrationSensor):
    _attr_name = "Retry Delay"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator: GpsTrackCoordinator) -> None:
        super().__init__(coordinator, "integration_retry_delay")

    @property
    def available(self) -> bool:
        return bool(super().available and self.integration_status.retry_delay_seconds is not None)

    @property
    def native_value(self) -> int | None:
        return self.integration_status.retry_delay_seconds


class GpsTrackIntegrationLastErrorSensor(GpsTrackIntegrationSensor):
    _attr_name = "Last Error"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator: GpsTrackCoordinator) -> None:
        super().__init__(coordinator, "integration_last_error")

    @property
    def available(self) -> bool:
        return bool(super().available and self.integration_status.last_error_message)

    @property
    def native_value(self) -> str | None:
        return self.integration_status.last_error_message


class GpsTrackMemberBatterySensor(GpsTrackMemberSensor):
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GpsTrackCoordinator, member_id: str) -> None:
        super().__init__(coordinator, member_id)
        self._attr_unique_id = f"{member_id}_battery"

    @property
    def available(self) -> bool:
        member = self.member
        return bool(super().available and member is not None and member.battery_level is not None)

    @property
    def native_value(self) -> int | None:
        member = self.member
        return None if member is None else member.battery_level


class GpsTrackMemberPlaceSensor(GpsTrackMemberSensor):
    _attr_name = "Place"

    def __init__(self, coordinator: GpsTrackCoordinator, member_id: str) -> None:
        super().__init__(coordinator, member_id)
        self._attr_unique_id = f"{member_id}_place"

    @property
    def available(self) -> bool:
        member = self.member
        return bool(super().available and member is not None and member.current_location_label is not None)

    @property
    def native_value(self) -> str | None:
        member = self.member
        return None if member is None else member.current_location_label


class GpsTrackMemberLastSeenSensor(GpsTrackMemberSensor):
    _attr_name = "Last Seen"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GpsTrackCoordinator, member_id: str) -> None:
        super().__init__(coordinator, member_id)
        self._attr_unique_id = f"{member_id}_last_seen"

    @property
    def available(self) -> bool:
        member = self.member
        return bool(
            super().available
            and member is not None
            and (member.observed_at is not None or member.last_seen_at is not None)
        )

    @property
    def native_value(self) -> datetime | None:
        member = self.member
        if member is None:
            return None
        return member.observed_at or member.last_seen_at
