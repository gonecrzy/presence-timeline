from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HomeAssistantMemberSummaryResponse(BaseModel):
    member_id: UUID
    display_name: str
    is_child: bool
    last_seen_at: datetime | None = None
    current_location_label: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    accuracy_m: float | None = None
    battery_level: int | None = None
    observed_at: datetime | None = None
    source_entity_id: str | None = None


class HomeAssistantSummaryListResponse(BaseModel):
    items: list[HomeAssistantMemberSummaryResponse]
