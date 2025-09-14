"""GraphQL API implementation using Strawberry."""
import strawberry
from typing import List, Optional
from datetime import datetime
from strawberry.fastapi import GraphQLRouter
import structlog

from app.core.database import async_session_maker
from app.models.sensor import SensorData, AnomalyAlert
from sqlalchemy import select, desc

logger = structlog.get_logger(__name__)


@strawberry.type
class SensorDataType:
    """GraphQL type for sensor data."""
    id: int
    sensor_id: str
    sensor_type: str
    timestamp: datetime
    value: float
    unit: str
    location: Optional[str]
    is_anomaly: bool
    anomaly_score: Optional[float]


@strawberry.type
class AnomalyAlertType:
    """GraphQL type for anomaly alerts."""
    id: int
    sensor_id: str
    alert_type: str
    severity: str
    message: str
    anomaly_score: float
    sensor_value: float
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime]


@strawberry.type
class SensorStatsType:
    """GraphQL type for sensor statistics."""
    sensor_id: str
    total_readings: int
    avg_value: float
    min_value: float
    max_value: float
    anomaly_count: int
    last_reading: datetime


@strawberry.type
class Query:
    """GraphQL queries for monitoring system data."""
    
    @strawberry.field
    async def sensor_data(
        self,
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        limit: int = 100
    ) -> List[SensorDataType]:
        """Get sensor data with optional filtering."""
        try:
            async with async_session_maker() as db:
                query = select(SensorData).order_by(desc(SensorData.timestamp))
                
                if sensor_id:
                    query = query.where(SensorData.sensor_id == sensor_id)
                if sensor_type:
                    query = query.where(SensorData.sensor_type == sensor_type)
                
                query = query.limit(limit)
                
                result = await db.execute(query)
                sensor_data = result.scalars().all()
                
                return [
                    SensorDataType(
                        id=data.id,
                        sensor_id=data.sensor_id,
                        sensor_type=data.sensor_type,
                        timestamp=data.timestamp,
                        value=data.value,
                        unit=data.unit,
                        location=data.location,
                        is_anomaly=data.is_anomaly or False,
                        anomaly_score=data.anomaly_score
                    )
                    for data in sensor_data
                ]
        except Exception as e:
            logger.error(f"GraphQL sensor_data query failed: {e}")
            return []
    
    @strawberry.field
    async def anomaly_alerts(
        self,
        sensor_id: Optional[str] = None,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[AnomalyAlertType]:
        """Get anomaly alerts with optional filtering."""
        try:
            async with async_session_maker() as db:
                query = select(AnomalyAlert).order_by(desc(AnomalyAlert.timestamp))
                
                if sensor_id:
                    query = query.where(AnomalyAlert.sensor_id == sensor_id)
                if severity:
                    query = query.where(AnomalyAlert.severity == severity)
                if resolved is not None:
                    query = query.where(AnomalyAlert.resolved == resolved)
                
                query = query.limit(limit)
                
                result = await db.execute(query)
                alerts = result.scalars().all()
                
                return [
                    AnomalyAlertType(
                        id=alert.id,
                        sensor_id=alert.sensor_id,
                        alert_type=alert.alert_type,
                        severity=alert.severity,
                        message=alert.message,
                        anomaly_score=alert.anomaly_score,
                        sensor_value=alert.sensor_value,
                        timestamp=alert.timestamp,
                        resolved=alert.resolved,
                        resolved_at=alert.resolved_at
                    )
                    for alert in alerts
                ]
        except Exception as e:
            logger.error(f"GraphQL anomaly_alerts query failed: {e}")
            return []
    
    @strawberry.field
    async def sensor_stats(self, sensor_id: str) -> Optional[SensorStatsType]:
        """Get statistics for a specific sensor."""
        try:
            async with async_session_maker() as db:
                from sqlalchemy import func
                
                # Get sensor statistics
                stats_query = select(
                    func.count(SensorData.id).label('total_readings'),
                    func.avg(SensorData.value).label('avg_value'),
                    func.min(SensorData.value).label('min_value'),
                    func.max(SensorData.value).label('max_value'),
                    func.max(SensorData.timestamp).label('last_reading')
                ).where(SensorData.sensor_id == sensor_id)
                
                stats_result = await db.execute(stats_query)
                stats = stats_result.first()
                
                if not stats or stats.total_readings == 0:
                    return None
                
                # Get anomaly count
                anomaly_query = select(func.count(AnomalyAlert.id)).where(
                    AnomalyAlert.sensor_id == sensor_id
                )
                anomaly_result = await db.execute(anomaly_query)
                anomaly_count = anomaly_result.scalar()
                
                return SensorStatsType(
                    sensor_id=sensor_id,
                    total_readings=stats.total_readings,
                    avg_value=float(stats.avg_value),
                    min_value=float(stats.min_value),
                    max_value=float(stats.max_value),
                    anomaly_count=anomaly_count,
                    last_reading=stats.last_reading
                )
                
        except Exception as e:
            logger.error(f"GraphQL sensor_stats query failed: {e}")
            return None


@strawberry.type
class Mutation:
    """GraphQL mutations for monitoring system operations."""
    
    @strawberry.field
    async def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an anomaly alert."""
        try:
            async with async_session_maker() as db:
                query = select(AnomalyAlert).where(AnomalyAlert.id == alert_id)
                result = await db.execute(query)
                alert = result.scalar_one_or_none()
                
                if not alert:
                    return False
                
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                
                await db.commit()
                
                logger.info(f"Resolved alert {alert_id} via GraphQL")
                return True
                
        except Exception as e:
            logger.error(f"GraphQL resolve_alert mutation failed: {e}")
            return False


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL app
graphql_app = GraphQLRouter(schema)