import redis.asyncio as redis
from settings import get_settings

settings = get_settings()

redis_client = redis.from_url("redis://redis:6379/0", decode_responses=True)
