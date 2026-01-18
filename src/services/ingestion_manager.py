"""Ingestion manager for coordinating all data connectors.

Provides centralized management, monitoring, and health checks for all data sources.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.services.connectors.base import BaseConnector, ConnectorStatus
from src.services.kafka_bus_real import get_kafka_bus
from src.services.stream_processor import get_stream_processor

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class IngestionHealth:
    """Overall health status of the ingestion system."""
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    connectors_total: int
    connectors_healthy: int
    connectors_degraded: int
    connectors_unhealthy: int
    connectors_disabled: int
    kafka_connected: bool
    stream_processor_running: bool
    last_check: str


class IngestionManager:
    """Centralized manager for all data ingestion connectors.
    
    Features:
    - Start/stop all connectors
    - Health monitoring
    - Automatic restart of failed connectors
    - Performance metrics
    - Alerting on failures
    """

    def __init__(self):
        """Initialize ingestion manager."""
        self._connectors: dict[str, BaseConnector] = {}
        self._kafka = get_kafka_bus()
        self._stream_processor = get_stream_processor()
        self._running = False
        self._health_check_task: asyncio.Task | None = None
        self._health_check_interval = 60  # seconds
    
    def register_connector(self, name: str, connector: BaseConnector) -> None:
        """Register a data connector."""
        self._connectors[name] = connector
        logger.info(f"Registered connector: {name}")
    
    def unregister_connector(self, name: str) -> None:
        """Unregister a data connector."""
        if name in self._connectors:
            del self._connectors[name]
            logger.info(f"Unregistered connector: {name}")
    
    async def start_all(self) -> None:
        """Start all registered connectors."""
        if self._running:
            logger.warning("Ingestion manager already running")
            return
        
        logger.info("=" * 60)
        logger.info("Starting ISR Platform Data Ingestion System")
        logger.info("=" * 60)
        
        # 1. Start Kafka
        logger.info("Step 1: Connecting to Kafka...")
        await self._kafka.connect()
        logger.info("✓ Kafka connected")
        
        # 2. Start stream processor
        logger.info("Step 2: Starting stream processing pipeline...")
        await self._stream_processor.start()
        logger.info("✓ Stream processor started")
        
        # 3. Start all connectors
        logger.info(f"Step 3: Starting {len(self._connectors)} data connectors...")
        for name, connector in self._connectors.items():
            try:
                await connector.start()
                logger.info(f"  ✓ {name} started")
            except Exception as e:
                logger.error(f"  ✗ Failed to start {name}: {e}")
        
        # 4. Start health monitoring
        logger.info("Step 4: Starting health monitoring...")
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("✓ Health monitoring started")
        
        logger.info("=" * 60)
        logger.info("✓ ISR Platform Data Ingestion System ONLINE")
        logger.info("=" * 60)
        
        # Log initial status
        await self._log_system_status()
    
    async def stop_all(self) -> None:
        """Stop all connectors."""
        if not self._running:
            return
        
        logger.info("=" * 60)
        logger.info("Stopping ISR Platform Data Ingestion System")
        logger.info("=" * 60)
        
        self._running = False
        
        # Stop health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Stop all connectors
        logger.info(f"Stopping {len(self._connectors)} connectors...")
        for name, connector in self._connectors.items():
            try:
                await connector.stop()
                logger.info(f"  ✓ {name} stopped")
            except Exception as e:
                logger.error(f"  ✗ Error stopping {name}: {e}")
        
        # Stop stream processor
        logger.info("Stopping stream processor...")
        await self._stream_processor.stop()
        logger.info("✓ Stream processor stopped")
        
        # Disconnect Kafka
        logger.info("Disconnecting Kafka...")
        await self._kafka.disconnect()
        logger.info("✓ Kafka disconnected")
        
        logger.info("=" * 60)
        logger.info("✓ ISR Platform Data Ingestion System OFFLINE")
        logger.info("=" * 60)
    
    async def restart_connector(self, name: str) -> bool:
        """Restart a specific connector."""
        if name not in self._connectors:
            logger.error(f"Connector not found: {name}")
            return False
        
        connector = self._connectors[name]
        
        try:
            logger.info(f"Restarting connector: {name}")
            await connector.stop()
            await asyncio.sleep(2)
            await connector.start()
            logger.info(f"✓ Connector restarted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restart connector {name}: {e}")
            return False
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while self._running:
            try:
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
            
            await asyncio.sleep(self._health_check_interval)
    
    async def _perform_health_check(self) -> None:
        """Perform health check on all connectors."""
        health = self.get_health()
        
        # Log status
        logger.info(
            f"Health Check: {health.status} | "
            f"Connectors: {health.connectors_healthy}/{health.connectors_total} healthy, "
            f"{health.connectors_degraded} degraded, "
            f"{health.connectors_unhealthy} unhealthy"
        )
        
        # Check for unhealthy connectors and attempt restart
        for name, connector in self._connectors.items():
            status = connector.get_status()
            
            if status["status"] == ConnectorStatus.UNHEALTHY.value:
                logger.warning(f"Connector {name} is unhealthy, attempting restart...")
                await self.restart_connector(name)
            
            # Check circuit breaker
            if status["circuit_breaker"]["is_open"]:
                logger.warning(f"Circuit breaker open for {name}")
        
        # Publish health status to Kafka
        await self._publish_health_metrics(health)
    
    async def _publish_health_metrics(self, health: IngestionHealth) -> None:
        """Publish health metrics to Kafka."""
        try:
            from src.services.kafka_bus_real import MessageTopic
            
            await self._kafka.publish(
                topic=MessageTopic.SYSTEM_HEALTH,
                payload={
                    "component": "ingestion_manager",
                    "status": health.status,
                    "metrics": {
                        "connectors_total": health.connectors_total,
                        "connectors_healthy": health.connectors_healthy,
                        "connectors_degraded": health.connectors_degraded,
                        "connectors_unhealthy": health.connectors_unhealthy,
                        "kafka_connected": health.kafka_connected,
                        "stream_processor_running": health.stream_processor_running,
                    },
                    "timestamp": health.last_check,
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish health metrics: {e}")
    
    async def _log_system_status(self) -> None:
        """Log detailed system status."""
        logger.info("")
        logger.info("System Status:")
        logger.info("-" * 60)
        
        # Kafka status
        kafka_stats = self._kafka.get_stats()
        logger.info(f"Kafka: {kafka_stats['mode']} mode, connected={kafka_stats['connected']}")
        
        # Stream processor status
        processor_stats = self._stream_processor.get_stats()
        logger.info(f"Stream Processor: running={processor_stats['running']}")
        
        # Connector status
        logger.info(f"Connectors ({len(self._connectors)}):")
        for name, connector in self._connectors.items():
            status = connector.get_status()
            logger.info(
                f"  - {name}: {status['status']} "
                f"(requests: {status['stats']['requests_total']}, "
                f"success: {status['stats']['requests_successful']}, "
                f"failed: {status['stats']['requests_failed']})"
            )
        
        logger.info("-" * 60)
        logger.info("")
    
    def get_health(self) -> IngestionHealth:
        """Get overall health status."""
        healthy = 0
        degraded = 0
        unhealthy = 0
        disabled = 0
        
        for connector in self._connectors.values():
            status = connector.get_status()
            status_value = status["status"]
            
            if status_value == ConnectorStatus.HEALTHY.value:
                healthy += 1
            elif status_value == ConnectorStatus.DEGRADED.value:
                degraded += 1
            elif status_value == ConnectorStatus.UNHEALTHY.value:
                unhealthy += 1
            elif status_value == ConnectorStatus.DISABLED.value:
                disabled += 1
        
        total = len(self._connectors)
        
        # Determine overall status
        if unhealthy > 0 or not self._kafka.get_stats()["connected"]:
            overall_status = "UNHEALTHY"
        elif degraded > 0:
            overall_status = "DEGRADED"
        else:
            overall_status = "HEALTHY"
        
        return IngestionHealth(
            status=overall_status,
            connectors_total=total,
            connectors_healthy=healthy,
            connectors_degraded=degraded,
            connectors_unhealthy=unhealthy,
            connectors_disabled=disabled,
            kafka_connected=self._kafka.get_stats()["connected"],
            stream_processor_running=self._stream_processor.get_stats()["running"],
            last_check=utcnow().isoformat(),
        )
    
    def get_connector_stats(self, name: str) -> dict[str, Any] | None:
        """Get statistics for a specific connector."""
        if name not in self._connectors:
            return None
        
        return self._connectors[name].get_status()
    
    def get_all_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics for all components."""
        return {
            "health": self.get_health().__dict__,
            "kafka": self._kafka.get_stats(),
            "stream_processor": self._stream_processor.get_stats(),
            "connectors": {
                name: connector.get_status()
                for name, connector in self._connectors.items()
            },
        }


# Global instance
_ingestion_manager: IngestionManager | None = None


def get_ingestion_manager() -> IngestionManager:
    """Get the ingestion manager instance."""
    global _ingestion_manager
    if _ingestion_manager is None:
        _ingestion_manager = IngestionManager()
    return _ingestion_manager
