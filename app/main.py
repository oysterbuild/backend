from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from utils.loggers import setup_logger
import logging
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from settings import get_settings
from routers import api_v1_router
import asyncio
from services.permission_service import seed_roles_permissions
from services.plan_service import seed_plans
from utils.db_setup import get_database
from fastapi.staticfiles import StaticFiles
from utils.redis_client import redis_client
from middlewares.cors import setup_cors
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# from utils import cloudinary

from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()

log_level = logging.INFO
logger = setup_logger(__name__, log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Oysterbuild API...")
    try:
        logger.info("Starting Oysterbuild API...")

        # load permission on app start.......
        logger.info("Loading Permission on App starts")
        # asyncio.create_task(seed_roles_permissions())

        # asyncio.create_task(seed_plans())

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

    yield
    # Shutdown
    logger.info("Shutting down Oysterbuild API...")


app = FastAPI(
    title=settings.app_name,
    description="API for Oysterbuild",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Restrict which hosts can hit your API at all
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["oysterbuild.pm", "localhost"])

app.include_router(api_v1_router)

# setup cors
setup_cors(app)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []

    for err in exc.errors():
        errors.append(
            {
                "field": ".".join(map(str, err.get("loc", []))),
                "message": err.get("msg"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Invalid request payload",
            "errors": errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail

    # Defaults
    response_payload = {
        "success": False,
        "statusCode": exc.status_code,
        "message": "An unexpected error occurred",
    }

    if isinstance(detail, dict):
        # Preserve message, status_code, provider if present
        response_payload["message"] = detail.get("message", response_payload["message"])
        response_payload["statusCode"] = detail.get("statusCode", exc.status_code)
        if "provider" in detail:
            response_payload["provider"] = detail.get("provider")

    elif isinstance(detail, str):
        response_payload["message"] = detail

    return JSONResponse(status_code=exc.status_code, content=response_payload)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/redis_health")
async def redis_health_check():
    try:
        await redis_client.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
