from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from typing import Callable
import logging
from utils.loggers import setup_logger

# Set up a logger for this module
logger = setup_logger("error_handler")


class ErrorHandler(BaseHTTPMiddleware):
    """
    Middleware for handling uncaught exceptions in the application.
    Converts all exceptions to a standardized JSON response format.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Handle request and catch any unhandled exceptions.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the next handler or an error response
        """
        try:
            # Process the request with the next handler
            return await call_next(request)

        except Exception as e:
            # Log the exception
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(traceback.format_exc())

            # Return a standardized error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "An unexpected error occurred",
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                },
            )
