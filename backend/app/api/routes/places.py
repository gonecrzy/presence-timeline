from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.auth import AppPrincipal, require_app_access
from app.core.database import get_db
from app.schemas.place import (
    PlaceListResponse,
    PlaceResponse,
    PlaceSearchListResponse,
    PlaceSearchResultResponse,
    PlaceUpsertRequest,
)
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


@router.get("/search")
def search_places(
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[PlaceViewService, Depends(get_place_view_service)],
    q: str = Query(..., min_length=2),
) -> PlaceSearchListResponse:
    return PlaceSearchListResponse(items=[PlaceSearchResultResponse.model_validate(item) for item in service.search_addresses(q)])


@router.post("")
def create_place(
    payload: PlaceUpsertRequest,
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[PlaceViewService, Depends(get_place_view_service)],
) -> PlaceResponse:
    place = service.create_place(
        principal.family_slug,
        name=payload.name,
        place_type=payload.place_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_m=payload.radius_m,
        is_safe_zone=payload.is_safe_zone,
    )
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found.")
    return PlaceResponse.model_validate(place)


@router.patch("/{place_id}")
def update_place(
    place_id: UUID,
    payload: PlaceUpsertRequest,
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[PlaceViewService, Depends(get_place_view_service)],
) -> PlaceResponse:
    place = service.update_place(
        principal.family_slug,
        place_id,
        name=payload.name,
        place_type=payload.place_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_m=payload.radius_m,
        is_safe_zone=payload.is_safe_zone,
    )
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found.")
    return PlaceResponse.model_validate(place)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place(
    place_id: UUID,
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[PlaceViewService, Depends(get_place_view_service)],
) -> Response:
    deleted = service.delete_place(principal.family_slug, place_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
