from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.repositories.location_repository import LocationRepository


class RetentionService:
    def __init__(self, repository: LocationRepository) -> None:
        self.repository = repository

    def prune(self, retention_days: int, now: datetime | None = None) -> dict[str, int]:
        now = now or datetime.now(UTC)
        cutoff = now - timedelta(days=retention_days)

        counts = {
            "location_points": self.repository.delete_location_points_older_than(cutoff),
            "safety_events": self.repository.delete_safety_events_older_than(cutoff),
            "daily_summaries": self.repository.delete_daily_summaries_older_than(cutoff),
            "trips": self.repository.delete_trips_older_than(cutoff),
        }
        self.repository.commit()
        return counts
