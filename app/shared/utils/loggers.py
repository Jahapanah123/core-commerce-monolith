import sys
from loguru import logger


logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    backtrace=True,
    diagnose=False,
)

logger.add(
    "logs/app.log",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=False,
)