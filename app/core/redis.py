import redis.asyncio as redis
from app.core.settings import get_settings

settings = get_settings()

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
