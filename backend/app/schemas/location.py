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
