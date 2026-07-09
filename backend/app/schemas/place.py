from uuid import UUID

from pydantic import BaseModel


class PlaceResponse(BaseModel):
    id: UUID
    name: str
    place_type: str | None = None
    latitude: float
    longitude: float
    radius_m: float
    is_safe_zone: bool


class PlaceListResponse(BaseModel):
    items: list[PlaceResponse]


class PlaceSearchResultResponse(BaseModel):
    label: str
    latitude: float
    longitude: float


class PlaceSearchListResponse(BaseModel):
    items: list[PlaceSearchResultResponse]


class PlaceUpsertRequest(BaseModel):
    name: str
    place_type: str | None = None
    latitude: float
    longitude: float
    radius_m: float
    is_safe_zone: bool
