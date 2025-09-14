"""
Main FastAPI application entry point for the Intelligent Detection and Monitoring Platform.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging as structlog

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.services.redis_service import RedisService
from app.services.kafka_service import KafkaService

logger = structlog.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    logger.info("Starting Intelligent Detection and Monitoring Platform")
    
    # Initialize database
    await init_db()
    
    # Initialize Redis connection
    redis_service = RedisService()
    await redis_service.connect()
    
    # Initialize Kafka
    kafka_service = KafkaService()
    await kafka_service.initialize()
    
    logger.info("Platform initialization completed")
    yield
    
    # Cleanup
    await redis_service.disconnect()
    await kafka_service.close()
    logger.info("Platform shutdown completed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Intelligent Detection and Monitoring Platform",
        description="A distributed system for intelligent sensor data monitoring and anomaly detection",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "platform": "intelligent-detection-monitoring"}
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)