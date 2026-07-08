import pytest
from fastapi import HTTPException

from app.core.auth import OIDCAuthenticator, OpenAccessAuthenticator, require_app_access
from app.core.config import Settings


def test_open_authenticator_returns_dev_principal() -> None:
    settings = Settings(
        auth_mode="open",
        open_auth_family_slug="family-alpha",
        open_auth_parent_subject="parent-123",
    )

    principal = OpenAccessAuthenticator(settings).authenticate()

    assert principal.auth_mode == "open"
    assert principal.family_slug == "family-alpha"
    assert principal.subject == "parent-123"
    assert principal.roles == ("parent",)


def test_oidc_authenticator_requires_authorization_header() -> None:
    settings = Settings(
        auth_mode="oidc",
        oidc_issuer_url="https://auth.example.com/application/o/gpstrack/",
        oidc_client_id="gpstrack-mobile",
        oidc_audience="gpstrack-api",
    )

    with pytest.raises(HTTPException) as exc:
        OIDCAuthenticator(settings).authenticate()

    assert exc.value.status_code == 401


def test_require_app_access_rejects_incomplete_oidc_configuration() -> None:
    settings = Settings(auth_mode="oidc")

    with pytest.raises(RuntimeError, match="GPSTRACK_OIDC_ISSUER_URL"):
        require_app_access(settings=settings)
