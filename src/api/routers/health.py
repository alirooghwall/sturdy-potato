"""Health check endpoints."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, status
from sqlalchemy import text

from src.config.settings import get_settings
from src.services.database import get_db_service


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


async def check_database() -> dict[str, Any]:
    """Check database connectivity and health."""
    try:
        db = get_db_service()
        async with db.session() as session:
            # Execute a simple query to check connectivity
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Check connection pool status
            pool = db.engine.pool
            
            return {
                "status": "healthy",
                "details": {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                },
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_redis() -> dict[str, Any]:
    """Check Redis connectivity and health."""
    try:
        settings = get_settings()
        redis_client = aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
        )
        
        # Test connection with ping
        await redis_client.ping()
        
        # Get server info
        info = await redis_client.info("server")
        
        await redis_client.close()
        
        return {
            "status": "healthy",
            "details": {
                "version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_kafka() -> dict[str, Any]:
    """Check Kafka connectivity and health."""
    try:
        settings = get_settings()
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            request_timeout_ms=5000,
        )
        
        # Start and stop to test connection
        await asyncio.wait_for(producer.start(), timeout=5.0)
        await producer.stop()
        
        return {
            "status": "healthy",
            "details": {
                "bootstrap_servers": settings.kafka_bootstrap_servers,
            },
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "error": "Connection timeout",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/health")
async def health_check() -> dict:
    """Check API health status."""
    return {
        "status": "healthy",
        "timestamp": utcnow().isoformat(),
        "service": "isr-platform-api",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """Check if the API is ready to serve requests."""
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_kafka(),
        return_exceptions=True,
    )
    
    database_check, redis_check, kafka_check = checks
    
    # Determine overall status
    all_healthy = all(
        isinstance(check, dict) and check.get("status") == "healthy"
        for check in [database_check, redis_check, kafka_check]
    )
    
    overall_status = "ready" if all_healthy else "degraded"
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    response = {
        "status": overall_status,
        "timestamp": utcnow().isoformat(),
        "checks": {
            "database": database_check if isinstance(database_check, dict) else {"status": "error", "error": str(database_check)},
            "cache": redis_check if isinstance(redis_check, dict) else {"status": "error", "error": str(redis_check)},
            "message_bus": kafka_check if isinstance(kafka_check, dict) else {"status": "error", "error": str(kafka_check)},
        },
    }
    
    return response


@router.get("/health/live")
async def liveness_check() -> dict:
    """Kubernetes liveness probe endpoint."""
    return {
        "status": "alive",
        "timestamp": utcnow().isoformat(),
    }


@router.get("/health/startup")
async def startup_check() -> dict:
    """Kubernetes startup probe endpoint."""
    # Check if critical dependencies are available
    db_check = await check_database()
    
    if db_check.get("status") == "healthy":
        return {
            "status": "started",
            "timestamp": utcnow().isoformat(),
        }
    else:
        return {
            "status": "starting",
            "timestamp": utcnow().isoformat(),
            "message": "Waiting for database connection",
        }
