from collections.abc import AsyncIterator

from app.domain.events import NormalizedLocationEvent
from app.providers.base import LocationProvider
from app.providers.home_assistant.normalizer import HomeAssistantEventNormalizer


class HomeAssistantWebSocketProvider(LocationProvider):
    name = "home_assistant"

    def __init__(self, ws_url: str, access_token: str) -> None:
        self.ws_url = ws_url
        self.access_token = access_token
        self.normalizer = HomeAssistantEventNormalizer()

    async def connect(self) -> None:
        """Placeholder for the future websocket handshake."""

    async def close(self) -> None:
        """Placeholder for connection teardown."""

    async def listen(self) -> AsyncIterator[NormalizedLocationEvent]:
        raise NotImplementedError("WebSocket streaming is part of the next milestone.")
