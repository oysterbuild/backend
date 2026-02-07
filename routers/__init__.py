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

# Include routers with tags
api_v1_router.include_router(auth_router, tags=["Authentication"])
api_v1_router.include_router(project_router, tags=["Projects"])
api_v1_router.include_router(core_router, tags=["Core"])
api_v1_router.include_router(payment_router, tags=["Payments"])
