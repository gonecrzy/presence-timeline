from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import AppPrincipal, require_app_access
from app.core.database import get_db
from app.schemas.home_assistant import HomeAssistantMemberSummaryResponse, HomeAssistantSummaryListResponse
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
