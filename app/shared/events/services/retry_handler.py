import json
import aio_pika
from app.shared.core.config import settings
from app.shared.utils.loggers import logger
from app.shared.events.infra.rabbitmq import get_channel


MAX_RETRIES = 3


async def handle_retry(phone: str, otp: str, retry_count: int) -> bool:
    try:
        channel = await get_channel()
        next_retry = retry_count + 1

        # ───── FINAL FAILURE → DLQ ─────
        if retry_count >= MAX_RETRIES:
            logger.error(f"Max retries exceeded, routing to DLQ | phone={phone}")

            dlq_exchange = await channel.get_exchange(
                settings.RABBITMQ_DLQ_EXCHANGE
            )

            payload = {
                "phone": phone,
                "otp": otp,
                "retry_count": retry_count
            }

            message = aio_pika.Message(                        
                body=json.dumps(payload).encode(),             
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            )

            await dlq_exchange.publish(
                message,                                       
                routing_key=settings.RABBITMQ_DLQ_ROUTING_KEY,
            )

            return False                                      

        # ───── RETRY DECISION ─────
        if next_retry == 1:
            routing_key = settings.RABBITMQ_RETRY_ROUTING_KEY_5
            logger.info(f"Retry-1 (5s) | phone={phone}")

        elif next_retry == 2:
            routing_key = settings.RABBITMQ_RETRY_ROUTING_KEY_10
            logger.info(f"Retry-2 (10s) | phone={phone}")

        else:
            routing_key = settings.RABBITMQ_RETRY_ROUTING_KEY_10
            logger.info(f"Fallback retry (10s) | phone={phone}")

        retry_exchange = await channel.get_exchange(
            settings.RABBITMQ_RETRY_EXCHANGE
        )

        payload = {
            "phone": phone,
            "otp": otp,
            "retry_count": next_retry                         
        }

        message = aio_pika.Message(                           
            body=json.dumps(payload).encode(),                
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await retry_exchange.publish(
            message,                                         
            routing_key=routing_key,
        )

        return True                                           

    except Exception as e:
        logger.error(f"Retry handler failed | phone={phone} | error={e}")
        raise