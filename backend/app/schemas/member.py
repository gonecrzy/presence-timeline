from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MemberResponse(BaseModel):
    id: UUID
    display_name: str
    is_child: bool
    last_seen_at: datetime | None = None


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
