from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceResponse(BaseModel):
    id: UUID
    provider: str
    external_id: str
    label: str | None = None
    ignored: bool
    last_seen_at: datetime | None = None


class MemberResponse(BaseModel):
    id: UUID
    display_name: str
    is_child: bool
    last_seen_at: datetime | None = None
    devices: list[DeviceResponse] = Field(default_factory=list)


class DeviceUpdateRequest(BaseModel):
    label: str | None = None
    ignored: bool | None = None


class MemberUpdateRequest(BaseModel):
    display_name: str | None = None
    is_child: bool | None = None
    avatar_color: str | None = None


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
