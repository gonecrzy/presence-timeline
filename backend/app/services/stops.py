from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Sequence

from app.services.places import haversine_m


@dataclass(frozen=True)
class DerivedStop:
    started_at: object
    ended_at: object
    latitude: float
    longitude: float
    point_count: int
    accuracy_m: float | None = None

    @property
    def duration_seconds(self) -> int:
        return int((self.ended_at - self.started_at).total_seconds())


def derive_stops(points: Sequence[object], *, dwell_radius_m: float, minimum_duration: timedelta) -> list[DerivedStop]:
    ordered_points = sorted(points, key=lambda point: point.observed_at)
    if len(ordered_points) < 2:
        return []

    stops: list[DerivedStop] = []
    current_segment = [ordered_points[0]]

    for point in ordered_points[1:]:
        if _belongs_to_segment(point, current_segment, dwell_radius_m):
            current_segment.append(point)
            continue
        _append_stop(stops, current_segment, minimum_duration)
        current_segment = [point]

    _append_stop(stops, current_segment, minimum_duration)
    return stops


def _append_stop(stops: list[DerivedStop], points: Sequence[object], minimum_duration: timedelta) -> None:
    started_at = points[0].observed_at
    ended_at = points[-1].observed_at
    if ended_at - started_at < minimum_duration:
        return

    latitude = sum(point.latitude for point in points) / len(points)
    longitude = sum(point.longitude for point in points) / len(points)
    accuracies = [point.accuracy_m for point in points if getattr(point, "accuracy_m", None) is not None]
    stops.append(
        DerivedStop(
            started_at=started_at,
            ended_at=ended_at,
            latitude=latitude,
            longitude=longitude,
            point_count=len(points),
            accuracy_m=min(accuracies) if accuracies else None,
        )
    )


def _belongs_to_segment(point: object, current_segment: Sequence[object], dwell_radius_m: float) -> bool:
    center_latitude = sum(item.latitude for item in current_segment) / len(current_segment)
    center_longitude = sum(item.longitude for item in current_segment) / len(current_segment)
    return haversine_m(point.latitude, point.longitude, center_latitude, center_longitude) <= dwell_radius_m
