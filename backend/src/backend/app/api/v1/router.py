from fastapi import APIRouter

from backend.app.api.v1.routes.health import router as health_router
from backend.app.api.v1.routes.auth import router as auth_router
from backend.app.api.v1.routes.classrooms import router as classrooms_router
from backend.app.api.v1.routes.content import router as content_router
from backend.app.api.v1.routes.teacher import router as teacher_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(classrooms_router)
api_router.include_router(content_router)
api_router.include_router(teacher_router)
