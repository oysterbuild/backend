import time
from typing import Callable, Dict, Optional

import jwt
from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from settings import get_settings

settings = get_settings()
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm


class RateLimiter(BaseHTTPMiddleware):
    """
    Token Bucket Rate Limiter

    Priority: 1. Authenticated user (JWT)  2. IP address

    IMPORTANT — single-process only: buckets live in this process's memory.
    Running more than one worker/instance multiplies the effective limit
    (N workers = N independent buckets per client). If you scale beyond one
    worker, back this with Redis (e.g. INCR + PEXPIRE, or a Lua token-bucket
    script) instead — this implementation deliberately doesn't do that for
    you since it changes your infra requirements.
    """

    def __init__(
        self,
        app,
        requests_limit: int = 100,
        window_seconds: int = 60,
        burst: int = 120,
        cleanup_interval: int = 300,
        excluded_paths: set | None = None,
        trust_proxy_headers: bool = True,
        max_buckets: int = 50_000,
    ):
        super().__init__(app)

        self.capacity = burst
        self.refill_rate = requests_limit / window_seconds
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        self.max_buckets = max_buckets

        # key -> {"tokens": float, "last": float}
        # No lock: every access below is synchronous (no `await` in between),
        # so on a single asyncio event loop this is already atomic — the
        # loop can't switch coroutines mid-block. If you ever run this
        # under a threaded server this assumption breaks and you'd need a
        # real per-key lock (or just move to Redis, per the class docstring).
        self.buckets: Dict[str, Dict[str, float]] = {}

        self.excluded_paths = excluded_paths or {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        key = self._get_client_key(request)
        now = time.time()

        self._cleanup(now)

        bucket = self.buckets.get(key, {"tokens": float(self.capacity), "last": now})

        elapsed = now - bucket["last"]
        bucket["tokens"] = min(
            self.capacity, bucket["tokens"] + elapsed * self.refill_rate
        )
        bucket["last"] = now

        if bucket["tokens"] < 1:
            self.buckets[key] = bucket
            retry_after = max(1, int((1 - bucket["tokens"]) / self.refill_rate))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_limit),
                    "X-RateLimit-Remaining": "0",
                },
                content={"detail": "Too many requests. Please slow down."},
            )

        bucket["tokens"] -= 1
        remaining = int(bucket["tokens"])
        self.buckets[key] = bucket

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _get_client_key(self, request: Request) -> str:
        """
        Priority: 1. JWT user id 2. IP address
        """

        # -------------------------
        # JWT
        # -------------------------
        auth = request.headers.get("Authorization")

        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]

            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = (
                    payload.get("sub") or payload.get("user_id") or payload.get("id")
                )
                if (
                    user_id
                ):  # the email is used which is actually unqiue for that customer
                    return f"user:{user_id}"
            except jwt.PyJWTError:
                pass

        # -------------------------
        # IP address
        # -------------------------
        ip = self._resolve_ip(request)
        return f"ip:{ip}"

    def _resolve_ip(self, request: Request) -> str:
        """
        `request.client.host` is trusted here rather than reading
        X-Forwarded-For/X-Real-IP directly: those headers are attacker-
        controlled unless a trusted reverse proxy set them, and reading them
        unconditionally lets any client bypass rate limiting by sending a
        different fake IP on every request. ProxyHeadersMiddleware (see
        main.py) already resolves the real client IP from those headers —
        but only when the request actually came from a trusted proxy — and
        runs before this middleware, so `request.client.host` is the
        correct, spoof-resistant value to key on.
        """
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup(self, now: float):
        if (
            now - self.last_cleanup < self.cleanup_interval
            and len(self.buckets) < self.max_buckets
        ):
            return

        timeout = self.capacity / self.refill_rate

        stale = [
            key
            for key, bucket in self.buckets.items()
            if now - bucket["last"] > timeout
        ]
        for key in stale:
            del self.buckets[key]

        # Hard cap as a backstop against spoofed-key memory exhaustion even
        # when trust_proxy_headers is off (JWT/API-key values are still
        # attacker-suppliable at some volume). Evicts oldest-touched first.
        if len(self.buckets) > self.max_buckets:
            overflow = len(self.buckets) - self.max_buckets
            oldest = sorted(self.buckets.items(), key=lambda kv: kv[1]["last"])[
                :overflow
            ]
            for key, _ in oldest:
                del self.buckets[key]

        self.last_cleanup = now
