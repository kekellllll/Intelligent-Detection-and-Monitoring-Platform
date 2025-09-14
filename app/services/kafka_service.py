"""Kafka service for high-throughput message streaming."""
import json
import asyncio
from typing import Dict, Any, Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class KafkaService:
    """Kafka service for high-throughput sensor data streaming."""
    
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self.consumers: Dict[str, KafkaConsumer] = {}
        self.settings = get_settings()
        self.running = False
    
    async def initialize(self) -> None:
        """Initialize Kafka producer."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                retry_backoff_ms=1000,
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10,  # Wait up to 10ms to batch messages
            )
            logger.info("Kafka producer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    async def close(self) -> None:
        """Close Kafka connections."""
        self.running = False
        
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
        
        for topic, consumer in self.consumers.items():
            consumer.close()
            logger.info(f"Kafka consumer for topic {topic} closed")
        
        self.consumers.clear()
    
    async def produce_sensor_data(self, sensor_data: Dict[str, Any]) -> None:
        """Produce sensor data to Kafka topic."""
        if not self.producer:
            await self.initialize()
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in sensor_data:
                from datetime import datetime
                sensor_data['timestamp'] = datetime.utcnow().isoformat()
            
            future = self.producer.send(
                topic=self.settings.KAFKA_SENSOR_TOPIC,
                key=sensor_data.get('sensor_id'),
                value=sensor_data
            )
            
            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)
            logger.debug(
                f"Sent sensor data to topic {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
        except KafkaError as e:
            logger.error(f"Failed to send sensor data to Kafka: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending sensor data: {e}")
            raise
    
    async def produce_anomaly_alert(self, alert_data: Dict[str, Any]) -> None:
        """Produce anomaly alert to Kafka topic."""
        if not self.producer:
            await self.initialize()
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in alert_data:
                from datetime import datetime
                alert_data['timestamp'] = datetime.utcnow().isoformat()
            
            future = self.producer.send(
                topic=self.settings.KAFKA_ANOMALY_TOPIC,
                key=alert_data.get('sensor_id'),
                value=alert_data
            )
            
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Sent anomaly alert to topic {record_metadata.topic} "
                f"for sensor {alert_data.get('sensor_id')}"
            )
        except KafkaError as e:
            logger.error(f"Failed to send anomaly alert to Kafka: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending anomaly alert: {e}")
            raise
    
    async def consume_sensor_data(self, message_handler: Callable[[Dict[str, Any]], None]) -> None:
        """Consume sensor data from Kafka topic."""
        try:
            consumer = KafkaConsumer(
                self.settings.KAFKA_SENSOR_TOPIC,
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                group_id='sensor-data-processors',
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000,
            )
            
            self.consumers[self.settings.KAFKA_SENSOR_TOPIC] = consumer
            self.running = True
            
            logger.info(f"Started consuming from topic {self.settings.KAFKA_SENSOR_TOPIC}")
            
            while self.running:
                try:
                    message_batch = consumer.poll(timeout_ms=1000)
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            try:
                                await asyncio.get_event_loop().run_in_executor(
                                    None, message_handler, message.value
                                )
                            except Exception as e:
                                logger.error(f"Error processing message: {e}")
                    
                    await asyncio.sleep(0.1)  # Prevent tight loop
                except Exception as e:
                    logger.error(f"Error in consumer loop: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise


# Global Kafka service instance
kafka_service = KafkaService()