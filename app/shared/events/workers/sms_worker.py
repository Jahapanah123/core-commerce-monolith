import json
import asyncio
from aio_pika.abc import AbstractIncomingMessage

from app.shared.events.infra.rabbitmq import get_channel, init_rabbitmq
from app.shared.events.services.sms_service import send_sms
from app.shared.events.services.idempotency import is_processed, mark_processed
from app.shared.events.services.retry_handler import handle_retry
from app.shared.core.config import settings
from app.shared.utils.loggers import logger
from app.shared.cache.redis_client import init_redis


async def _on_message(message: AbstractIncomingMessage) -> None:
    body = {}

    try:
        body = json.loads(message.body.decode())

        phone = body["phone"]
        otp = body["otp"]
        retry_count = body.get("retry_count", 0)

        msg_id = message.message_id or f"{phone}:{otp}"

        # ───── IDEMPOTENCY ─────
        if await is_processed(msg_id):
            logger.info(f"Duplicate ignored | {msg_id}")
            await message.ack()
            return

        logger.info(f"Processing SMS | phone={phone} retry={retry_count} msg_id={msg_id}")

        # ───── BUSINESS LOGIC ─────
        success = await send_sms(phone, otp)

        if success:
            await mark_processed(msg_id)
            await message.ack()                           
            logger.info(f"SMS sent successfully | phone={phone}")
            return

        # ───── FAILURE → DELEGATE RETRY ─────
        logger.warning(f"SMS send failed | phone={phone} | retry_count={retry_count}")
        retry_ok = await handle_retry(phone, otp, retry_count)

        if retry_ok:
            await message.ack()                          
        else:
            await message.ack()                           
            logger.error(f"Message sent to DLQ | phone={phone}")

    except KeyError as e:
        logger.error(f"Missing required field | {e} | body={body}")
        await message.nack(requeue=False)                 

    except Exception as e:
        logger.error(f"Worker crash | {e} | body={body}")

        try:
            retry_ok = await handle_retry(
                phone=body.get("phone", "unknown"),
                otp=body.get("otp", ""),
                retry_count=body.get("retry_count", 0)
            )

            if retry_ok:
                await message.ack()
            else:
                await message.ack()                       

        except Exception as inner:
            logger.error(f"Retry delegation failed | {inner}")
            await message.nack(requeue=False)            


async def start_sms_worker() -> None:
    # Fix: removed retry loop, assumes bootstrap already called init_rabbitmq()
    # If running standalone, uncomment the init call below
    # await init_rabbitmq()

    channel = await get_channel()
    queue = await channel.get_queue(settings.RABBITMQ_MAIN_QUEUE)

    await queue.consume(_on_message)

    logger.info("SMS Worker started")

    await asyncio.Future()  # run forever


if __name__ == "__main__":
    # For standalone worker execution (not integrated with app bootstrap)
    async def main():
        await init_rabbitmq()
        await init_redis()
        await start_sms_worker()
    
    asyncio.run(main())