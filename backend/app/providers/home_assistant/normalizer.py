from datetime import datetime
from typing import Any

from app.domain.events import NormalizedLocationEvent, ProviderName


class HomeAssistantEventNormalizer:
    """Translate Home Assistant state events into provider-agnostic location events."""

    def normalize(self, payload: dict[str, Any]) -> NormalizedLocationEvent | None:
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
            },
            raw_payload=payload,
        )

    def normalize_state(
        self,
        state: dict[str, Any],
        *,
        raw_payload: dict[str, Any] | None = None,
    ) -> NormalizedLocationEvent | None:
        entity_id = state.get("entity_id", "")
        attributes = state.get("attributes") or {}

        if not entity_id.startswith("device_tracker."):
            return None

        latitude = attributes.get("latitude")
        longitude = attributes.get("longitude")
        if latitude is None or longitude is None:
            return None

        observed_at = state.get("last_updated")
        if not observed_at:
            return None

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
            battery_level=_coerce_int(attributes.get("battery_level")),
            is_charging=_coerce_bool(attributes.get("battery_charging")),
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
