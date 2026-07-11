from datetime import date, datetime, timedelta
from uuid import UUID

from app.repositories.location_repository import LocationRepository
from app.services.places import (
    PlaceMatcher,
    choose_address_granularity,
    format_reverse_geocode_label,
    format_reverse_geocode_place_name,
)
from app.services.reverse_geocode_cache import ReverseGeocodeCacheService
from app.services.safety import SafetyDerivationService
from app.services.stops import derive_stops
from app.services.trip_derivation import TripDerivationService


class MemberViewService:
    def __init__(self, db) -> None:
        self.repository = LocationRepository(db)
        self.trip_derivation = TripDerivationService(self.repository)
        self.safety_derivation = SafetyDerivationService()
        self.place_matcher = PlaceMatcher()
        self.reverse_geocode_cache = ReverseGeocodeCacheService(self.repository)

    def list_members(self, family_slug: str, *, resolve_addresses: bool = True) -> list[dict]:
        members = self.repository.list_members_for_family_slug(family_slug)
        return [
            {
                "id": member.id,
                "display_name": member.display_name,
                "is_child": member.is_child,
                "last_seen_at": member.last_seen_at,
                "current_location_label": self._current_location_label(
                    member,
                    resolve_addresses=resolve_addresses,
                ),
                "devices": [_serialize_device(device) for device in member.devices],
            }
            for member in members
            if not _is_presence_timeline_mirror_member(member)
        ]

    def set_device_ignored(self, member_id: UUID, device_id: UUID, ignored: bool) -> dict | None:
        device = self.repository.set_device_ignored(member_id, device_id, ignored)
        if device is None:
            return None
        self.repository.commit()
        return _serialize_device(device)

    def update_member(
        self,
        family_slug: str,
        member_id: UUID,
        *,
        display_name: str | None,
        is_child: bool | None,
        avatar_color: str | None,
    ) -> dict | None:
        member = self.repository.update_member_for_family_slug(
            family_slug,
            member_id,
            display_name=display_name,
            is_child=is_child,
            avatar_color=avatar_color,
        )
        if member is None:
            return None
        self.repository.commit()
        return _serialize_member(member)

    def update_device(
        self,
        family_slug: str,
        member_id: UUID,
        device_id: UUID,
        *,
        label: str | None,
        ignored: bool | None,
    ) -> dict | None:
        device = self.repository.update_device_for_family_slug(
            family_slug,
            member_id,
            device_id,
            label=label,
            ignored=ignored,
        )
        if device is None:
            return None
        self.repository.commit()
        return _serialize_device(device)

    def latest_location(self, member_id: UUID) -> dict | None:
        point = self.repository.get_latest_point_for_member(member_id)
        if point is None:
            return None
        return _serialize_point(point)

    def history(self, member_id: UUID, start: datetime, end: datetime) -> list[dict]:
        points = self.repository.list_member_history(member_id, start, end)
        return [_serialize_point(point) for point in points]

    def stops(
        self,
        member_id: UUID,
        start: datetime,
        end: datetime,
        *,
        dwell_radius_m: float = 250.0,
        minimum_duration: timedelta = timedelta(minutes=10),
        resolve_addresses: bool = True,
    ) -> list[dict]:
        member = self.repository.get_member(member_id)
        if member is None:
            return []

        points = self.repository.list_member_history(member_id, start, end)
        places = _serialize_places(self.repository.list_places_for_family_id(member.family_id))
        return _build_stop_items(
            points=points,
            places=places,
            place_matcher=self.place_matcher,
            reverse_geocode_cache=self.reverse_geocode_cache,
            dwell_radius_m=dwell_radius_m,
            minimum_duration=minimum_duration,
            resolve_addresses=resolve_addresses,
        )

    def timeline(
        self,
        member_id: UUID,
        start: datetime,
        end: datetime,
        *,
        resolve_addresses: bool = True,
    ) -> list[dict]:
        member = self.repository.get_member(member_id)
        if member is None:
            return []

        for target_date in _dates_in_range(start.date(), end.date()):
            self.trip_derivation.rebuild_member_day(member_id, target_date)

        points = self.repository.list_member_history(member_id, start, end)
        places = [
            {
                "id": place.id,
                "name": place.name,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "radius_m": place.radius_m,
                "is_safe_zone": place.is_safe_zone,
            }
            for place in self.repository.list_places_for_family_id(member.family_id)
        ]
        point_dicts = [
            {
                "member_id": point.member_id,
                "observed_at": point.observed_at,
                "latitude": point.latitude,
                "longitude": point.longitude,
            }
            for point in points
        ]
        self.repository.replace_safety_events_for_range(
            member_id,
            start,
            end,
            self.safety_derivation.derive(points=point_dicts, places=places),
        )
        self.repository.commit()

        items = []
        stop_items = _build_stop_items(
            points=points,
            places=places,
            place_matcher=self.place_matcher,
            reverse_geocode_cache=self.reverse_geocode_cache,
            dwell_radius_m=250.0,
            minimum_duration=timedelta(minutes=10),
            resolve_addresses=resolve_addresses,
        )
        for stop in stop_items:
            items.append(
                {
                    "kind": "location_stay",
                    "observed_at": stop["started_at"],
                    "started_at": stop["started_at"],
                    "ended_at": stop["ended_at"],
                    "duration_seconds": stop["duration_seconds"],
                    "latitude": stop["latitude"],
                    "longitude": stop["longitude"],
                    "point_count": stop["point_count"],
                    "place_id": stop["place_id"],
                    "label": stop["label"],
                    "is_current": stop["is_current"],
                }
            )
        for event in self.repository.list_safety_events_for_range(member_id, start, end):
            items.append(
                {
                    "kind": "safety_event",
                    "observed_at": event.observed_at,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "place_id": event.place_id,
                    "payload": event.payload,
                }
            )
        seen_trip_ids: set[UUID] = set()
        for trip in self.repository.list_trips_for_member_range(member_id, start, end):
            if trip.id in seen_trip_ids:
                continue
            seen_trip_ids.add(trip.id)
            items.append(
                {
                    "kind": "trip",
                    "observed_at": trip.started_at,
                    "trip_id": trip.id,
                    "started_at": trip.started_at,
                    "ended_at": trip.ended_at,
                    "distance_m": trip.distance_m,
                    "point_count": trip.point_count,
                    "start_label": trip.start_label,
                    "end_label": trip.end_label,
                }
            )

        return sorted(items, key=lambda item: item["observed_at"])

    def _current_location_label(self, member, *, resolve_addresses: bool = True) -> str | None:
        latest_point = self.repository.get_latest_point_for_member(member.id)
        if latest_point is None:
            return None

        history = self.repository.list_member_history(
            member.id,
            latest_point.observed_at - timedelta(days=1),
            latest_point.observed_at,
        )
        places = _serialize_places(self.repository.list_places_for_family_id(self.repository.get_member(member.id).family_id))
        stop_items = _build_stop_items(
            points=history,
            places=places,
            place_matcher=self.place_matcher,
            reverse_geocode_cache=self.reverse_geocode_cache,
            dwell_radius_m=250.0,
            minimum_duration=timedelta(minutes=10),
            resolve_addresses=resolve_addresses,
        )
        current_stop = next((stop for stop in reversed(stop_items) if stop["is_current"]), None)
        if current_stop is not None:
            return current_stop["label"]

        if not resolve_addresses:
            return _coordinate_label(latest_point.latitude, latest_point.longitude)

        granularity = choose_address_granularity(
            accuracy_m=latest_point.accuracy_m,
            duration_seconds=None,
            point_count=None,
            moving=True,
        )
        return self.reverse_geocode_cache.lookup_label(
            latest_point.latitude,
            latest_point.longitude,
            granularity=granularity,
        ) or _coordinate_label(latest_point.latitude, latest_point.longitude)


def _serialize_point(point) -> dict:
    return {
        "member_id": point.member_id,
        "observed_at": point.observed_at,
        "latitude": point.latitude,
        "longitude": point.longitude,
        "accuracy_m": point.accuracy_m,
        "battery_level": point.battery_level,
        "source_entity_id": point.source_entity_id,
    }


def _serialize_device(device) -> dict:
    return {
        "id": device.id,
        "provider": device.provider,
        "external_id": device.external_id,
        "label": device.label,
        "ignored": device.ignored,
        "last_seen_at": device.last_seen_at,
    }


def _serialize_member(member) -> dict:
    return {
        "id": member.id,
        "display_name": member.display_name,
        "is_child": member.is_child,
        "last_seen_at": member.last_seen_at,
        "devices": [_serialize_device(device) for device in member.devices],
    }


def _serialize_places(places) -> list[dict]:
    return [
        {
            "id": place.id,
            "name": place.name,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "radius_m": place.radius_m,
            "is_safe_zone": place.is_safe_zone,
        }
        for place in places
    ]


def _build_stop_items(
    *,
    points,
    places: list[dict],
    place_matcher: PlaceMatcher,
    reverse_geocode_cache: ReverseGeocodeCacheService,
    dwell_radius_m: float,
    minimum_duration: timedelta,
    resolve_addresses: bool,
) -> list[dict]:
    derived_stops = derive_stops(
        points,
        dwell_radius_m=dwell_radius_m,
        minimum_duration=minimum_duration,
    )
    latest_observed_at = points[-1].observed_at if points else None

    items = []
    for index, stop in enumerate(derived_stops):
        matched_place = place_matcher.match(places, stop.latitude, stop.longitude)
        place_name = matched_place["name"] if matched_place is not None else None
        representative_point = next(
            (point for point in reversed(points) if point.observed_at == stop.ended_at),
            None,
        )
        granularity = choose_address_granularity(
            accuracy_m=stop.accuracy_m if stop.accuracy_m is not None else representative_point.accuracy_m if representative_point is not None else None,
            duration_seconds=stop.duration_seconds,
            point_count=stop.point_count,
            moving=False,
        )
        payload = None
        address = None
        derived_place_name = None
        if place_name is None and resolve_addresses:
            payload = reverse_geocode_cache.lookup_payload(stop.latitude, stop.longitude)
            if payload is None:
                reverse_geocode_cache.queue_lookup(stop.latitude, stop.longitude)
            if payload is None and representative_point is not None:
                payload = reverse_geocode_cache.lookup_payload(
                    representative_point.latitude,
                    representative_point.longitude,
                )
            if payload is not None:
                derived_place_name = format_reverse_geocode_place_name(payload)
                address = format_reverse_geocode_label(payload, granularity=granularity) or payload.get("display_name")
            if address is None:
                address = reverse_geocode_cache.lookup_label(
                    stop.latitude,
                    stop.longitude,
                    granularity=granularity,
                )
            if address is None and representative_point is not None:
                address = reverse_geocode_cache.lookup_label(
                    representative_point.latitude,
                    representative_point.longitude,
                    granularity=granularity,
                )

        place_name = place_name or derived_place_name
        label = place_name or address or _coordinate_label(stop.latitude, stop.longitude)
        items.append(
            {
                "started_at": stop.started_at,
                "ended_at": stop.ended_at,
                "duration_seconds": stop.duration_seconds,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "point_count": stop.point_count,
                "place_id": matched_place["id"] if matched_place is not None else None,
                "place_name": place_name,
                "address": address,
                "label": label,
                "is_current": index == len(derived_stops) - 1 and stop.ended_at == latest_observed_at,
            }
        )

    return items


def _coordinate_label(latitude: float, longitude: float) -> str:
    return f"{latitude:.4f}, {longitude:.4f}"


def _is_presence_timeline_mirror_member(member) -> bool:
    display_name = str(getattr(member, "display_name", "") or "")
    devices = list(getattr(member, "devices", []) or [])
    if not display_name.endswith(" Location") or not devices:
        return False

    for device in devices:
        external_id = str(getattr(device, "external_id", "") or "")
        if not external_id.startswith("device_tracker."):
            return False
        slug = external_id.split(".", 1)[-1]
        if not slug.endswith("_location"):
            return False
    return True


def _dates_in_range(start_date: date, end_date: date) -> list[date]:
    current = start_date
    dates = []
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates
