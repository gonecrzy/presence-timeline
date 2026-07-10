from datetime import timezone

from app.domain.events import ProviderName
from app.providers.home_assistant.normalizer import HomeAssistantEventNormalizer


def test_normalizer_extracts_location_from_state_change() -> None:
    payload = {
        "event": {
            "event_type": "state_changed",
            "time_fired": "2026-07-08T21:00:00Z",
            "data": {
                "new_state": {
                    "entity_id": "device_tracker.pixel_8",
                    "last_updated": "2026-07-08T20:59:40Z",
                    "attributes": {
                        "friendly_name": "Sam Phone",
                        "latitude": 37.4219999,
                        "longitude": -122.0840575,
                        "gps_accuracy": 12,
                        "battery_level": 76,
                        "battery_charging": True,
                        "source_type": "gps",
                        "speed": 0.4,
                    },
                }
            },
        }
    }

    event = HomeAssistantEventNormalizer().normalize(payload)

    assert event is not None
    assert event.provider == ProviderName.HOME_ASSISTANT
    assert event.source_entity_id == "device_tracker.pixel_8"
    assert event.source_device_name == "Sam Phone"
    assert event.latitude == 37.4219999
    assert event.longitude == -122.0840575
    assert event.accuracy_m == 12.0
    assert event.battery_level == 76
    assert event.is_charging is True
    assert event.observed_at.tzinfo == timezone.utc


def test_normalizer_ignores_non_tracker_events() -> None:
    payload = {
        "event": {
            "event_type": "state_changed",
            "data": {
                "new_state": {
                    "entity_id": "sensor.kitchen_temperature",
                    "attributes": {"state_class": "measurement"},
                }
            },
        }
    }

    assert HomeAssistantEventNormalizer().normalize(payload) is None


def test_normalizer_extracts_location_from_state_snapshot() -> None:
    state = {
        "entity_id": "device_tracker.pixel_10_pro",
        "last_updated": "2026-07-08T20:59:40Z",
        "attributes": {
            "friendly_name": "Kristi",
            "latitude": 37.4219999,
            "longitude": -122.0840575,
            "gps_accuracy": 12,
            "battery_level": 76,
            "battery_charging": True,
            "speed": 0.4,
        },
    }

    event = HomeAssistantEventNormalizer().normalize_state(state)

    assert event is not None
    assert event.provider == ProviderName.HOME_ASSISTANT
    assert event.source_entity_id == "device_tracker.pixel_10_pro"
    assert event.source_device_name == "Kristi"
    assert event.observed_at.tzinfo == timezone.utc


def test_normalizer_enriches_tracker_state_from_related_battery_sensors() -> None:
    state = {
        "entity_id": "device_tracker.rileyphone",
        "last_updated": "2026-07-08T20:59:40Z",
        "attributes": {
            "friendly_name": "RileyPhone",
            "latitude": 37.4219999,
            "longitude": -122.0840575,
            "gps_accuracy": 12,
        },
    }
    state_index = {
        "sensor.rileyphone_battery_level": {
            "entity_id": "sensor.rileyphone_battery_level",
            "state": "21",
            "attributes": {
                "friendly_name": "RileyPhone Battery level",
                "device_class": "battery",
                "unit_of_measurement": "%",
            },
        },
        "sensor.rileyphone_battery_state": {
            "entity_id": "sensor.rileyphone_battery_state",
            "state": "charging",
            "attributes": {
                "friendly_name": "RileyPhone Battery state",
            },
        },
    }

    event = HomeAssistantEventNormalizer().normalize_state(state, state_index=state_index)

    assert event is not None
    assert event.battery_level == 21
    assert event.is_charging is True
