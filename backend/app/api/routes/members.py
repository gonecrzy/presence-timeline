from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AppPrincipal, require_app_access
from app.core.database import get_db
from app.schemas.location import LocationHistoryResponse, LocationPointResponse
from app.schemas.member import MemberListResponse
from app.schemas.trip import DailySummaryResponse, TripListResponse
from app.services.member_views import MemberViewService
from app.services.trip_views import TripViewService

router = APIRouter()


def get_member_view_service(db=Depends(get_db)) -> MemberViewService:
    return MemberViewService(db)


def get_trip_view_service(db=Depends(get_db)) -> TripViewService:
    return TripViewService(db)


@router.get("")
def list_members(
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
) -> MemberListResponse:
    return MemberListResponse(items=service.list_members(principal.family_slug))


@router.get("/{member_id}/latest-location")
def get_latest_location(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
) -> LocationPointResponse:
    point = service.latest_location(member_id)
    if point is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member location not found.")
    return LocationPointResponse.model_validate(point)


@router.get("/{member_id}/history")
def get_member_history(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
    start: datetime = Query(...),
    end: datetime = Query(...),
) -> LocationHistoryResponse:
    points = service.history(member_id, start, end)
    return LocationHistoryResponse(
        items=[LocationPointResponse.model_validate(point) for point in points],
    )


@router.get("/{member_id}/trips")
def get_member_trips(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[TripViewService, Depends(get_trip_view_service)],
    date: date = Query(...),
) -> TripListResponse:
    return TripListResponse(items=service.trips(member_id, date))


@router.get("/{member_id}/daily-summary")
def get_member_daily_summary(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[TripViewService, Depends(get_trip_view_service)],
    date: date = Query(...),
) -> DailySummaryResponse:
    summary = service.daily_summary(member_id, date)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Daily summary not found.")
    return DailySummaryResponse.model_validate(summary)
