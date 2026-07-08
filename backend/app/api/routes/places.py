from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import AppPrincipal, require_app_access
from app.core.database import get_db
from app.schemas.place import PlaceListResponse
from app.services.place_views import PlaceViewService

router = APIRouter()


def get_place_view_service(db=Depends(get_db)) -> PlaceViewService:
    return PlaceViewService(db)


@router.get("")
def list_places(
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[PlaceViewService, Depends(get_place_view_service)],
) -> PlaceListResponse:
    return PlaceListResponse(items=service.list_places(principal.family_slug))
