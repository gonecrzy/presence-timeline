from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.location import LocationPointResponse, StopResponse
from app.schemas.timeline import TimelineItemResponse


class HomeAssistantMemberSummaryResponse(BaseModel):
    member_id: UUID
    display_name: str
    is_child: bool
    last_seen_at: datetime | None = None
    current_location_label: str | None = None
    status: str = "unknown"
    status_detail: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    accuracy_m: float | None = None
    battery_level: int | None = None
    observed_at: datetime | None = None
    source_entity_id: str | None = None


class HomeAssistantSummaryListResponse(BaseModel):
    items: list[HomeAssistantMemberSummaryResponse]


class HomeAssistantMemberPanelResponse(BaseModel):
    member: HomeAssistantMemberSummaryResponse
    history: list[LocationPointResponse]
    timeline: list[TimelineItemResponse]
    stops: list[StopResponse]
