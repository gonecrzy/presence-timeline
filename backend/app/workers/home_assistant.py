import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime

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
PROVIDER_NAME = "home_assistant"
STATE_CONNECTED = "connected"
STATE_DISABLED = "disabled"
STATE_RETRYING = "retrying"
STATE_STARTING = "starting"


def retry_delay_seconds(attempt: int) -> int:
    normalized_attempt = max(1, attempt)
    return min(RETRY_MAX_DELAY_SECONDS, RETRY_BASE_DELAY_SECONDS * (2 ** (normalized_attempt - 1)))


async def run_with_retry(
    operation,
    *,
    sleep=asyncio.sleep,
    logger=LOGGER,
    on_error=None,
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
        except Exception as err:
            consecutive_failures += 1
            delay = retry_delay_seconds(consecutive_failures)
            if on_error is not None:
                on_error(err, delay)
            logger.exception("Home Assistant ingestion cycle failed; retrying in %s seconds", delay)
            await sleep(delay)


async def run() -> None:
    settings = get_settings()
    if not settings.enable_home_assistant_ingestion:
        _persist_provider_status(
            state=STATE_DISABLED,
            retry_delay_seconds=None,
            last_error_at=None,
            last_error_message=None,
        )
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

    def persist_status(**kwargs) -> None:
        _persist_provider_status(**kwargs)

    async def cycle() -> None:
        db = SessionLocal()
        try:
            repository = LocationRepository(db)
            location_service = LocationService(
                repository,
                auto_discovery_family_slug=settings.open_auth_family_slug,
                auto_discovery_family_name=settings.default_family_name,
            )
            snapshot_completed_at = datetime.now(UTC)
            for event in await provider.snapshot():
                location_service.ingest(event)
            repository.upsert_provider_status(
                PROVIDER_NAME,
                state=STATE_STARTING,
                last_snapshot_at=snapshot_completed_at,
                last_error_at=None,
                last_error_message=None,
                retry_delay_seconds=None,
            )
            repository.commit()

            runner = HomeAssistantIngestionRunner(
                provider,
                location_service,
                on_connected=lambda: _mark_connected(repository),
                on_event=lambda event: _mark_event(repository),
            )
            await runner.run()
        finally:
            with suppress(Exception):
                await provider.close()
            db.close()

    await run_with_retry(
        cycle,
        on_error=lambda err, delay: persist_status(
            state=STATE_RETRYING,
            retry_delay_seconds=delay,
            last_error_at=datetime.now(UTC),
            last_error_message=str(err),
        ),
    )


def _mark_connected(repository: LocationRepository) -> None:
    repository.upsert_provider_status(
        PROVIDER_NAME,
        state=STATE_CONNECTED,
        last_connected_at=datetime.now(UTC),
        last_error_at=None,
        last_error_message=None,
        retry_delay_seconds=None,
    )
    repository.commit()


def _mark_event(repository: LocationRepository) -> None:
    repository.upsert_provider_status(
        PROVIDER_NAME,
        state=STATE_CONNECTED,
        last_event_at=datetime.now(UTC),
        last_error_at=None,
        last_error_message=None,
        retry_delay_seconds=None,
    )
    repository.commit()


def _persist_provider_status(
    *,
    state: str,
    retry_delay_seconds: int | None,
    last_error_at: datetime | None,
    last_error_message: str | None,
) -> None:
    db = SessionLocal()
    try:
        repository = LocationRepository(db)
        repository.upsert_provider_status(
            PROVIDER_NAME,
            state=state,
            last_error_at=last_error_at,
            last_error_message=last_error_message,
            retry_delay_seconds=retry_delay_seconds,
        )
        repository.commit()
    finally:
        db.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
