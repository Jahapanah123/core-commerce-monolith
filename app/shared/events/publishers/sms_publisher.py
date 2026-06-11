import json
import uuid
import aio_pika
from app.shared.events.infra.rabbitmq import get_channel
from app.shared.core.config import settings
from app.shared.utils.loggers import logger
from app.auth.interfaces import MessagePublisher


class SMSPublisher(MessagePublisher):
    
    async def publish_sms_job(self, phone: str, otp: str) -> None:
        try:
            channel = await get_channel()
            exchange = await channel.get_exchange(settings.RABBITMQ_MAIN_EXCHANGE)

            payload = {
                "phone": phone,
                "otp": otp,
                "type": "OTP_SMS"
            }

            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                message_id=str(uuid.uuid4()),              # Fix: unique ID per publish
                correlation_id=phone,                      # kept for tracing
            )

            await exchange.publish(
                message,
                routing_key=settings.RABBITMQ_MAIN_ROUTING_KEY
            )

            logger.info(f"SMS job published | phone: {phone} | msg_id: {message.message_id}")

        except Exception as e:
            logger.error(f"Failed to publish SMS job | phone: {phone} | error: {e}")
            raise