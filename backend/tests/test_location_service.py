from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.events import NormalizedLocationEvent, ProviderName
from app.services.locations import LocationService


class FakeLocationRepository:
    def __init__(self) -> None:
        self.members = {}
        self.devices = {}
        self.points = []

    def resolve_member_by_source_entity(self, source_entity_id: str):
        return self.members.get(source_entity_id)

    def upsert_device_for_member(self, member, provider: str, external_id: str, label: str | None):
        device = {
            "member_id": member["id"],
            "provider": provider,
            "external_id": external_id,
            "label": label,
        }
        self.devices[external_id] = device
        return device

    def add_location_point(self, point):
        self.points.append(point)
        return point

    def list_member_history(self, member_id, start, end):
        return [
            point
            for point in self.points
            if point.member_id == member_id and start <= point.observed_at <= end
        ]

    def get_latest_point_for_member(self, member_id):
        matching = [point for point in self.points if point.member_id == member_id]
        if not matching:
            return None
        return sorted(matching, key=lambda item: item.observed_at, reverse=True)[0]


def test_ingest_location_event_persists_point_for_known_member() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}

    event = NormalizedLocationEvent(
        provider=ProviderName.HOME_ASSISTANT,
        source_entity_id="device_tracker.sam_phone",
        source_device_id="pixel-8",
        source_device_name="Sam Phone",
        observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
        latitude=37.42,
        longitude=-122.08,
        battery_level=81,
        raw_payload={"event": "x"},
    )

    service = LocationService(repository)
    stored = service.ingest(event, received_at=datetime(2026, 7, 8, 21, 0, 2, tzinfo=UTC))

    assert stored.member_id == member_id
    assert stored.provider == "home_assistant"
    assert stored.battery_level == 81
    assert repository.devices["pixel-8"]["label"] == "Sam Phone"


def test_ingest_location_event_ignores_unknown_member_mapping() -> None:
    repository = FakeLocationRepository()
    service = LocationService(repository)

    event = NormalizedLocationEvent(
        provider=ProviderName.HOME_ASSISTANT,
        source_entity_id="device_tracker.unknown_phone",
        source_device_id="unknown-device",
        source_device_name="Unknown",
        observed_at=datetime(2026, 7, 8, 21, 0, tzinfo=UTC),
        latitude=37.42,
        longitude=-122.08,
    )

    assert service.ingest(event) is None
    assert repository.points == []


def test_latest_and_history_views_are_ordered_by_observed_at() -> None:
    repository = FakeLocationRepository()
    member_id = uuid4()
    repository.members["device_tracker.sam_phone"] = {"id": member_id, "display_name": "Sam"}
    service = LocationService(repository)
    start = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)

    for minute in (0, 15, 45):
        service.ingest(
            NormalizedLocationEvent(
                provider=ProviderName.HOME_ASSISTANT,
                source_entity_id="device_tracker.sam_phone",
                observed_at=start + timedelta(minutes=minute),
                latitude=37.42 + minute / 1000,
                longitude=-122.08,
            ),
            received_at=start + timedelta(minutes=minute, seconds=2),
        )

    latest = service.get_latest_location(member_id)
    history = service.get_history(member_id, start, start + timedelta(hours=1))

    assert latest is not None
    assert latest.observed_at == start + timedelta(minutes=45)
    assert [point.observed_at for point in history] == [
        start,
        start + timedelta(minutes=15),
        start + timedelta(minutes=45),
    ]
