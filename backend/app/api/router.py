from fastapi import APIRouter

from app.api.routes import health, home_assistant, members, places

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(home_assistant.router, prefix="/home-assistant", tags=["home-assistant"])
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
