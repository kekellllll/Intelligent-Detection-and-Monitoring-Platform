"""Configuration management for the platform."""
from functools import lru_cache
from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Intelligent Detection and Monitoring Platform"
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/monitoring_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SENSOR_TOPIC: str = "sensor-data"
    KAFKA_ANOMALY_TOPIC: str = "anomaly-alerts"
    
    # ML Model
    MODEL_PATH: str = "models/anomaly_detector.h5"
    MODEL_ACCURACY_THRESHOLD: float = 0.95
    
    # Monitoring
    PROMETHEUS_PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    
    # Kubernetes
    NAMESPACE: str = "monitoring-platform"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()