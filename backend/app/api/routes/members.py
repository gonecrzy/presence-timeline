from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AppPrincipal, require_app_access
from app.core.database import get_db
from app.schemas.location import LocationHistoryResponse, LocationPointResponse
from app.schemas.member import DeviceResponse, DeviceUpdateRequest, MemberListResponse, MemberResponse, MemberUpdateRequest
from app.schemas.safety import SafetyEventListResponse
from app.schemas.timeline import TimelineItemResponse, TimelineResponse
from app.schemas.trip import DailySummaryResponse, TripListResponse, TripRouteResponse
from app.services.member_views import MemberViewService
from app.services.safety_views import SafetyViewService
from app.services.trip_views import TripViewService

router = APIRouter()


def get_member_view_service(db=Depends(get_db)) -> MemberViewService:
    return MemberViewService(db)


def get_trip_view_service(db=Depends(get_db)) -> TripViewService:
    return TripViewService(db)


def get_safety_view_service(db=Depends(get_db)) -> SafetyViewService:
    return SafetyViewService(db)


@router.get("")
def list_members(
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
) -> MemberListResponse:
    return MemberListResponse(items=service.list_members(principal.family_slug))


@router.patch("/{member_id}")
def update_member(
    member_id: UUID,
    payload: MemberUpdateRequest,
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
) -> MemberResponse:
    member = service.update_member(
        principal.family_slug,
        member_id,
        display_name=payload.display_name,
        is_child=payload.is_child,
        avatar_color=payload.avatar_color,
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    return MemberResponse.model_validate(member)


@router.patch("/{member_id}/devices/{device_id}")
def update_member_device(
    member_id: UUID,
    device_id: UUID,
    payload: DeviceUpdateRequest,
    *,
    principal: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
) -> DeviceResponse:
    device = service.update_device(
        principal.family_slug,
        member_id,
        device_id,
        label=payload.label,
        ignored=payload.ignored,
    )
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member device not found.")
    return DeviceResponse.model_validate(device)


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


@router.get("/{member_id}/timeline")
def get_member_timeline(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[MemberViewService, Depends(get_member_view_service)],
    start: datetime = Query(...),
    end: datetime = Query(...),
) -> TimelineResponse:
    items = service.timeline(member_id, start, end)
    return TimelineResponse(items=[TimelineItemResponse.model_validate(item) for item in items])


@router.get("/{member_id}/trips")
def get_member_trips(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[TripViewService, Depends(get_trip_view_service)],
    date: date = Query(...),
) -> TripListResponse:
    return TripListResponse(items=service.trips(member_id, date))


@router.get("/{member_id}/trips/{trip_id}/route")
def get_member_trip_route(
    member_id: UUID,
    trip_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[TripViewService, Depends(get_trip_view_service)],
) -> TripRouteResponse:
    route = service.trip_route(member_id, trip_id)
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip route not found.")
    return TripRouteResponse.model_validate(route)


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


@router.get("/{member_id}/safety-events")
def get_member_safety_events(
    member_id: UUID,
    *,
    _: Annotated[AppPrincipal, Depends(require_app_access)],
    service: Annotated[SafetyViewService, Depends(get_safety_view_service)],
    start: datetime = Query(...),
    end: datetime = Query(...),
) -> SafetyEventListResponse:
    return SafetyEventListResponse(items=service.events(member_id, start, end))
