import redis.asyncio as redis
from app.shared.utils.otp_generator import hash_otp, verify_otp_hash
from app.auth.interfaces import OTPStorage


OTP_TTL = 300  # 5 minutes
OTP_PREFIX = "otp:"
OTP_ATTEMPT_PREFIX = "otp_attempts:"
MAX_ATTEMPTS = 3


class OTPCache(OTPStorage):
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def store_otp(self, mobile: str, otp: str):
        key = f"{OTP_PREFIX}{mobile}"
        hashed = hash_otp(otp)
        await self.redis.setex(key, OTP_TTL, hashed)

    async def get_otp(self, mobile: str) -> str | None:           # ← Fixed: removed otp param
        key = f"{OTP_PREFIX}{mobile}"
        stored_hash = await self.redis.get(key)

        if not stored_hash:
            return None

        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode()

        return stored_hash                                        # ← return the hash, let service verify

    async def delete_otp(self, mobile: str) -> None:
        await self.redis.delete(f"{OTP_PREFIX}{mobile}")

    async def increment_attempts(self, mobile: str) -> int:
        key = f"{OTP_ATTEMPT_PREFIX}{mobile}"
        attempts = await self.redis.incr(key)

        if attempts == 1:
            await self.redis.expire(key, OTP_TTL)

        return attempts

    async def clear_attempts(self, mobile: str) -> None:
        await self.redis.delete(f"{OTP_ATTEMPT_PREFIX}{mobile}")

    async def otp_exists(self, mobile: str) -> bool:
        key = f"{OTP_PREFIX}{mobile}"
        return await self.redis.exists(key) == 1

    async def verify_otp(self, mobile: str, otp: str) -> bool:   # ← renamed from verify_with_limits
        """
        Verify OTP with attempt limiting.
        Returns True if valid, False otherwise.
        Auto-deletes OTP after max attempts.
        """
        stored_hash = await self.get_otp(mobile)

        if not stored_hash:
            return False

        is_valid = verify_otp_hash(otp, stored_hash)

        if is_valid:
            await self.delete_otp(mobile)
            await self.clear_attempts(mobile)
            return True

        attempts = await self.increment_attempts(mobile)

        if attempts >= MAX_ATTEMPTS:
            await self.delete_otp(mobile)
            await self.clear_attempts(mobile)

        return False