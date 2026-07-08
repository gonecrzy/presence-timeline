import asyncio

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.providers.home_assistant import HomeAssistantWebSocketProvider
from app.repositories.location_repository import LocationRepository
from app.services.bootstrap import BootstrapService
from app.services.ingestion import HomeAssistantIngestionRunner
from app.services.locations import LocationService


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
    finally:
        db.close()

    while True:
        db = SessionLocal()
        try:
            repository = LocationRepository(db)
            runner = HomeAssistantIngestionRunner(
                provider,
                LocationService(
                    repository,
                    auto_discovery_family_slug=settings.open_auth_family_slug,
                    auto_discovery_family_name=settings.default_family_name,
                ),
            )
            await runner.run()
        finally:
            db.close()

        await asyncio.sleep(5)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
