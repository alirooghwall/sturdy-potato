"""Tests for data ingestion system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.connectors.base import ConnectorConfig, ConnectorStatus
from src.services.ingestion_manager import IngestionManager


@pytest.fixture
def mock_connector():
    """Create a mock connector for testing."""
    connector = MagicMock()
    connector.config = ConnectorConfig(name="TestConnector")
    connector.start = AsyncMock()
    connector.stop = AsyncMock()
    connector.get_status = MagicMock(return_value={
        "name": "TestConnector",
        "status": ConnectorStatus.HEALTHY.value,
        "running": True,
        "circuit_breaker": {
            "state": "CLOSED",
            "is_open": False,
            "failure_count": 0,
        },
        "stats": {
            "requests_total": 100,
            "requests_successful": 95,
            "requests_failed": 5,
            "records_ingested": 1000,
        },
    })
    return connector


@pytest.mark.asyncio
async def test_ingestion_manager_register_connector(mock_connector):
    """Test registering a connector."""
    manager = IngestionManager()
    
    manager.register_connector("test", mock_connector)
    
    assert "test" in manager._connectors
    assert manager._connectors["test"] == mock_connector


@pytest.mark.asyncio
async def test_ingestion_manager_health_check(mock_connector):
    """Test health check functionality."""
    manager = IngestionManager()
    manager.register_connector("test", mock_connector)
    
    health = manager.get_health()
    
    assert health.connectors_total == 1
    assert health.connectors_healthy == 1
    assert health.status in ["HEALTHY", "DEGRADED", "UNHEALTHY"]


@pytest.mark.asyncio
async def test_connector_stats(mock_connector):
    """Test getting connector statistics."""
    manager = IngestionManager()
    manager.register_connector("test", mock_connector)
    
    stats = manager.get_connector_stats("test")
    
    assert stats is not None
    assert stats["name"] == "TestConnector"
    assert stats["status"] == ConnectorStatus.HEALTHY.value


@pytest.mark.asyncio
async def test_kafka_message_serialization():
    """Test Kafka message serialization."""
    from uuid import uuid4
    from src.services.kafka_bus_real import KafkaMessage, MessageTopic, MessagePriority
    
    message = KafkaMessage(
        message_id=uuid4(),
        topic=MessageTopic.OSINT_NEWS,
        key="test-key",
        payload={"data": "test"},
        priority=MessagePriority.HIGH,
    )
    
    # Serialize to JSON
    json_str = message.to_json()
    
    # Deserialize back
    restored = KafkaMessage.from_json(json_str)
    
    assert restored.message_id == message.message_id
    assert restored.topic == message.topic
    assert restored.key == message.key
    assert restored.payload == message.payload
    assert restored.priority == message.priority
