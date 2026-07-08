from datetime import timezone

import pytest

from app.providers.home_assistant.client import HomeAssistantWebSocketProvider


class FakeConnection:
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        self.sent = []
        self.closed = False

    async def recv(self) -> str:
        return self.messages.pop(0)

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def close(self) -> None:
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)


@pytest.mark.anyio
async def test_provider_authenticates_and_subscribes(monkeypatch) -> None:
    connection = FakeConnection(
        [
            '{"type":"auth_required","ha_version":"2026.7.0"}',
            '{"type":"auth_ok","ha_version":"2026.7.0"}',
            '{"id":1,"type":"result","success":true,"result":null}',
        ]
    )

    async def fake_connect(url: str):
        assert url == "wss://ha.example.com/api/websocket"
        return connection

    monkeypatch.setattr("app.providers.home_assistant.client.websockets.connect", fake_connect)

    provider = HomeAssistantWebSocketProvider(
        ws_url="wss://ha.example.com/api/websocket",
        access_token="secret",
    )
    await provider.connect()
    await provider.close()

    assert connection.closed is True
    assert '"type": "auth"' in connection.sent[0]
    assert '"type": "subscribe_events"' in connection.sent[1]


@pytest.mark.anyio
async def test_provider_listen_yields_normalized_state_changed_events(monkeypatch) -> None:
    connection = FakeConnection(
        [
            '{"type":"auth_required","ha_version":"2026.7.0"}',
            '{"type":"auth_ok","ha_version":"2026.7.0"}',
            '{"id":1,"type":"result","success":true,"result":null}',
            '{"id":1,"type":"event","event":{"event_type":"state_changed","time_fired":"2026-07-09T00:00:05Z","data":{"new_state":{"entity_id":"device_tracker.sam_phone","last_updated":"2026-07-09T00:00:00Z","attributes":{"friendly_name":"Sam Phone","latitude":37.42,"longitude":-122.08,"gps_accuracy":9}}}}}',
        ]
    )

    async def fake_connect(url: str):
        return connection

    monkeypatch.setattr("app.providers.home_assistant.client.websockets.connect", fake_connect)

    provider = HomeAssistantWebSocketProvider(
        ws_url="wss://ha.example.com/api/websocket",
        access_token="secret",
    )

    events = []
    async for event in provider.listen():
        events.append(event)

    assert len(events) == 1
    assert events[0].source_entity_id == "device_tracker.sam_phone"
    assert events[0].observed_at.tzinfo == timezone.utc
