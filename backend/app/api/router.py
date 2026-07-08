from fastapi import APIRouter

from app.api.routes import health, members

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(members.router, prefix="/members", tags=["members"])
