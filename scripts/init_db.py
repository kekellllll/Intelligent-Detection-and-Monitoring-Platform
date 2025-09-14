"""Database migration and setup utilities."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.core.config import get_settings
from app.models.sensor import SensorData, AnomalyAlert


async def create_tables():
    """Create database tables."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database tables created successfully!")


async def drop_tables():
    """Drop database tables."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
    print("Database tables dropped successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        asyncio.run(drop_tables())
    else:
        asyncio.run(create_tables())