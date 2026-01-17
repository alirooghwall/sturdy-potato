"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Check API health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "isr-platform-api",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """Check if the API is ready to serve requests."""
    # In production, check database connectivity, cache, etc.
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "ok",
            "cache": "ok",
            "message_bus": "ok",
        },
    }
