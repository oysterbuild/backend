"""Middleware package for SurgePay API."""

from fastapi import FastAPI
from settings import Settings, get_settings
from middlewares.cors import setup_cors
from middlewares.rate_limiter import RateLimiter
from middlewares.error_handlers import ErrorHandler
from middlewares.request_logger import RequestLoggerMiddleware


def setup_middlewares(app: FastAPI) -> None:
    """
    Configure all middlewares for the application.

    This function should be called in the main application setup.
    The order of middleware registration is important - the last registered
    middleware will be the first to process a request.
    """
    settings = get_settings()

    # Setup CORS middleware
    setup_cors(app)

    # Setup request logger middleware
    app.add_middleware(RequestLoggerMiddleware)

    # Setup error handler middleware
    app.add_middleware(ErrorHandler)

    # Setup rate limiter middleware if enabled
    if settings.enable_rate_limiting:
        app.add_middleware(
            RateLimiter,
            requests_limit=50,
            window_seconds=60,
        )
