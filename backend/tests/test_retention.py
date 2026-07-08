from datetime import UTC, datetime

from app.services.retention import RetentionService


class FakeRetentionRepository:
    def __init__(self) -> None:
        self.cutoffs = {}
        self.committed = False

    def delete_location_points_older_than(self, cutoff: datetime) -> int:
        self.cutoffs["location_points"] = cutoff
        return 3

    def delete_safety_events_older_than(self, cutoff: datetime) -> int:
        self.cutoffs["safety_events"] = cutoff
        return 1

    def delete_daily_summaries_older_than(self, cutoff: datetime) -> int:
        self.cutoffs["daily_summaries"] = cutoff
        return 2

    def delete_trips_older_than(self, cutoff: datetime) -> int:
        self.cutoffs["trips"] = cutoff
        return 4

    def commit(self) -> None:
        self.committed = True


def test_retention_prunes_all_retained_data_classes() -> None:
    repository = FakeRetentionRepository()
    service = RetentionService(repository)
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)

    results = service.prune(retention_days=7, now=now)

    expected_cutoff = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    assert results == {
        "location_points": 3,
        "safety_events": 1,
        "daily_summaries": 2,
        "trips": 4,
    }
    assert repository.cutoffs["location_points"] == expected_cutoff
    assert repository.cutoffs["safety_events"] == expected_cutoff
    assert repository.cutoffs["daily_summaries"] == expected_cutoff
    assert repository.cutoffs["trips"] == expected_cutoff
    assert repository.committed is True
