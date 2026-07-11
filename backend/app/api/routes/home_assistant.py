from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AppPrincipal, require_app_access
from app.core.database import get_db
from app.schemas.home_assistant import (
    HomeAssistantMemberPanelResponse,
    HomeAssistantMemberSummaryResponse,
    HomeAssistantSummaryListResponse,
)
from app.services.home_assistant_views import HomeAssistantViewService

router = APIRouter()


def get_home_assistant_view_service(db=Depends(get_db)) -> HomeAssistantViewService:
    return HomeAssistantViewService(db)


@router.get("/summary")
def get_summary(
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[HomeAssistantViewService, Depends(get_home_assistant_view_service)],
) -> HomeAssistantSummaryListResponse:
    return HomeAssistantSummaryListResponse(
        items=[
            HomeAssistantMemberSummaryResponse.model_validate(item)
            for item in service.summary(principal.family_slug)
        ]
    )


@router.get("/members/{member_id}/panel")
def get_member_panel(
    member_id: UUID,
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[HomeAssistantViewService, Depends(get_home_assistant_view_service)],
    start: datetime = Query(...),
    end: datetime = Query(...),
) -> HomeAssistantMemberPanelResponse:
    panel = service.member_panel(principal.family_slug, member_id, start, end)
    if panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    return HomeAssistantMemberPanelResponse.model_validate(panel)
