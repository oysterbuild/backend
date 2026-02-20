from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from settings import get_settings


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.

    This allows the API to handle requests from different origins,
    which is essential for web applications consuming this API.
    """
    settings = get_settings()

    # Parse allowed origins from settings
    # In development, this might be a single origin like http://localhost:3000
    # In production, this would be your frontend domain(s)
    allowed_origins = ["http://localhost:3000", "https://oysterbuild.pm"]

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],  # You can restrict to specific HTTP methods if needed
        allow_headers=[
            "Authorization",
            "Content-Type",
        ],  # You can restrict to specific headers if needed
        expose_headers=["X-Request-ID"],  # Expose custom headers to the frontend
        max_age=600,  # Cache preflight requests for 10 minutes
    )
