from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest

from app.domain.events import NormalizedLocationEvent, ProviderName
from app.services.ingestion import HomeAssistantIngestionRunner


class FakeProvider:
    def __init__(self) -> None:
        self.connected = False
        self.closed = False

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.closed = True

    async def listen(self) -> AsyncIterator[NormalizedLocationEvent]:
        yield NormalizedLocationEvent(
            provider=ProviderName.HOME_ASSISTANT,
            source_entity_id="device_tracker.sam_phone",
            observed_at=datetime(2026, 7, 9, 0, 0, tzinfo=UTC),
            latitude=37.42,
            longitude=-122.08,
        )


class FakeLocationService:
    def __init__(self) -> None:
        self.events = []

    def ingest(self, event: NormalizedLocationEvent) -> None:
        self.events.append(event)


class CallbackRecorder:
    def __init__(self) -> None:
        self.connected_calls = 0
        self.events = []

    def on_connected(self) -> None:
        self.connected_calls += 1

    def on_event(self, event: NormalizedLocationEvent) -> None:
        self.events.append(event)


@pytest.mark.anyio
async def test_ingestion_runner_processes_provider_events() -> None:
    provider = FakeProvider()
    location_service = FakeLocationService()

    processed = await HomeAssistantIngestionRunner(provider, location_service).run(max_events=1)

    assert processed == 1
    assert provider.connected is True
    assert provider.closed is True
    assert location_service.events[0].source_entity_id == "device_tracker.sam_phone"


@pytest.mark.anyio
async def test_ingestion_runner_emits_connected_and_event_callbacks() -> None:
    provider = FakeProvider()
    location_service = FakeLocationService()
    recorder = CallbackRecorder()

    processed = await HomeAssistantIngestionRunner(
        provider,
        location_service,
        on_connected=recorder.on_connected,
        on_event=recorder.on_event,
    ).run(max_events=1)

    assert processed == 1
    assert recorder.connected_calls == 1
    assert [event.source_entity_id for event in recorder.events] == ["device_tracker.sam_phone"]
