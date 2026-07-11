from app.domain.events import NormalizedLocationEvent
from app.providers.base import LocationProvider
from app.services.locations import LocationService


class HomeAssistantIngestionRunner:
    def __init__(
        self,
        provider: LocationProvider,
        location_service: LocationService,
        *,
        on_connected=None,
        on_event=None,
    ) -> None:
        self.provider = provider
        self.location_service = location_service
        self.on_connected = on_connected
        self.on_event = on_event

    async def run(self, max_events: int | None = None) -> int:
        processed = 0
        await self.provider.connect()
        if self.on_connected is not None:
            self.on_connected()
        try:
            async for event in self.provider.listen():
                self._handle_event(event)
                if self.on_event is not None:
                    self.on_event(event)
                processed += 1
                if max_events is not None and processed >= max_events:
                    break
        finally:
            await self.provider.close()

        return processed

    def _handle_event(self, event: NormalizedLocationEvent) -> None:
        self.location_service.ingest(event)
