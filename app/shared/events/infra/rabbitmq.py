import aio_pika
from aio_pika import Channel
from aio_pika.abc import AbstractRobustConnection

from app.shared.core.config import settings
from app.shared.utils.loggers import logger

_connection: AbstractRobustConnection | None = None
_channel: Channel | None = None


async def init_rabbitmq() -> None:
    global _connection, _channel

    # ───── GUARD: already initialized ─────
    if _connection is not None and not _connection.is_closed:      # Fix: skip if already up
        logger.info("RabbitMQ already initialized, skipping")
        return

    try:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        _channel = await _connection.channel()
        await _channel.set_qos(prefetch_count=10)

        # ───────── EXCHANGES ─────────
        main_ex = await _channel.declare_exchange(
            settings.RABBITMQ_MAIN_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        retry_ex = await _channel.declare_exchange(
            settings.RABBITMQ_RETRY_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        dlq_ex = await _channel.declare_exchange(
            settings.RABBITMQ_DLQ_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        # ───────── DLQ QUEUE ─────────
        dlq_q = await _channel.declare_queue(
            settings.RABBITMQ_DLQ_QUEUE,
            durable=True,
        )
        await dlq_q.bind(dlq_ex, settings.RABBITMQ_DLQ_ROUTING_KEY)

        # ───────── MAIN QUEUE ─────────
        main_q = await _channel.declare_queue(
            settings.RABBITMQ_MAIN_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.RABBITMQ_RETRY_EXCHANGE,
                "x-dead-letter-routing-key": settings.RABBITMQ_RETRY_ROUTING_KEY,
            },
        )
        await main_q.bind(main_ex, settings.RABBITMQ_MAIN_ROUTING_KEY)

        # ───────── RETRY QUEUE (5 sec) ─────────
        retry_q_5 = await _channel.declare_queue(
            settings.RABBITMQ_RETRY_QUEUE_5,
            durable=True,
            arguments={
                "x-message-ttl": 5000,
                "x-dead-letter-exchange": settings.RABBITMQ_MAIN_EXCHANGE,
                "x-dead-letter-routing-key": settings.RABBITMQ_MAIN_ROUTING_KEY,
            },
        )
        await retry_q_5.bind(retry_ex, settings.RABBITMQ_RETRY_ROUTING_KEY_5)

        # ───────── RETRY QUEUE (10 sec) ─────────
        retry_q_10 = await _channel.declare_queue(
            settings.RABBITMQ_RETRY_QUEUE_10,
            durable=True,
            arguments={
                "x-message-ttl": 10000,
                "x-dead-letter-exchange": settings.RABBITMQ_MAIN_EXCHANGE,
                "x-dead-letter-routing-key": settings.RABBITMQ_MAIN_ROUTING_KEY,
            },
        )
        await retry_q_10.bind(retry_ex, settings.RABBITMQ_RETRY_ROUTING_KEY_10)

        logger.info("RabbitMQ topology initialized successfully")

    except Exception as e:
        logger.error(f"RabbitMQ init failed: {e}")
        raise


async def get_channel() -> Channel:
    if _channel is None or _channel.is_closed:                    
        raise RuntimeError("RabbitMQ channel not available")
    return _channel


async def close_rabbitmq() -> None:
    global _connection, _channel                                   

    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("RabbitMQ connection closed")

    _connection = None                                             
    _channel = None                                                