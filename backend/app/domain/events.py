from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ProviderName(StrEnum):
    HOME_ASSISTANT = "home_assistant"


@dataclass(slots=True)
class NormalizedLocationEvent:
    provider: ProviderName
    source_entity_id: str
    observed_at: datetime
    latitude: float
    longitude: float
    source_device_id: str | None = None
    source_device_name: str | None = None
    altitude_m: float | None = None
    accuracy_m: float | None = None
    battery_level: int | None = None
    is_charging: bool | None = None
    speed_mps: float | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
