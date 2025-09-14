"""API router for sensor data endpoints."""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import structlog

from app.core.database import get_db_session
from app.models.sensor import (
    SensorData, AnomalyAlert, SensorDataCreate, SensorDataResponse,
    AnomalyAlertCreate, AnomalyAlertResponse
)
from app.services.redis_service import redis_service
from app.services.kafka_service import kafka_service
from app.ml.anomaly_detection import anomaly_detection_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("/data", response_model=SensorDataResponse)
async def create_sensor_data(
    sensor_data: SensorDataCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new sensor data entry."""
    try:
        # Create database entry
        db_sensor_data = SensorData(**sensor_data.dict())
        db.add(db_sensor_data)
        await db.commit()
        await db.refresh(db_sensor_data)
        
        # Process in background
        background_tasks.add_task(
            process_sensor_data_async,
            sensor_data.dict(),
            db_sensor_data.id
        )
        
        logger.info(f"Created sensor data entry for sensor {sensor_data.sensor_id}")
        return db_sensor_data
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data", response_model=List[SensorDataResponse])
async def get_sensor_data(
    sensor_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """Get sensor data with optional filtering."""
    try:
        query = select(SensorData).order_by(desc(SensorData.timestamp))
        
        if sensor_id:
            query = query.where(SensorData.sensor_id == sensor_id)
        if sensor_type:
            query = query.where(SensorData.sensor_type == sensor_type)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        sensor_data = result.scalars().all()
        
        return sensor_data
        
    except Exception as e:
        logger.error(f"Failed to get sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{sensor_id}/latest", response_model=SensorDataResponse)
async def get_latest_sensor_data(
    sensor_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get latest sensor data for a specific sensor."""
    try:
        query = select(SensorData).where(
            SensorData.sensor_id == sensor_id
        ).order_by(desc(SensorData.timestamp)).limit(1)
        
        result = await db.execute(query)
        sensor_data = result.scalar_one_or_none()
        
        if not sensor_data:
            raise HTTPException(status_code=404, detail="Sensor data not found")
        
        return sensor_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[AnomalyAlertResponse])
async def get_anomaly_alerts(
    sensor_id: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """Get anomaly alerts with optional filtering."""
    try:
        query = select(AnomalyAlert).order_by(desc(AnomalyAlert.timestamp))
        
        if sensor_id:
            query = query.where(AnomalyAlert.sensor_id == sensor_id)
        if severity:
            query = query.where(AnomalyAlert.severity == severity)
        if resolved is not None:
            query = query.where(AnomalyAlert.resolved == resolved)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        return alerts
        
    except Exception as e:
        logger.error(f"Failed to get anomaly alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_anomaly_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Resolve an anomaly alert."""
    try:
        query = select(AnomalyAlert).where(AnomalyAlert.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Resolved anomaly alert {alert_id}")
        return {"message": "Alert resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_sensor_data_async(sensor_data: dict, sensor_data_id: int):
    """Process sensor data asynchronously for anomaly detection."""
    try:
        # Publish to Redis for real-time processing
        await redis_service.publish_sensor_data("sensor_data_stream", sensor_data)
        
        # Send to Kafka for batch processing
        await kafka_service.produce_sensor_data(sensor_data)
        
        # Get historical data for context
        historical_data = await get_historical_sensor_data(
            sensor_data['sensor_id'], 
            hours=24
        )
        
        # Perform anomaly detection
        detection_result = await anomaly_detection_service.detect_anomaly(
            sensor_data, historical_data
        )
        
        # Update sensor data with anomaly information
        await update_sensor_anomaly_status(sensor_data_id, detection_result)
        
        # Create alert if anomaly detected
        if detection_result['is_anomaly']:
            await create_anomaly_alert(sensor_data, detection_result)
        
        logger.debug(f"Processed sensor data for sensor {sensor_data['sensor_id']}")
        
    except Exception as e:
        logger.error(f"Failed to process sensor data asynchronously: {e}")


async def get_historical_sensor_data(sensor_id: str, hours: int = 24) -> List[dict]:
    """Get historical sensor data for anomaly detection context."""
    try:
        # Check cache first
        cache_key = f"historical_data:{sensor_id}:{hours}h"
        cached_data = await redis_service.cache_get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Get from database
        from app.core.database import async_session_maker
        async with async_session_maker() as db:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = select(SensorData).where(
                SensorData.sensor_id == sensor_id,
                SensorData.timestamp >= start_time
            ).order_by(SensorData.timestamp)
            
            result = await db.execute(query)
            sensor_data = result.scalars().all()
            
            # Convert to dict format
            historical_data = [
                {
                    'sensor_id': data.sensor_id,
                    'sensor_type': data.sensor_type,
                    'timestamp': data.timestamp.isoformat(),
                    'value': data.value,
                    'unit': data.unit,
                    'location': data.location,
                    'is_anomaly': data.is_anomaly or False
                }
                for data in sensor_data
            ]
            
            # Cache for 5 minutes
            await redis_service.cache_set(cache_key, historical_data, ttl=300)
            
            return historical_data
            
    except Exception as e:
        logger.error(f"Failed to get historical sensor data: {e}")
        return []


async def update_sensor_anomaly_status(sensor_data_id: int, detection_result: dict):
    """Update sensor data with anomaly detection results."""
    try:
        from app.core.database import async_session_maker
        async with async_session_maker() as db:
            query = select(SensorData).where(SensorData.id == sensor_data_id)
            result = await db.execute(query)
            sensor_data = result.scalar_one_or_none()
            
            if sensor_data:
                sensor_data.is_anomaly = detection_result['is_anomaly']
                sensor_data.anomaly_score = detection_result['anomaly_score']
                await db.commit()
                
    except Exception as e:
        logger.error(f"Failed to update sensor anomaly status: {e}")


async def create_anomaly_alert(sensor_data: dict, detection_result: dict):
    """Create anomaly alert."""
    try:
        from app.core.database import async_session_maker
        async with async_session_maker() as db:
            alert = AnomalyAlert(
                sensor_id=sensor_data['sensor_id'],
                alert_type='anomaly_detection',
                severity=detection_result['severity'],
                message=detection_result['message'],
                anomaly_score=detection_result['anomaly_score'],
                sensor_value=sensor_data['value'],
                metadata={
                    'sensor_type': sensor_data.get('sensor_type'),
                    'location': sensor_data.get('location'),
                    'detection_timestamp': detection_result.get('timestamp')
                }
            )
            
            db.add(alert)
            await db.commit()
            
            # Send alert to Kafka
            alert_data = {
                'alert_id': alert.id,
                'sensor_id': alert.sensor_id,
                'severity': alert.severity,
                'message': alert.message,
                'anomaly_score': alert.anomaly_score,
                'sensor_value': alert.sensor_value,
                'timestamp': alert.timestamp.isoformat()
            }
            
            await kafka_service.produce_anomaly_alert(alert_data)
            
            logger.info(f"Created anomaly alert for sensor {sensor_data['sensor_id']}")
            
    except Exception as e:
        logger.error(f"Failed to create anomaly alert: {e}")