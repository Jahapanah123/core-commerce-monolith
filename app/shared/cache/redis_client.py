import redis.asyncio as redis
from app.shared.core.config import settings

redis_client: redis.Redis | None = None


async def init_redis():
    global redis_client
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise Exception("Redis not initialized")
    return redis_client


async def close_redis():
    if redis_client:
        await redis_client.close()