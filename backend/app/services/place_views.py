from app.repositories.location_repository import LocationRepository


class PlaceViewService:
    def __init__(self, db) -> None:
        self.repository = LocationRepository(db)

    def list_places(self, family_slug: str) -> list[dict]:
        places = self.repository.list_places_for_family_slug(family_slug)
        return [_serialize_place(place) for place in places]

    def create_place(
        self,
        family_slug: str,
        *,
        name: str,
        place_type: str | None,
        latitude: float,
        longitude: float,
        radius_m: float,
        is_safe_zone: bool,
    ) -> dict | None:
        family = self.repository.get_family_by_slug(family_slug)
        if family is None:
            return None
        place = self.repository.create_place(
            family.id,
            name=name,
            place_type=place_type,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            is_safe_zone=is_safe_zone,
        )
        self.repository.commit()
        return _serialize_place(place)

    def update_place(
        self,
        family_slug: str,
        place_id,
        *,
        name: str,
        place_type: str | None,
        latitude: float,
        longitude: float,
        radius_m: float,
        is_safe_zone: bool,
    ) -> dict | None:
        place = self.repository.update_place_for_family_slug(
            family_slug,
            place_id,
            name=name,
            place_type=place_type,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            is_safe_zone=is_safe_zone,
        )
        if place is None:
            return None
        self.repository.commit()
        return _serialize_place(place)

    def delete_place(self, family_slug: str, place_id) -> bool:
        deleted = self.repository.delete_place_for_family_slug(family_slug, place_id)
        if not deleted:
            return False
        self.repository.commit()
        return True


def _serialize_place(place) -> dict:
    return {
        "id": place.id,
        "name": place.name,
        "place_type": place.place_type,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "radius_m": place.radius_m,
        "is_safe_zone": place.is_safe_zone,
    }
