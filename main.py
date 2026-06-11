from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI

from app.shared.cache.redis_client import init_redis, close_redis, get_redis
from app.shared.events.infra.rabbitmq import init_rabbitmq, close_rabbitmq
from app.shared.events.workers.sms_worker import start_sms_worker
from app.shared.core.exceptions import AppException, app_exception_handler
from app.auth.api.v1.router import router as auth_router
from app.shared.utils.loggers import logger
from app.shared.cache.otp_cache import OTPCache
from app.auth.services.auth_service import AuthService
from app.shared.events.publishers.sms_publisher import SMSPublisher

worker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global worker_task

    # STARTUP
    logger.info("Starting application...")

    await init_redis()
    for i in range(10):
        try:
            await init_rabbitmq()
            break
        except Exception:
            await asyncio.sleep(min(2 ** i, 30))
    else:
        raise RuntimeError("RabbitMQ not ready")
    
    # checkout get clients
    redis_client = get_redis()
    
    
    # Create Implementations
    
    otp_storage = OTPCache(redis_client=redis_client)
    sms_publisher = SMSPublisher()
    
    #  Wire Service (Dependency Injection)
    
    auth_service = AuthService(otp_storage=otp_storage, publisher=sms_publisher)
    
    # Store in App State for Router to use
    
    app.state.auth_service = auth_service
    
    # backgroud worker
    
    worker_task = asyncio.create_task(start_sms_worker())
    logger.info("SMS worker started")

    yield

    # SHUTDOWN
    logger.info("Shutting down application...")

    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            logger.info("SMS worker stopped")
            pass

    await close_redis()
    await close_rabbitmq()

    logger.info("Shutdown complete")


app = FastAPI(title="Core Commerce", lifespan=lifespan)

app.add_exception_handler(AppException, app_exception_handler)
app.include_router(auth_router, prefix="/api/v1")