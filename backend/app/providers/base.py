from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.domain.events import NormalizedLocationEvent


class LocationProvider(ABC):
    name: str

    @abstractmethod
    async def connect(self) -> None:
        """Open any provider-side resources."""

    @abstractmethod
    async def close(self) -> None:
        """Release provider-side resources."""

    @abstractmethod
    async def listen(self) -> AsyncIterator[NormalizedLocationEvent]:
        """Yield normalized location events."""
