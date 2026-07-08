from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


from app.schemas.location import LocationPointResponse


class TripResponse(BaseModel):
    id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    point_count: int
    distance_m: float
    start_label: str | None = None
    end_label: str | None = None


class TripListResponse(BaseModel):
    items: list[TripResponse]


class DailySummaryResponse(BaseModel):
    summary_date: date
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    trip_count: int
    total_distance_m: float


class TripRouteResponse(BaseModel):
    id: UUID
    member_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    distance_m: float
    point_count: int
    points: list[LocationPointResponse]
