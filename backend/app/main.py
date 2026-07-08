from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.repositories.location_repository import LocationRepository
from app.services.bootstrap import BootstrapService

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.home_assistant_bootstrap_members:
        db = SessionLocal()
        try:
            BootstrapService(LocationRepository(db)).seed_home_assistant_members(
                family_slug=settings.open_auth_family_slug,
                family_name=settings.default_family_name,
                members=settings.home_assistant_bootstrap_members,
            )
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Provider-agnostic API for private family location tracking.",
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }
