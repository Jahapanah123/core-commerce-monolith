from concurrent.futures import ThreadPoolExecutor
from app.shared.core.config import settings
from app.shared.utils.loggers import logger
import asyncio
from functools import lru_cache

_executor = ThreadPoolExecutor(max_workers=10)


@lru_cache
def get_twilio_client():
    from twilio.rest import Client
    return Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )


async def send_sms(phone: str, otp: str) -> bool:
    if settings.USE_MOCK_SMS:
        logger.info(f"[MOCK SMS] Phone={phone} OTP={otp}")
        return True

    return await _send_via_twilio(phone, otp)


async def _send_via_twilio(phone: str, otp: str) -> bool:
    try:
        loop = asyncio.get_running_loop()
        client = get_twilio_client()

        def _sync_send():
            msg = client.messages.create(
                body=f"Your OTP: {otp}. Valid for 5 minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=f"+91{phone}"
            )
            logger.info(f"Twilio SID={msg.sid}")

        await asyncio.wait_for(
            loop.run_in_executor(_executor, _sync_send),
            timeout=10
        )

        logger.info(f"SMS sent | phone={phone}")
        return True

    except asyncio.TimeoutError:
        logger.error(f"Twilio timeout | phone={phone}")
        return False

    except Exception as e:
        logger.error(f"Twilio error | phone={phone} | error={e}")
        return False