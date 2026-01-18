"""Tests for Kafka message bus service."""

import pytest
import asyncio
from uuid import uuid4

from src.services.kafka_bus import (
    KafkaMessage,
    KafkaMessageBus,
    MessagePriority,
    MessageTopic,
)


@pytest.fixture
def bus():
    """Create Kafka message bus instance."""
    return KafkaMessageBus()


class TestKafkaMessageBus:
    """Tests for KafkaMessageBus."""

    @pytest.mark.asyncio
    async def test_connect(self, bus):
        """Test connecting to Kafka."""
        await bus.connect()
        assert bus._connected is True
        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_message(self, bus):
        """Test publishing a message."""
        await bus.connect()

        message = await bus.publish(
            topic=MessageTopic.ALERTS_NEW,
            payload={"test": "data"},
            key="test-key",
        )

        assert message is not None
        assert message.topic == MessageTopic.ALERTS_NEW
        assert message.payload == {"test": "data"}
        assert bus._stats["messages_sent"] == 1

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_alert(self, bus):
        """Test publishing an alert."""
        await bus.connect()

        message = await bus.publish_alert(
            alert_id=uuid4(),
            alert_type="THREAT",
            severity="HIGH",
            title="Test Alert",
            details={"location": "Kabul"},
        )

        assert message.topic == MessageTopic.ALERTS_NEW
        assert message.priority == MessagePriority.HIGH
        assert "alert_id" in message.payload

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_critical_alert(self, bus):
        """Test that critical alerts get critical priority."""
        await bus.connect()

        message = await bus.publish_alert(
            alert_id=uuid4(),
            alert_type="THREAT",
            severity="CRITICAL",
            title="Critical Alert",
        )

        assert message.priority == MessagePriority.CRITICAL

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_threat_score(self, bus):
        """Test publishing a threat score."""
        await bus.connect()

        entity_id = uuid4()
        message = await bus.publish_threat_score(
            entity_id=entity_id,
            event_id=None,
            score=85.5,
            category="CRITICAL",
            factors={"credibility": 80, "impact": 90},
        )

        assert message.topic == MessageTopic.ANALYTICS_THREAT
        assert message.priority == MessagePriority.HIGH  # score > 70
        assert message.payload["score"] == 85.5

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_anomaly(self, bus):
        """Test publishing an anomaly."""
        await bus.connect()

        message = await bus.publish_anomaly(
            anomaly_id=uuid4(),
            domain="GEO_MOVEMENT",
            severity="HIGH",
            score=0.92,
            details={"location": "Border region"},
        )

        assert message.topic == MessageTopic.ANALYTICS_ANOMALY
        assert message.priority == MessagePriority.HIGH

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_sensor_data(self, bus):
        """Test publishing sensor data."""
        await bus.connect()

        for sensor_type, expected_topic in [
            ("satellite", MessageTopic.SENSOR_SATELLITE),
            ("uav", MessageTopic.SENSOR_UAV),
            ("ground", MessageTopic.SENSOR_GROUND),
            ("cyber", MessageTopic.SENSOR_CYBER),
        ]:
            message = await bus.publish_sensor_data(
                sensor_type=sensor_type,
                sensor_id=f"sensor-{sensor_type}-001",
                data={"reading": 123},
            )
            assert message.topic == expected_topic

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_subscribe_handler(self, bus):
        """Test subscribing a handler to a topic."""
        received_messages = []

        async def handler(msg: KafkaMessage):
            received_messages.append(msg)

        await bus.connect()
        bus.subscribe(MessageTopic.ALERTS_NEW, handler)

        assert len(bus._handlers[MessageTopic.ALERTS_NEW]) == 1

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_unsubscribe_handler(self, bus):
        """Test unsubscribing a handler."""
        async def handler(msg: KafkaMessage):
            pass

        await bus.connect()
        bus.subscribe(MessageTopic.ALERTS_NEW, handler)
        bus.unsubscribe(MessageTopic.ALERTS_NEW, handler)

        assert len(bus._handlers[MessageTopic.ALERTS_NEW]) == 0

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_get_stats(self, bus):
        """Test getting message bus statistics."""
        await bus.connect()
        await bus.publish(MessageTopic.ALERTS_NEW, {"test": 1})
        await bus.publish(MessageTopic.ALERTS_NEW, {"test": 2})

        stats = bus.get_stats()

        assert stats["messages_sent"] == 2
        assert stats["connected"] is True

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_message_history(self, bus):
        """Test getting message history."""
        await bus.connect()

        for i in range(5):
            await bus.publish(MessageTopic.ALERTS_NEW, {"index": i})

        history = bus.get_message_history(topic=MessageTopic.ALERTS_NEW)

        assert len(history) == 5

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_audit_log_publishing(self, bus):
        """Test publishing audit logs."""
        await bus.connect()

        message = await bus.publish_audit_log(
            user_id=uuid4(),
            action="CREATE",
            resource_type="entity",
            resource_id="123",
            details={"name": "Test Entity"},
        )

        assert message.topic == MessageTopic.SYSTEM_AUDIT
        assert message.priority == MessagePriority.LOW

        await bus.disconnect()


class TestKafkaMessage:
    """Tests for KafkaMessage serialization."""

    def test_message_to_json(self):
        """Test serializing message to JSON."""
        message = KafkaMessage(
            message_id=uuid4(),
            topic=MessageTopic.ALERTS_NEW,
            key="test-key",
            payload={"data": "value"},
        )

        json_str = message.to_json()

        assert "message_id" in json_str
        assert "isr.alerts.new" in json_str  # Topic value, not enum name
        assert "test-key" in json_str

    def test_message_from_json(self):
        """Test deserializing message from JSON."""
        original = KafkaMessage(
            message_id=uuid4(),
            topic=MessageTopic.ALERTS_NEW,
            key="test-key",
            payload={"data": "value"},
            priority=MessagePriority.HIGH,
        )

        json_str = original.to_json()
        restored = KafkaMessage.from_json(json_str)

        assert restored.message_id == original.message_id
        assert restored.topic == original.topic
        assert restored.key == original.key
        assert restored.payload == original.payload
        assert restored.priority == original.priority
