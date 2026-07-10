import asyncio
from collections.abc import AsyncIterator
import json
from typing import Any
from urllib import request

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
        self._state_index: dict[str, dict[str, Any]] = {}

    async def snapshot(self) -> list[NormalizedLocationEvent]:
        return await asyncio.to_thread(self._fetch_snapshot)

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
            new_state = payload.get("event", {}).get("data", {}).get("new_state")
            if isinstance(new_state, dict):
                entity_id = new_state.get("entity_id")
                if entity_id:
                    self._state_index[entity_id] = new_state
            normalized = self.normalizer.normalize(payload, state_index=self._state_index)
            if normalized is not None:
                yield normalized

    def _fetch_snapshot(self) -> list[NormalizedLocationEvent]:
        req = request.Request(
            self._states_url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=20) as response:
            states = json.load(response)

        self._state_index = {
            state["entity_id"]: state
            for state in states
            if isinstance(state, dict) and state.get("entity_id")
        }
        events = []
        for state in states:
            normalized = self.normalizer.normalize_state(state, state_index=self._state_index)
            if normalized is not None:
                events.append(normalized)
        return events

    @property
    def _states_url(self) -> str:
        base_url = self.ws_url.replace("wss://", "https://").replace("ws://", "http://")
        if base_url.endswith("/api/websocket"):
            base_url = base_url[: -len("/api/websocket")]
        return f"{base_url.rstrip('/')}/api/states"
