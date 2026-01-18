"""Real Kafka Message Bus Implementation for ISR Platform.

This is a complete rewrite using aiokafka for production-grade Kafka connectivity.
Includes fallback to in-memory mode if Kafka is unavailable.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Coroutine
from uuid import UUID, uuid4

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from aiokafka.errors import KafkaError, KafkaConnectionError
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    AIOKafkaProducer = None
    AIOKafkaConsumer = None
    KafkaError = Exception
    KafkaConnectionError = Exception

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class MessageTopic(str, Enum):
    """Kafka topics for ISR platform."""
    # Sensor data ingestion
    SENSOR_SATELLITE = "isr.sensor.satellite"
    SENSOR_UAV = "isr.sensor.uav"
    SENSOR_GROUND = "isr.sensor.ground"
    SENSOR_CYBER = "isr.sensor.cyber"
    
    # OSINT and social media
    OSINT_SOCIAL = "isr.osint.social"
    OSINT_NEWS = "isr.osint.news"
    OSINT_RADIO = "isr.osint.radio"
    
    # Analytics outputs
    ANALYTICS_THREAT = "isr.analytics.threat"
    ANALYTICS_ANOMALY = "isr.analytics.anomaly"
    ANALYTICS_NARRATIVE = "isr.analytics.narrative"
    
    # Alerts and notifications
    ALERTS_NEW = "isr.alerts.new"
    ALERTS_UPDATED = "isr.alerts.updated"
    ALERTS_RESOLVED = "isr.alerts.resolved"
    
    # Entity and event updates
    ENTITIES_CREATED = "isr.entities.created"
    ENTITIES_UPDATED = "isr.entities.updated"
    EVENTS_CREATED = "isr.events.created"
    EVENTS_UPDATED = "isr.events.updated"
    
    # Simulation events
    SIMULATION_STATE = "isr.simulation.state"
    SIMULATION_EVENTS = "isr.simulation.events"
    
    # System events
    SYSTEM_AUDIT = "isr.system.audit"
    SYSTEM_HEALTH = "isr.system.health"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class KafkaMessage:
    """Kafka message wrapper."""
    message_id: UUID
    topic: MessageTopic
    key: str | None
    payload: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=utcnow)
    headers: dict[str, str] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps({
            "message_id": str(self.message_id),
            "topic": self.topic.value,
            "key": self.key,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "headers": self.headers,
        })
    
    @classmethod
    def from_json(cls, data: str) -> "KafkaMessage":
        """Deserialize message from JSON."""
        obj = json.loads(data)
        return cls(
            message_id=UUID(obj["message_id"]),
            topic=MessageTopic(obj["topic"]),
            key=obj.get("key"),
            payload=obj["payload"],
            priority=MessagePriority(obj.get("priority", "NORMAL")),
            timestamp=datetime.fromisoformat(obj["timestamp"]),
            headers=obj.get("headers", {}),
        )


# Type alias for message handlers
MessageHandler = Callable[[KafkaMessage], Coroutine[Any, Any, None]]


class RealKafkaMessageBus:
    """Production-grade Kafka message bus using aiokafka.
    
    Features:
    - Real Kafka connectivity with aiokafka
    - Automatic fallback to in-memory mode
    - Graceful error handling
    - Message acknowledgment
    - Consumer groups
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        consumer_group: str = "isr-platform",
        use_real_kafka: bool = True,
    ) -> None:
        """Initialize Kafka message bus."""
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.use_real_kafka = use_real_kafka and AIOKAFKA_AVAILABLE
        
        # Real Kafka components
        self._producer: AIOKafkaProducer | None = None
        self._consumers: dict[MessageTopic, AIOKafkaConsumer] = {}
        self._consumer_tasks: list[asyncio.Task] = []
        
        # Message handlers
        self._handlers: dict[MessageTopic, list[MessageHandler]] = {}
        
        # In-memory fallback
        self._message_queues: dict[MessageTopic, asyncio.Queue[KafkaMessage]] = {}
        self._fallback_consumer_tasks: list[asyncio.Task] = []
        
        # State tracking
        self._connected = False
        self._producer_started = False
        self._consumer_started = False
        
        # Message history for debugging
        self._message_history: list[KafkaMessage] = []
        self._max_history = 1000
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
        }

    async def connect(self) -> None:
        """Connect to Kafka cluster."""
        if self._connected:
            return

        logger.info(
            f"Connecting to Kafka at {self.bootstrap_servers} "
            f"(real_kafka={self.use_real_kafka}, aiokafka_available={AIOKAFKA_AVAILABLE})"
        )

        if self.use_real_kafka:
            try:
                # Create real Kafka producer with production settings
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    compression_type='gzip',
                    acks='all',  # Wait for all replicas
                    enable_idempotence=True,  # Exactly-once semantics
                    max_in_flight_requests_per_connection=5,
                    retries=10,
                    request_timeout_ms=30000,
                )
                await self._producer.start()
                logger.info("✓ Real Kafka producer started successfully")
                self._connected = True
                self._producer_started = True
            except Exception as e:
                logger.warning(f"Failed to connect to real Kafka: {e}")
                logger.info("→ Falling back to in-memory mode")
                self.use_real_kafka = False
                self._producer = None
        
        if not self.use_real_kafka:
            # Initialize in-memory queues
            for topic in MessageTopic:
                self._message_queues[topic] = asyncio.Queue()
                self._handlers[topic] = []
            
            self._connected = True
            logger.info("✓ In-memory Kafka mode initialized")

    async def disconnect(self) -> None:
        """Disconnect from Kafka cluster."""
        if not self._connected:
            return

        logger.info("Disconnecting from Kafka...")

        if self.use_real_kafka:
            # Stop all consumer tasks
            for task in self._consumer_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Close all consumers
            for consumer in self._consumers.values():
                try:
                    await consumer.stop()
                except Exception as e:
                    logger.error(f"Error stopping consumer: {e}")
            
            # Close producer
            if self._producer:
                try:
                    await self._producer.stop()
                except Exception as e:
                    logger.error(f"Error stopping producer: {e}")
            
            self._consumer_tasks.clear()
            self._consumers.clear()
        else:
            # Stop in-memory consumer tasks
            for task in self._fallback_consumer_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self._fallback_consumer_tasks.clear()

        self._connected = False
        self._producer_started = False
        self._consumer_started = False
        logger.info("✓ Kafka disconnected")

    async def start_consumer(self, topics: list[MessageTopic] | None = None) -> None:
        """Start consuming from specified topics."""
        if not self._connected:
            await self.connect()
        
        topics_to_consume = topics or list(MessageTopic)
        
        if self.use_real_kafka:
            await self._start_real_consumers(topics_to_consume)
        else:
            await self._start_fallback_consumers(topics_to_consume)
        
        self._consumer_started = True
        logger.info(f"✓ Kafka consumer started for {len(topics_to_consume)} topics")

    async def _start_real_consumers(self, topics: list[MessageTopic]) -> None:
        """Start real Kafka consumers."""
        for topic in topics:
            try:
                consumer = AIOKafkaConsumer(
                    topic.value,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.consumer_group,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    key_deserializer=lambda k: k.decode('utf-8') if k else None,
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    max_poll_records=100,
                )
                await consumer.start()
                self._consumers[topic] = consumer
                
                # Start consumer task
                task = asyncio.create_task(self._consume_real_topic(topic, consumer))
                self._consumer_tasks.append(task)
                
                logger.info(f"  → Started consumer for {topic.value}")
            except Exception as e:
                logger.error(f"Failed to start consumer for {topic.value}: {e}")

    async def _consume_real_topic(self, topic: MessageTopic, consumer: AIOKafkaConsumer) -> None:
        """Consume messages from a real Kafka topic."""
        try:
            async for msg in consumer:
                try:
                    # Reconstruct KafkaMessage
                    message = KafkaMessage(
                        message_id=UUID(msg.value["message_id"]),
                        topic=topic,
                        key=msg.key,
                        payload=msg.value["payload"],
                        priority=MessagePriority(msg.value.get("priority", "NORMAL")),
                        timestamp=datetime.fromisoformat(msg.value["timestamp"]),
                        headers=msg.value.get("headers", {}),
                    )
                    
                    # Store in history
                    self._message_history.append(message)
                    if len(self._message_history) > self._max_history:
                        self._message_history.pop(0)
                    
                    # Call handlers
                    handlers = self._handlers.get(topic, [])
                    for handler in handlers:
                        try:
                            await handler(message)
                            self._stats["messages_received"] += 1
                        except Exception as e:
                            logger.error(f"Handler error for {topic.value}: {e}")
                            self._stats["errors"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing message from {topic.value}: {e}")
                    self._stats["errors"] += 1
        
        except asyncio.CancelledError:
            logger.info(f"Consumer task cancelled for {topic.value}")
        except Exception as e:
            logger.error(f"Consumer error for {topic.value}: {e}")

    async def _start_fallback_consumers(self, topics: list[MessageTopic]) -> None:
        """Start in-memory fallback consumers."""
        for topic in topics:
            if topic not in self._handlers:
                self._handlers[topic] = []
            task = asyncio.create_task(self._consume_fallback_topic(topic))
            self._fallback_consumer_tasks.append(task)

    async def _consume_fallback_topic(self, topic: MessageTopic) -> None:
        """Consume messages from in-memory queue."""
        queue = self._message_queues[topic]
        
        try:
            while True:
                message = await queue.get()
                handlers = self._handlers.get(topic, [])
                
                for handler in handlers:
                    try:
                        await handler(message)
                        self._stats["messages_received"] += 1
                    except Exception as e:
                        logger.error(f"Handler error for {topic.value}: {e}")
                        self._stats["errors"] += 1
                
                queue.task_done()
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Fallback consumer error for {topic.value}: {e}")

    async def publish(
        self,
        topic: MessageTopic,
        payload: dict[str, Any],
        key: str | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        headers: dict[str, str] | None = None,
    ) -> KafkaMessage:
        """Publish a message to a topic."""
        if not self._connected:
            await self.connect()
        
        message = KafkaMessage(
            message_id=uuid4(),
            topic=topic,
            key=key,
            payload=payload,
            priority=priority,
            headers=headers or {},
        )
        
        # Store in history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        if self.use_real_kafka and self._producer:
            try:
                # Send to real Kafka
                message_dict = {
                    "message_id": str(message.message_id),
                    "topic": topic.value,
                    "key": key,
                    "payload": payload,
                    "priority": priority.value,
                    "timestamp": message.timestamp.isoformat(),
                    "headers": headers or {},
                }
                
                await self._producer.send_and_wait(
                    topic.value,
                    value=message_dict,
                    key=key,
                )
                
                self._stats["messages_sent"] += 1
                logger.debug(f"Published to Kafka: {topic.value} [{message.message_id}]")
            
            except Exception as e:
                logger.error(f"Error publishing to Kafka: {e}")
                self._stats["errors"] += 1
                raise
        else:
            # Use in-memory queue
            queue = self._message_queues.get(topic)
            if queue:
                await queue.put(message)
            
            self._stats["messages_sent"] += 1
            logger.debug(f"Published to queue: {topic.value} [{message.message_id}]")
        
        return message

    def subscribe(self, topic: MessageTopic, handler: MessageHandler) -> None:
        """Subscribe a handler to a topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        
        self._handlers[topic].append(handler)
        logger.info(f"Subscribed handler to {topic.value}")

    def unsubscribe(self, topic: MessageTopic, handler: MessageHandler) -> None:
        """Unsubscribe a handler from a topic."""
        if topic in self._handlers and handler in self._handlers[topic]:
            self._handlers[topic].remove(handler)
            logger.info(f"Unsubscribed handler from {topic.value}")

    # Convenience methods for common message types
    
    async def publish_sensor_data(
        self,
        sensor_type: str,  # "satellite", "uav", "ground", "cyber"
        sensor_id: str,
        data: dict[str, Any],
    ) -> KafkaMessage:
        """Publish sensor data."""
        topic_map = {
            "satellite": MessageTopic.SENSOR_SATELLITE,
            "uav": MessageTopic.SENSOR_UAV,
            "ground": MessageTopic.SENSOR_GROUND,
            "cyber": MessageTopic.SENSOR_CYBER,
        }
        topic = topic_map.get(sensor_type, MessageTopic.SENSOR_GROUND)
        
        return await self.publish(
            topic=topic,
            payload={
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "data": data,
                "timestamp": utcnow().isoformat(),
            },
            key=sensor_id,
        )

    async def publish_osint_data(
        self,
        source_type: str,  # "social", "news", "radio"
        source_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> KafkaMessage:
        """Publish OSINT data."""
        topic_map = {
            "social": MessageTopic.OSINT_SOCIAL,
            "news": MessageTopic.OSINT_NEWS,
            "radio": MessageTopic.OSINT_RADIO,
        }
        topic = topic_map.get(source_type, MessageTopic.OSINT_NEWS)
        
        return await self.publish(
            topic=topic,
            payload={
                "source_id": source_id,
                "source_type": source_type,
                "content": content,
                "metadata": metadata,
                "timestamp": utcnow().isoformat(),
            },
            key=source_id,
        )

    async def publish_alert(
        self,
        alert_id: UUID,
        alert_type: str,
        severity: str,
        title: str,
        details: dict[str, Any] | None = None,
    ) -> KafkaMessage:
        """Publish a new alert."""
        priority = MessagePriority.CRITICAL if severity == "CRITICAL" else MessagePriority.HIGH
        
        return await self.publish(
            topic=MessageTopic.ALERTS_NEW,
            payload={
                "alert_id": str(alert_id),
                "alert_type": alert_type,
                "severity": severity,
                "title": title,
                "details": details or {},
            },
            key=str(alert_id),
            priority=priority,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self._stats,
            "mode": "real_kafka" if self.use_real_kafka else "in_memory",
            "connected": self._connected,
            "producer_started": self._producer_started,
            "consumer_started": self._consumer_started,
            "topic_count": len(MessageTopic),
            "active_consumers": len(self._consumers) if self.use_real_kafka else len(self._fallback_consumer_tasks),
            "handler_counts": {
                topic.value: len(handlers)
                for topic, handlers in self._handlers.items()
                if handlers
            },
        }

    def get_message_history(
        self,
        topic: MessageTopic | None = None,
        limit: int = 100,
    ) -> list[KafkaMessage]:
        """Get recent message history."""
        messages = self._message_history
        
        if topic:
            messages = [m for m in messages if m.topic == topic]
        
        return messages[-limit:]


# Global instance
_kafka_bus: RealKafkaMessageBus | None = None


def get_kafka_bus() -> RealKafkaMessageBus:
    """Get the Kafka message bus instance."""
    global _kafka_bus
    if _kafka_bus is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _kafka_bus = RealKafkaMessageBus(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group=settings.kafka_consumer_group,
        )
    return _kafka_bus
