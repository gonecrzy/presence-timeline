from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SafetyEventResponse(BaseModel):
    id: UUID
    event_type: str
    severity: str
    observed_at: datetime
    place_id: UUID | None = None
    payload: dict


class SafetyEventListResponse(BaseModel):
    items: list[SafetyEventResponse]
