"""Data models for sensor data and monitoring."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, Field

from app.core.database import Base


class SensorData(Base):
    """Sensor data table."""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    sensor_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    location = Column(String(100))
    metadata = Column(JSONB)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnomalyAlert(Base):
    """Anomaly alerts table."""
    __tablename__ = "anomaly_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    message = Column(Text, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    sensor_value = Column(Float, nullable=False)
    threshold = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    metadata = Column(JSONB)


# Pydantic models for API
class SensorDataCreate(BaseModel):
    """Schema for creating sensor data."""
    sensor_id: str = Field(..., min_length=1, max_length=50)
    sensor_type: str = Field(..., min_length=1, max_length=50)
    value: float
    unit: str = Field(..., min_length=1, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    metadata: Optional[dict] = None


class SensorDataResponse(BaseModel):
    """Schema for sensor data response."""
    id: int
    sensor_id: str
    sensor_type: str
    timestamp: datetime
    value: float
    unit: str
    location: Optional[str]
    is_anomaly: bool
    anomaly_score: Optional[float]
    
    class Config:
        from_attributes = True


class AnomalyAlertCreate(BaseModel):
    """Schema for creating anomaly alerts."""
    sensor_id: str
    alert_type: str
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    message: str
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    sensor_value: float
    threshold: Optional[float] = None
    metadata: Optional[dict] = None


class AnomalyAlertResponse(BaseModel):
    """Schema for anomaly alert response."""
    id: int
    sensor_id: str
    alert_type: str
    severity: str
    message: str
    anomaly_score: float
    sensor_value: float
    threshold: Optional[float]
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True