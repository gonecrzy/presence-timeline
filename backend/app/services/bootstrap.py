from app.core.config import HomeAssistantBootstrapMember
from app.repositories.location_repository import LocationRepository


class BootstrapService:
    def __init__(self, repository: LocationRepository) -> None:
        self.repository = repository

    def seed_home_assistant_members(
        self,
        family_slug: str,
        family_name: str,
        members: list[HomeAssistantBootstrapMember],
    ) -> None:
        if not members:
            return

        family = self.repository.ensure_family(family_slug=family_slug, family_name=family_name)
        for configured_member in members:
            member = self.repository.ensure_member(
                family=family,
                display_name=configured_member.display_name,
                is_child=configured_member.is_child,
                avatar_color=configured_member.avatar_color,
            )
            self.repository.upsert_device_for_member(
                member=member,
                provider="home_assistant",
                external_id=configured_member.entity_id,
                label=configured_member.device_label or configured_member.display_name,
            )

        self.repository.commit()
