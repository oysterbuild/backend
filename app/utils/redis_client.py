import redis.asyncio as redis
from settings import get_settings

settings = get_settings()

if settings.environment in ["production", "staging"]:
    redis_client = redis.from_url("redis://redis:6379/0", decode_responses=True)
else:
    redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)

# redis_client = redis.from_url("redis://redis:6379/0", decode_responses=True)
