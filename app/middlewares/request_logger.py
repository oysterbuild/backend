import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from utils.loggers import setup_logger

logger = setup_logger("request_logger")

# Polled every few seconds by Docker's healthcheck - logging it would just
# be noise, not a request anyone needs to see.
SKIP_PATHS = {"/health"}


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code and duration for every request to the console."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        client_ip = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Real-IP")
            or request.headers.get("X-Forwarded-For")
            or (request.client.host if request.client else "unknown")
        )

        logger.info(
            f"{request.method} {request.url.path} {response.status_code} "
            f"{duration_ms:.1f}ms - {client_ip}"
        )

        return response
