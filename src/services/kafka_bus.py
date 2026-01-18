"""Kafka Message Bus Integration for ISR Platform.

Provides real-time event streaming for sensor data fusion,
alerts, and inter-service communication.
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
    from aiokafka.errors import KafkaError
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    AIOKafkaProducer = None
    AIOKafkaConsumer = None
    KafkaError = Exception

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


class KafkaMessageBus:
    """Kafka message bus for ISR platform.
    
    In production, this would use aiokafka for real Kafka connectivity.
    This implementation provides an in-memory message bus for development/testing.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        consumer_group: str = "isr-platform",
    ) -> None:
        """Initialize Kafka message bus."""
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self._connected = False
        self._producer_started = False
        self._consumer_started = False
        
        # In-memory queue for development
        self._message_queues: dict[MessageTopic, asyncio.Queue[KafkaMessage]] = {}
        self._handlers: dict[MessageTopic, list[MessageHandler]] = {}
        self._consumer_tasks: list[asyncio.Task] = []
        
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
            
        logger.info(f"Connecting to Kafka at {self.bootstrap_servers}")
        
        # Initialize queues for all topics
        for topic in MessageTopic:
            self._message_queues[topic] = asyncio.Queue()
            self._handlers[topic] = []
        
        self._connected = True
        logger.info("Kafka connection established (in-memory mode)")

    async def disconnect(self) -> None:
        """Disconnect from Kafka cluster."""
        if not self._connected:
            return
            
        logger.info("Disconnecting from Kafka")
        
        # Cancel consumer tasks
        for task in self._consumer_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._consumer_tasks.clear()
        self._connected = False
        logger.info("Kafka disconnected")

    async def start_producer(self) -> None:
        """Start the Kafka producer."""
        if not self._connected:
            await self.connect()
        
        self._producer_started = True
        logger.info("Kafka producer started")

    async def start_consumer(self, topics: list[MessageTopic] | None = None) -> None:
        """Start consuming from specified topics."""
        if not self._connected:
            await self.connect()
        
        topics_to_consume = topics or list(MessageTopic)
        
        for topic in topics_to_consume:
            task = asyncio.create_task(self._consume_topic(topic))
            self._consumer_tasks.append(task)
        
        self._consumer_started = True
        logger.info(f"Kafka consumer started for {len(topics_to_consume)} topics")

    async def _consume_topic(self, topic: MessageTopic) -> None:
        """Consume messages from a single topic."""
        queue = self._message_queues[topic]
        
        while True:
            try:
                message = await queue.get()
                handlers = self._handlers.get(topic, [])
                
                for handler in handlers:
                    try:
                        await handler(message)
                        self._stats["messages_received"] += 1
                    except Exception as e:
                        logger.error(f"Handler error for {topic}: {e}")
                        self._stats["errors"] += 1
                
                queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer error for {topic}: {e}")
                self._stats["errors"] += 1

    async def publish(
        self,
        topic: MessageTopic,
        payload: dict[str, Any],
        key: str | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        headers: dict[str, str] | None = None,
    ) -> KafkaMessage:
        """Publish a message to a topic."""
        if not self._producer_started:
            await self.start_producer()
        
        message = KafkaMessage(
            message_id=uuid4(),
            topic=topic,
            key=key,
            payload=payload,
            priority=priority,
            headers=headers or {},
        )
        
        # Add to queue
        queue = self._message_queues.get(topic)
        if queue:
            await queue.put(message)
        
        # Store in history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        self._stats["messages_sent"] += 1
        logger.debug(f"Published message to {topic.value}: {message.message_id}")
        
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

    async def publish_threat_score(
        self,
        entity_id: UUID | None,
        event_id: UUID | None,
        score: float,
        category: str,
        factors: dict[str, float],
    ) -> KafkaMessage:
        """Publish a threat score calculation."""
        return await self.publish(
            topic=MessageTopic.ANALYTICS_THREAT,
            payload={
                "entity_id": str(entity_id) if entity_id else None,
                "event_id": str(event_id) if event_id else None,
                "score": score,
                "category": category,
                "factors": factors,
            },
            key=str(entity_id or event_id),
            priority=MessagePriority.HIGH if score > 70 else MessagePriority.NORMAL,
        )

    async def publish_anomaly(
        self,
        anomaly_id: UUID,
        domain: str,
        severity: str,
        score: float,
        details: dict[str, Any],
    ) -> KafkaMessage:
        """Publish an anomaly detection."""
        return await self.publish(
            topic=MessageTopic.ANALYTICS_ANOMALY,
            payload={
                "anomaly_id": str(anomaly_id),
                "domain": domain,
                "severity": severity,
                "score": score,
                "details": details,
            },
            key=str(anomaly_id),
            priority=MessagePriority.HIGH if severity in ["HIGH", "CRITICAL"] else MessagePriority.NORMAL,
        )

    async def publish_entity_update(
        self,
        entity_id: UUID,
        entity_type: str,
        action: str,  # "created" or "updated"
        data: dict[str, Any],
    ) -> KafkaMessage:
        """Publish an entity update."""
        topic = MessageTopic.ENTITIES_CREATED if action == "created" else MessageTopic.ENTITIES_UPDATED
        
        return await self.publish(
            topic=topic,
            payload={
                "entity_id": str(entity_id),
                "entity_type": entity_type,
                "action": action,
                "data": data,
            },
            key=str(entity_id),
        )

    async def publish_event_update(
        self,
        event_id: UUID,
        event_type: str,
        action: str,
        data: dict[str, Any],
    ) -> KafkaMessage:
        """Publish an event update."""
        topic = MessageTopic.EVENTS_CREATED if action == "created" else MessageTopic.EVENTS_UPDATED
        
        return await self.publish(
            topic=topic,
            payload={
                "event_id": str(event_id),
                "event_type": event_type,
                "action": action,
                "data": data,
            },
            key=str(event_id),
        )

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
            },
            key=sensor_id,
        )

    async def publish_audit_log(
        self,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict[str, Any] | None = None,
    ) -> KafkaMessage:
        """Publish an audit log entry."""
        return await self.publish(
            topic=MessageTopic.SYSTEM_AUDIT,
            payload={
                "user_id": str(user_id) if user_id else None,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
            },
            priority=MessagePriority.LOW,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self._stats,
            "connected": self._connected,
            "producer_started": self._producer_started,
            "consumer_started": self._consumer_started,
            "topic_count": len(MessageTopic),
            "handler_counts": {
                topic.value: len(handlers)
                for topic, handlers in self._handlers.items()
                if handlers
            },
            "queue_sizes": {
                topic.value: queue.qsize()
                for topic, queue in self._message_queues.items()
                if queue.qsize() > 0
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
_kafka_bus: KafkaMessageBus | None = None


def get_kafka_bus() -> KafkaMessageBus:
    """Get the Kafka message bus instance."""
    global _kafka_bus
    if _kafka_bus is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _kafka_bus = KafkaMessageBus(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group=settings.kafka_consumer_group,
        )
    return _kafka_bus
