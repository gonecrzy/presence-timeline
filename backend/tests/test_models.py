from app.models import Base
from app.models.location import LocationPoint


def test_metadata_contains_core_tables() -> None:
    table_names = set(Base.metadata.tables)

    assert {
        "families",
        "members",
        "devices",
        "location_points",
        "trips",
        "daily_summaries",
        "safety_events",
    }.issubset(table_names)


def test_location_points_use_postgis_geometry() -> None:
    geom_column = LocationPoint.__table__.c.geom

    assert geom_column.type.geometry_type == "POINT"
    assert geom_column.type.srid == 4326
