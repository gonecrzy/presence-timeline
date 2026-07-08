from app.repositories.location_repository import LocationRepository


class PlaceViewService:
    def __init__(self, db) -> None:
        self.repository = LocationRepository(db)

    def list_places(self, family_slug: str) -> list[dict]:
        places = self.repository.list_places_for_family_slug(family_slug)
        return [
            {
                "id": place.id,
                "name": place.name,
                "place_type": place.place_type,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "radius_m": place.radius_m,
                "is_safe_zone": place.is_safe_zone,
            }
            for place in places
        ]
