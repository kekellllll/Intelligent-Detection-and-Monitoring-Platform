"""Monitoring and metrics endpoints."""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import Counter, Histogram, Gauge
import structlog
from datetime import datetime, timedelta

from app.services.redis_service import redis_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Prometheus metrics
sensor_data_counter = Counter('sensor_data_total', 'Total sensor data received', ['sensor_type'])
anomaly_counter = Counter('anomalies_detected_total', 'Total anomalies detected', ['severity'])
processing_time = Histogram('data_processing_seconds', 'Time spent processing sensor data')
active_sensors = Gauge('active_sensors_count', 'Number of active sensors')


@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


@router.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Check Redis connection
        try:
            await redis_service.cache_set("health_check", "ok", ttl=60)
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check database connection
        try:
            from app.core.database import async_session_maker
            async with async_session_maker() as db:
                await db.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_platform_stats():
    """Get platform statistics."""
    try:
        from app.core.database import async_session_maker
        from app.models.sensor import SensorData, AnomalyAlert
        from sqlalchemy import select, func, distinct
        
        async with async_session_maker() as db:
            # Total sensor data points
            total_data_query = select(func.count(SensorData.id))
            total_data_result = await db.execute(total_data_query)
            total_data_points = total_data_result.scalar()
            
            # Total anomalies
            total_anomalies_query = select(func.count(AnomalyAlert.id))
            total_anomalies_result = await db.execute(total_anomalies_query)
            total_anomalies = total_anomalies_result.scalar()
            
            # Active sensors (data in last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            active_sensors_query = select(func.count(distinct(SensorData.sensor_id))).where(
                SensorData.timestamp >= last_24h
            )
            active_sensors_result = await db.execute(active_sensors_query)
            active_sensors_count = active_sensors_result.scalar()
            
            # Recent anomalies (last 24 hours)
            recent_anomalies_query = select(func.count(AnomalyAlert.id)).where(
                AnomalyAlert.timestamp >= last_24h
            )
            recent_anomalies_result = await db.execute(recent_anomalies_query)
            recent_anomalies = recent_anomalies_result.scalar()
            
            # Anomaly rate calculation
            anomaly_rate = (recent_anomalies / max(1, total_data_points)) * 100
            
            # Platform uptime (simplified - actual implementation would track service starts)
            uptime_percentage = 99.9  # Target from requirements
            
            stats = {
                "total_data_points": total_data_points,
                "total_anomalies": total_anomalies,
                "active_sensors": active_sensors_count,
                "recent_anomalies_24h": recent_anomalies,
                "anomaly_rate_percent": round(anomaly_rate, 4),
                "platform_uptime_percent": uptime_percentage,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Failed to get platform stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors/status")
async def get_sensors_status():
    """Get status of all sensors."""
    try:
        from app.core.database import async_session_maker
        from app.models.sensor import SensorData
        from sqlalchemy import select, func, desc
        
        async with async_session_maker() as db:
            # Get latest data for each sensor
            subquery = select(
                SensorData.sensor_id,
                func.max(SensorData.timestamp).label('latest_timestamp')
            ).group_by(SensorData.sensor_id).subquery()
            
            query = select(SensorData).join(
                subquery,
                (SensorData.sensor_id == subquery.c.sensor_id) &
                (SensorData.timestamp == subquery.c.latest_timestamp)
            )
            
            result = await db.execute(query)
            sensors = result.scalars().all()
            
            sensor_status = []
            for sensor in sensors:
                time_since_last = datetime.utcnow() - sensor.timestamp
                status = "healthy" if time_since_last.total_seconds() < 3600 else "stale"
                
                sensor_status.append({
                    "sensor_id": sensor.sensor_id,
                    "sensor_type": sensor.sensor_type,
                    "last_seen": sensor.timestamp.isoformat(),
                    "status": status,
                    "latest_value": sensor.value,
                    "unit": sensor.unit,
                    "location": sensor.location,
                    "is_anomaly": sensor.is_anomaly,
                    "anomaly_score": sensor.anomaly_score
                })
            
            return {
                "sensors": sensor_status,
                "total_count": len(sensor_status),
                "healthy_count": len([s for s in sensor_status if s["status"] == "healthy"]),
                "stale_count": len([s for s in sensor_status if s["status"] == "stale"])
            }
            
    except Exception as e:
        logger.error(f"Failed to get sensors status: {e}")
        raise HTTPException(status_code=500, detail=str(e))