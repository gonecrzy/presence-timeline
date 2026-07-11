import asyncio
import logging
from contextlib import suppress

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.providers.home_assistant import HomeAssistantWebSocketProvider
from app.repositories.location_repository import LocationRepository
from app.services.bootstrap import BootstrapService
from app.services.ingestion import HomeAssistantIngestionRunner
from app.services.locations import LocationService

LOGGER = logging.getLogger(__name__)
RETRY_BASE_DELAY_SECONDS = 5
RETRY_MAX_DELAY_SECONDS = 300
RESTART_DELAY_SECONDS = 5


def retry_delay_seconds(attempt: int) -> int:
    normalized_attempt = max(1, attempt)
    return min(RETRY_MAX_DELAY_SECONDS, RETRY_BASE_DELAY_SECONDS * (2 ** (normalized_attempt - 1)))


async def run_with_retry(
    operation,
    *,
    sleep=asyncio.sleep,
    logger=LOGGER,
    stop_after_success: bool = False,
) -> None:
    consecutive_failures = 0

    while True:
        try:
            await operation()
            consecutive_failures = 0
            if stop_after_success:
                return
            await sleep(RESTART_DELAY_SECONDS)
        except Exception:
            consecutive_failures += 1
            delay = retry_delay_seconds(consecutive_failures)
            logger.exception("Home Assistant ingestion cycle failed; retrying in %s seconds", delay)
            await sleep(delay)


async def run() -> None:
    settings = get_settings()
    if not settings.enable_home_assistant_ingestion:
        return

    db = SessionLocal()
    try:
        repository = LocationRepository(db)
        BootstrapService(repository).seed_home_assistant_members(
            family_slug=settings.open_auth_family_slug,
            family_name=settings.default_family_name,
            members=settings.home_assistant_bootstrap_members,
        )
    finally:
        db.close()

    provider = HomeAssistantWebSocketProvider(
        ws_url=settings.home_assistant_ws_url,
        access_token=settings.home_assistant_access_token,
    )

    async def cycle() -> None:
        db = SessionLocal()
        try:
            repository = LocationRepository(db)
            location_service = LocationService(
                repository,
                auto_discovery_family_slug=settings.open_auth_family_slug,
                auto_discovery_family_name=settings.default_family_name,
            )
            for event in await provider.snapshot():
                location_service.ingest(event)
            runner = HomeAssistantIngestionRunner(provider, location_service)
            await runner.run()
        finally:
            with suppress(Exception):
                await provider.close()
            db.close()

    await run_with_retry(cycle)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
