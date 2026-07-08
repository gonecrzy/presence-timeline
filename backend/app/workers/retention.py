from __future__ import annotations

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.repositories.location_repository import LocationRepository
from app.services.retention import RetentionService


def run_once() -> dict[str, int]:
    settings = get_settings()
    db = SessionLocal()
    try:
        repository = LocationRepository(db)
        return RetentionService(repository).prune(settings.retention_days)
    finally:
        db.close()


def main() -> None:
    results = run_once()
    print(results)


if __name__ == "__main__":
    main()
