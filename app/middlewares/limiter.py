import jwt
from fastapi import Request
from slowapi import Limiter

from settings import get_settings

settings = get_settings()
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm


def rate_limit_key(request: Request) -> str:
    """
    Priority: 1. Authenticated user (JWT)  2. IP address — same resolution
    the app-wide token-bucket RateLimiter middleware uses
    (middlewares/rate_limiter.py), so a logged-in user is limited by
    identity rather than by IP.
    """
    auth = request.headers.get("Authorization")

    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
            if user_id:
                return f"user:{user_id}"
        except jwt.PyJWTError:
            pass

    return f"ip:{request.client.host if request.client else 'unknown'}"


# Per-route limiter for sensitive endpoints (login, OTP, password reset, ...)
# that need a stricter cap than the app-wide RateLimiter middleware. Apply
# with `@limiter.limit("5/5minutes")` directly on the route, below
# `@router.post(...)` — the decorated endpoint must accept `request: Request`
# since slowapi reads the client's key from it. See main.py for the matching
# RateLimitExceeded exception handler.
#
# headers_enabled=False: this app's endpoints return a pydantic APIResponse
# rather than a Starlette Response, and slowapi's header injection requires
# a real Response instance on the success path — leave X-RateLimit-* header
# writing to the app-wide middleware instead.
#
# Counters live in Redis so the limit is shared across all gunicorn workers
# (in-memory counters would give each worker its own allowance). If Redis is
# unreachable, swallow_errors + in_memory_fallback keep the endpoints working
# with per-worker limits instead of failing every request.
_REDIS_HOST = "redis" if settings.environment in ["production", "staging"] else "localhost"

limiter = Limiter(
    key_func=rate_limit_key,
    headers_enabled=False,
    storage_uri=f"redis://{_REDIS_HOST}:6379/0",
    key_prefix="ratelimit",
    swallow_errors=True,
    in_memory_fallback_enabled=True,
    enabled=settings.enable_rate_limiting,
)
