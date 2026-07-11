from __future__ import annotations

import time

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.repositories.location_repository import LocationRepository
from app.services.reverse_geocode_cache import ReverseGeocodeCacheService


def run_once() -> dict[str, int]:
    settings = get_settings()
    if not settings.enable_reverse_geocoding:
        return {"queued": 0, "resolved": 0, "failed": 0}

    db = SessionLocal()
    try:
        repository = LocationRepository(db)
        service = ReverseGeocodeCacheService(repository)
        queued = service.backfill_recent_points(limit=settings.reverse_geocode_backfill_limit)
        results = service.resolve_pending(limit=settings.reverse_geocode_batch_size)
        return {"queued": queued, **results}
    finally:
        db.close()


def main() -> None:
    settings = get_settings()
    while True:
        results = run_once()
        print(results, flush=True)
        time.sleep(settings.reverse_geocode_worker_interval_seconds)


if __name__ == "__main__":
    main()
