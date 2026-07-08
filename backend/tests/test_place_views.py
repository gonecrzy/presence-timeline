from types import SimpleNamespace
from uuid import uuid4

from app.services.place_views import PlaceViewService


class FakePlaceRepository:
    def __init__(self) -> None:
        self.committed = False
        self.family = SimpleNamespace(id=uuid4(), slug="family-alpha")
        self.place = SimpleNamespace(
            id=uuid4(),
            name="School",
            place_type="school",
            latitude=37.4210,
            longitude=-122.0840,
            radius_m=200.0,
            is_safe_zone=True,
        )

    def get_family_by_slug(self, family_slug: str):
        assert family_slug == "family-alpha"
        return self.family

    def create_place(
        self,
        family_id,
        *,
        name,
        place_type,
        latitude,
        longitude,
        radius_m,
        is_safe_zone,
    ):
        assert family_id == self.family.id
        assert name == "Home"
        assert place_type == "home"
        assert latitude == 37.42
        assert longitude == -122.08
        assert radius_m == 150.0
        assert is_safe_zone is True
        self.place = SimpleNamespace(
            id=uuid4(),
            name=name,
            place_type=place_type,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            is_safe_zone=is_safe_zone,
        )
        return self.place

    def update_place_for_family_slug(
        self,
        family_slug: str,
        place_id,
        *,
        name,
        place_type,
        latitude,
        longitude,
        radius_m,
        is_safe_zone,
    ):
        assert family_slug == "family-alpha"
        assert place_id == self.place.id
        assert name == "School West"
        assert place_type == "school"
        assert latitude == 37.422
        assert longitude == -122.085
        assert radius_m == 225.0
        assert is_safe_zone is False
        self.place.name = name
        self.place.place_type = place_type
        self.place.latitude = latitude
        self.place.longitude = longitude
        self.place.radius_m = radius_m
        self.place.is_safe_zone = is_safe_zone
        return self.place

    def delete_place_for_family_slug(self, family_slug: str, place_id) -> bool:
        assert family_slug == "family-alpha"
        assert place_id == self.place.id
        return True

    def commit(self) -> None:
        self.committed = True


def test_place_view_service_creates_place(monkeypatch) -> None:
    repository = FakePlaceRepository()
    monkeypatch.setattr("app.services.place_views.LocationRepository", lambda db: repository)

    service = PlaceViewService(db=None)
    created = service.create_place(
        "family-alpha",
        name="Home",
        place_type="home",
        latitude=37.42,
        longitude=-122.08,
        radius_m=150.0,
        is_safe_zone=True,
    )

    assert created is not None
    assert created["name"] == "Home"
    assert created["is_safe_zone"] is True
    assert repository.committed is True


def test_place_view_service_updates_place(monkeypatch) -> None:
    repository = FakePlaceRepository()
    monkeypatch.setattr("app.services.place_views.LocationRepository", lambda db: repository)

    service = PlaceViewService(db=None)
    updated = service.update_place(
        "family-alpha",
        repository.place.id,
        name="School West",
        place_type="school",
        latitude=37.422,
        longitude=-122.085,
        radius_m=225.0,
        is_safe_zone=False,
    )

    assert updated is not None
    assert updated["name"] == "School West"
    assert updated["is_safe_zone"] is False
    assert repository.committed is True


def test_place_view_service_deletes_place(monkeypatch) -> None:
    repository = FakePlaceRepository()
    monkeypatch.setattr("app.services.place_views.LocationRepository", lambda db: repository)

    service = PlaceViewService(db=None)

    assert service.delete_place("family-alpha", repository.place.id) is True
    assert repository.committed is True
