from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LocationPointResponse(BaseModel):
    member_id: UUID
    observed_at: datetime
    latitude: float
    longitude: float
    accuracy_m: float | None = None
    battery_level: int | None = None
    source_entity_id: str | None = None


class LocationHistoryResponse(BaseModel):
    items: list[LocationPointResponse]


class StopResponse(BaseModel):
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    latitude: float
    longitude: float
    point_count: int
    place_id: UUID | None = None
    place_name: str | None = None
    address: str | None = None
    label: str | None = None


class StopListResponse(BaseModel):
    items: list[StopResponse]
