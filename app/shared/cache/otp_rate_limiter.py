import redis.asyncio as redis

RATE_LIMIT_PREFIX = "otp_rl:"
WINDOW_SECONDS = 60
MAX_REQUESTS = 3


LUA_SCRIPT = """
local current = redis.call("GET", KEYS[1])

if current == false then
    redis.call("SET", KEYS[1], 1, "EX", ARGV[1])
    return 1
end

current = tonumber(current)

if current >= tonumber(ARGV[2]) then
    return 0
end

current = current + 1
redis.call("SET", KEYS[1], current, "EX", ARGV[1])

return 1
"""


class OTPRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.script = self.redis.register_script(LUA_SCRIPT)

    async def is_allowed(self, identifier: str) -> bool:
        key = f"{RATE_LIMIT_PREFIX}{identifier}"

        result = await self.script(
            keys=[key],
            args=[WINDOW_SECONDS, MAX_REQUESTS]
        )

        return bool(result)

    async def get_remaining(self, identifier: str) -> int:
        key = f"{RATE_LIMIT_PREFIX}{identifier}"
        current = await self.redis.get(key)

        if not current:
            return MAX_REQUESTS

        return max(0, MAX_REQUESTS - int(current))