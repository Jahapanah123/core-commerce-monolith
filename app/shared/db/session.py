from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncConnection
from sqlalchemy.orm import sessionmaker
from app.shared.core import settings

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True,
    )

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    )

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session