# Import all routers
from fastapi import APIRouter

# VERSION ROUTERS
api_v1_router = APIRouter(
    prefix="/api/v1",
)


# NEW ROUTERS
from routers.auth_router import router as auth_router
from routers.project_router import router as project_router
from routers.core import router as core_router
from routers.payment_router import router as payment_router
from routers.inspections_router import router as inspection_router
from routers.admins_router import router as admims_router
from routers.chat_router import router as chat_router

# Include routers with tags
api_v1_router.include_router(auth_router, tags=["Authentication"])
api_v1_router.include_router(project_router, tags=["Projects"])
api_v1_router.include_router(core_router, tags=["Core"])
api_v1_router.include_router(payment_router, tags=["Payments"])
api_v1_router.include_router(inspection_router, tags=["Projects-Inspectors"])
api_v1_router.include_router(admims_router, tags=["Admin"])
api_v1_router.include_router(chat_router, tags=["Chat"])
