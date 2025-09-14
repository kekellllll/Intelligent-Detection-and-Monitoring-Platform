"""Database connection and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Global variables for database connection
engine = None
async_session_maker = None


async def init_db() -> None:
    """Initialize database connection."""
    global engine, async_session_maker
    
    settings = get_settings()
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    logger.info("Database connection initialized")


async def get_db_session() -> AsyncSession:
    """Get database session."""
    if async_session_maker is None:
        await init_db()
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()