"""Ingestion management API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.ingestion_manager import get_ingestion_manager

router = APIRouter()


@router.get("/health")
async def get_ingestion_health() -> dict[str, Any]:
    """Get overall ingestion system health."""
    manager = get_ingestion_manager()
    health = manager.get_health()
    return health.__dict__


@router.get("/stats")
async def get_ingestion_stats() -> dict[str, Any]:
    """Get comprehensive ingestion statistics."""
    manager = get_ingestion_manager()
    return manager.get_all_stats()


@router.get("/connectors")
async def list_connectors() -> dict[str, Any]:
    """List all registered connectors and their status."""
    manager = get_ingestion_manager()
    stats = manager.get_all_stats()
    return {
        "connectors": stats["connectors"],
        "total": len(stats["connectors"]),
    }


@router.get("/connectors/{name}")
async def get_connector_status(name: str) -> dict[str, Any]:
    """Get status for a specific connector."""
    manager = get_ingestion_manager()
    status = manager.get_connector_stats(name)
    
    if status is None:
        raise HTTPException(status_code=404, detail=f"Connector not found: {name}")
    
    return status


@router.post("/connectors/{name}/restart")
async def restart_connector(name: str) -> dict[str, str]:
    """Restart a specific connector."""
    manager = get_ingestion_manager()
    success = await manager.restart_connector(name)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to restart connector: {name}"
        )
    
    return {"status": "success", "message": f"Connector {name} restarted"}


@router.get("/kafka/stats")
async def get_kafka_stats() -> dict[str, Any]:
    """Get Kafka message bus statistics."""
    from src.services.kafka_bus_real import get_kafka_bus
    
    kafka = get_kafka_bus()
    return kafka.get_stats()


@router.get("/kafka/history")
async def get_kafka_history(topic: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Get recent Kafka message history."""
    from src.services.kafka_bus_real import get_kafka_bus, MessageTopic
    
    kafka = get_kafka_bus()
    
    topic_enum = None
    if topic:
        try:
            topic_enum = MessageTopic(topic)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid topic: {topic}")
    
    messages = kafka.get_message_history(topic=topic_enum, limit=limit)
    
    return {
        "topic": topic,
        "count": len(messages),
        "messages": [
            {
                "message_id": str(msg.message_id),
                "topic": msg.topic.value,
                "key": msg.key,
                "priority": msg.priority.value,
                "timestamp": msg.timestamp.isoformat(),
                "payload_preview": str(msg.payload)[:200],
            }
            for msg in messages
        ],
    }


@router.get("/stream-processor/stats")
async def get_stream_processor_stats() -> dict[str, Any]:
    """Get stream processor statistics."""
    from src.services.stream_processor import get_stream_processor
    
    processor = get_stream_processor()
    return processor.get_stats()
