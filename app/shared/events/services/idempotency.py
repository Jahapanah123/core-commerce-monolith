import redis.asyncio as aioredis
from app.shared.core.config import settings

redis_client = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


async def is_processed(key: str) -> bool:
    return bool(await redis_client.exists(key))


async def mark_processed(key: str) -> None:
    await redis_client.set(key, "1", ex=86400)