from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimelineItemResponse(BaseModel):
    kind: str
    observed_at: datetime
    trip_id: UUID | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    battery_level: int | None = None
    source_entity_id: str | None = None
    distance_m: float | None = None
    point_count: int | None = None
    start_label: str | None = None
    end_label: str | None = None
    event_type: str | None = None
    severity: str | None = None
    place_id: UUID | None = None
    payload: dict | None = None


class TimelineResponse(BaseModel):
    items: list[TimelineItemResponse]
