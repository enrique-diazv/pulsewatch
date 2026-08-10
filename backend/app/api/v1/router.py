from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.incidents import router as incidents_router
from app.api.v1.endpoints.monitors import router as monitors_router
from app.api.v1.endpoints.realtime import router as realtime_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(monitors_router)
router.include_router(incidents_router)
router.include_router(realtime_router)
