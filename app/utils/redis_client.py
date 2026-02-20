import redis.asyncio as redis
from settings import get_settings

settings = get_settings()

redis_client = redis.from_url(settings.celery_broker_url, decode_responses=True)
