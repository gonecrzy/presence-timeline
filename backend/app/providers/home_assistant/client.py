from collections.abc import AsyncIterator
import json

import websockets

from app.domain.events import NormalizedLocationEvent
from app.providers.base import LocationProvider
from app.providers.home_assistant.normalizer import HomeAssistantEventNormalizer


class HomeAssistantWebSocketProvider(LocationProvider):
    name = "home_assistant"

    def __init__(self, ws_url: str, access_token: str) -> None:
        self.ws_url = ws_url
        self.access_token = access_token
        self.normalizer = HomeAssistantEventNormalizer()
        self._connection = None

    async def connect(self) -> None:
        self._connection = await websockets.connect(self.ws_url)
        auth_required = json.loads(await self._connection.recv())
        if auth_required.get("type") != "auth_required":
            raise RuntimeError("Home Assistant websocket did not request authentication.")
        await self._connection.send(
            json.dumps({"type": "auth", "access_token": self.access_token}),
        )
        auth_result = json.loads(await self._connection.recv())
        if auth_result.get("type") != "auth_ok":
            raise RuntimeError(f"Home Assistant websocket auth failed: {auth_result}")
        await self._connection.send(json.dumps({"id": 1, "type": "subscribe_events", "event_type": "state_changed"}))
        subscribe_result = json.loads(await self._connection.recv())
        if not subscribe_result.get("success"):
            raise RuntimeError(f"Home Assistant websocket subscription failed: {subscribe_result}")

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def listen(self) -> AsyncIterator[NormalizedLocationEvent]:
        if self._connection is None:
            await self.connect()

        assert self._connection is not None
        async for message in self._connection:
            payload = json.loads(message)
            if payload.get("type") != "event":
                continue
            normalized = self.normalizer.normalize(payload)
            if normalized is not None:
                yield normalized
