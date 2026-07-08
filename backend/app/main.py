from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import initialize_database

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Provider-agnostic API for private family location tracking.",
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup() -> None:
    if settings.auto_create_tables:
        initialize_database()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }
