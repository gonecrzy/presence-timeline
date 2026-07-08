from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str | int]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "retention_days": settings.retention_days,
    }
