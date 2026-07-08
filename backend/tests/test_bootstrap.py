from app.core.config import HomeAssistantBootstrapMember
from app.services.bootstrap import BootstrapService


class FakeBootstrapRepository:
    def __init__(self) -> None:
        self.family = None
        self.members = {}
        self.devices = {}
        self.committed = False

    def ensure_family(self, family_slug: str, family_name: str):
        self.family = {"slug": family_slug, "name": family_name, "id": "family-1"}
        return self.family

    def ensure_member(self, family, display_name: str, is_child: bool, avatar_color: str | None):
        member = {
            "family": family,
            "display_name": display_name,
            "is_child": is_child,
            "avatar_color": avatar_color,
            "id": display_name.lower(),
        }
        self.members[display_name] = member
        return member

    def upsert_device_for_member(self, member, provider: str, external_id: str, label: str | None):
        self.devices[external_id] = {
            "member_id": member["id"],
            "provider": provider,
            "label": label,
        }

    def commit(self) -> None:
        self.committed = True


def test_bootstrap_seeds_family_members_and_entity_mappings() -> None:
    repository = FakeBootstrapRepository()
    service = BootstrapService(repository)

    service.seed_home_assistant_members(
        family_slug="dev-family",
        family_name="GpsTrack Family",
        members=[
            HomeAssistantBootstrapMember(
                display_name="Sam",
                entity_id="device_tracker.sam_phone",
                is_child=True,
                device_label="Sam Phone",
            )
        ],
    )

    assert repository.family == {"slug": "dev-family", "name": "GpsTrack Family", "id": "family-1"}
    assert repository.members["Sam"]["is_child"] is True
    assert repository.devices["device_tracker.sam_phone"]["label"] == "Sam Phone"
    assert repository.committed is True
