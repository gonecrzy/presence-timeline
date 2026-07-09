from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HomeAssistantBootstrapMember(BaseModel):
    display_name: str
    entity_id: str
    is_child: bool = True
    avatar_color: str | None = None
    device_label: str | None = None


class Settings(BaseSettings):
    app_name: str = "GpsTrack API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://gpstrack:gpstrack@db:5432/gpstrack"
    retention_days: int = 7
    auth_mode: Literal["open", "oidc"] = "open"
    open_auth_family_slug: str = "dev-family"
    open_auth_parent_subject: str = "dev-parent"
    default_family_name: str = "GpsTrack Family"
    oidc_issuer_url: str | None = None
    oidc_client_id: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    enable_home_assistant_ingestion: bool = False
    home_assistant_bootstrap_members: list[HomeAssistantBootstrapMember] = Field(default_factory=list)
    home_assistant_ws_url: str = "ws://homeassistant.local:8123/api/websocket"
    home_assistant_access_token: str = "replace-me"
    enable_reverse_geocoding: bool = True
    reverse_geocode_url: str = "https://nominatim.openstreetmap.org/reverse"
    reverse_geocode_user_agent: str = "gpstrack/0.1.0"
    reverse_geocode_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_prefix="GPSTRACK_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
