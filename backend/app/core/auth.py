from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings

AuthMode = Literal["open", "oidc"]


@dataclass(frozen=True, slots=True)
class AppPrincipal:
    subject: str
    family_slug: str
    roles: tuple[str, ...]
    auth_mode: AuthMode


class OpenAccessAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authenticate(self, authorization: str | None = None) -> AppPrincipal:
        return AppPrincipal(
            subject=self.settings.open_auth_parent_subject,
            family_slug=self.settings.open_auth_family_slug,
            roles=("parent",),
            auth_mode="open",
        )


class OIDCAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authenticate(self, authorization: str | None = None) -> AppPrincipal:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header.",
            )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OIDC auth is configured but not implemented yet.",
        )


def get_authenticator(settings: Settings) -> OpenAccessAuthenticator | OIDCAuthenticator:
    if settings.auth_mode == "open":
        return OpenAccessAuthenticator(settings)

    if settings.auth_mode == "oidc":
        _validate_oidc_settings(settings)
        return OIDCAuthenticator(settings)

    raise RuntimeError(f"Unsupported auth mode: {settings.auth_mode}")


def require_app_access(
    authorization: str | None = Header(default=None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> AppPrincipal:
    authenticator = get_authenticator(settings)
    return authenticator.authenticate(authorization)


def _validate_oidc_settings(settings: Settings) -> None:
    missing = [
        name
        for name, value in (
            ("GPSTRACK_OIDC_ISSUER_URL", settings.oidc_issuer_url),
            ("GPSTRACK_OIDC_CLIENT_ID", settings.oidc_client_id),
            ("GPSTRACK_OIDC_AUDIENCE", settings.oidc_audience),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "OIDC auth mode requires configuration for: " + ", ".join(missing),
        )
