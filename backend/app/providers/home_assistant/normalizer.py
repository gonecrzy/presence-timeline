from datetime import datetime
from typing import Any, Mapping

from app.domain.events import NormalizedLocationEvent, ProviderName


class HomeAssistantEventNormalizer:
    """Translate Home Assistant state events into provider-agnostic location events."""

    def normalize(
        self,
        payload: dict[str, Any],
        *,
        state_index: Mapping[str, dict[str, Any]] | None = None,
    ) -> NormalizedLocationEvent | None:
        if payload.get("event", {}).get("event_type") != "state_changed":
            return None

        new_state = payload.get("event", {}).get("data", {}).get("new_state") or {}
        observed_at = new_state.get("last_updated") or payload.get("event", {}).get("time_fired")
        if not observed_at:
            return None

        return self.normalize_state(
            {
                "entity_id": new_state.get("entity_id", ""),
                "attributes": new_state.get("attributes") or {},
                "last_updated": observed_at,
                "state": new_state.get("state"),
            },
            raw_payload=payload,
            state_index=state_index,
        )

    def normalize_state(
        self,
        state: dict[str, Any],
        *,
        raw_payload: dict[str, Any] | None = None,
        state_index: Mapping[str, dict[str, Any]] | None = None,
    ) -> NormalizedLocationEvent | None:
        entity_id = state.get("entity_id", "")
        attributes = state.get("attributes") or {}

        if not entity_id.startswith("device_tracker."):
            return None

        mirrored_source = attributes.get("source_entity_id")
        if (
            isinstance(mirrored_source, str)
            and mirrored_source
            and mirrored_source != entity_id
        ):
            return None

        latitude = attributes.get("latitude")
        longitude = attributes.get("longitude")
        if latitude is None or longitude is None:
            return None

        observed_at = state.get("last_updated")
        if not observed_at:
            return None

        battery_level = _coerce_int(attributes.get("battery_level"))
        is_charging = _coerce_bool(attributes.get("battery_charging"))
        if state_index is not None:
            tracker_slug = entity_id.split(".", 1)[-1]
            if battery_level is None:
                battery_level = _lookup_related_battery_level(state_index, tracker_slug)
            if is_charging is None:
                is_charging = _lookup_related_charging_state(state_index, tracker_slug)

        return NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id=entity_id,
            source_device_id=None,
            source_device_name=attributes.get("friendly_name"),
            observed_at=datetime.fromisoformat(observed_at.replace("Z", "+00:00")),
            latitude=float(latitude),
            longitude=float(longitude),
            altitude_m=_coerce_float(attributes.get("altitude")),
            accuracy_m=_coerce_float(attributes.get("gps_accuracy")),
            battery_level=battery_level,
            is_charging=is_charging,
            speed_mps=_coerce_float(attributes.get("speed")),
            raw_payload=raw_payload or state,
        )


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return bool(value)


def _lookup_related_battery_level(
    state_index: Mapping[str, dict[str, Any]],
    tracker_slug: str,
) -> int | None:
    sensor_state = state_index.get(f"sensor.{tracker_slug}_battery_level")
    if not sensor_state:
        return None
    return _coerce_int(sensor_state.get("state"))


def _lookup_related_charging_state(
    state_index: Mapping[str, dict[str, Any]],
    tracker_slug: str,
) -> bool | None:
    battery_state = state_index.get(f"sensor.{tracker_slug}_battery_state")
    if battery_state:
        state_value = str(battery_state.get("state", "")).strip().lower()
        if state_value in {"charging", "full"}:
            return True
        if state_value in {"discharging", "not_charging", "not charging"}:
            return False

    charger_type = state_index.get(f"sensor.{tracker_slug}_charger_type")
    if charger_type:
        state_value = str(charger_type.get("state", "")).strip().lower()
        if state_value in {"none", "unknown", "unavailable"}:
            return False
        if state_value:
            return True

    return None
