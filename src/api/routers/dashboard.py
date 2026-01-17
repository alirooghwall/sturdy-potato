"""Dashboard endpoints."""

from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from src.schemas.api import ApiResponse, MetaSchema

from .auth import require_permission

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    user: Annotated[dict, Depends(require_permission("dashboard:read"))],
) -> dict[str, Any]:
    """Get dashboard overview with key metrics."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_alerts": {
            "CRITICAL": 2,
            "HIGH": 7,
            "MEDIUM": 15,
            "LOW": 23,
        },
        "active_tracks": 156,
        "active_simulations": 3,
        "data_ingestion_rate": {
            "satellite": {"rate": 1250, "unit": "images/hour", "status": "healthy"},
            "osint": {"rate": 5400, "unit": "articles/hour", "status": "healthy"},
            "social_media": {"rate": 12000, "unit": "posts/hour", "status": "healthy"},
            "sensors": {"rate": 340, "unit": "reports/hour", "status": "healthy"},
        },
        "threat_overview": {
            "overall_level": "ELEVATED",
            "score": 62,
            "trend": "STABLE",
            "hotspots": [
                {"region": "Nangarhar Province", "score": 78},
                {"region": "Helmand Province", "score": 72},
                {"region": "Kandahar Province", "score": 68},
            ],
        },
        "recent_events": [
            {
                "event_id": str(uuid4()),
                "type": "BORDER_CROSSING",
                "severity": "MEDIUM",
                "region": "Nangarhar Province",
                "title": "Unusual activity at Torkham border",
                "occurred_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            },
            {
                "event_id": str(uuid4()),
                "type": "EXPLOSION",
                "severity": "HIGH",
                "region": "Kabul Province",
                "title": "IED detonation on Highway 1",
                "occurred_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
            },
        ],
        "narrative_trends": {
            "trending_topics": [
                {"topic": "Economic Crisis", "volume": 3450, "sentiment": -0.42},
                {"topic": "Border Security", "volume": 2100, "sentiment": -0.28},
                {"topic": "Humanitarian Aid", "volume": 1870, "sentiment": 0.15},
            ],
            "disinformation_alerts": 3,
            "coordinated_campaigns_detected": 1,
        },
        "system_health": {
            "api": "healthy",
            "database": "healthy",
            "message_bus": "healthy",
            "ml_services": "healthy",
            "simulation_engine": "healthy",
        },
    }


@router.get("/situational-awareness")
async def get_situational_awareness(
    user: Annotated[dict, Depends(require_permission("dashboard:read"))],
    region: str | None = None,
) -> dict[str, Any]:
    """Get situational awareness data for map display."""
    # In production, aggregate from various services
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "region": region or "Afghanistan",
        "entities": [
            {
                "entity_id": str(uuid4()),
                "entity_type": "MILITARY_UNIT",
                "display_name": "Coalition Patrol Alpha",
                "position": {"latitude": 34.5281, "longitude": 69.1723},
                "status": "ACTIVE",
                "threat_score": None,
            },
            {
                "entity_id": str(uuid4()),
                "entity_type": "CONVOY",
                "display_name": "Supply Convoy Echo",
                "position": {"latitude": 34.3157, "longitude": 62.2032},
                "status": "ACTIVE",
                "threat_score": 35,
            },
            {
                "entity_id": str(uuid4()),
                "entity_type": "INSURGENT_CELL",
                "display_name": "Unknown Group Alpha",
                "position": {"latitude": 34.0151, "longitude": 70.6343},
                "status": "ACTIVE",
                "threat_score": 72,
            },
        ],
        "events": [
            {
                "event_id": str(uuid4()),
                "event_type": "EXPLOSION",
                "severity": "HIGH",
                "position": {"latitude": 34.5553, "longitude": 69.2075},
                "occurred_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "title": "IED detonation reported",
            },
        ],
        "alerts": [
            {
                "alert_id": str(uuid4()),
                "severity": "CRITICAL",
                "category": "SECURITY",
                "position": {"latitude": 34.4015, "longitude": 70.4526},
                "title": "High-value target movement detected",
            },
        ],
        "coverage_areas": [
            {
                "type": "UAV",
                "center": {"latitude": 34.5, "longitude": 69.5},
                "radius_km": 50,
                "status": "ACTIVE",
            },
            {
                "type": "SATELLITE",
                "bounds": {
                    "north": 35.0,
                    "south": 34.0,
                    "east": 70.0,
                    "west": 69.0,
                },
                "last_update": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            },
        ],
    }


@router.get("/metrics/ingestion")
async def get_ingestion_metrics(
    user: Annotated[dict, Depends(require_permission("dashboard:read"))],
    hours: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    """Get data ingestion metrics."""
    import random

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Generate hourly metrics
    metrics = []
    current = start_time

    while current <= end_time:
        metrics.append({
            "timestamp": current.isoformat(),
            "satellite_images": random.randint(1000, 1500),
            "osint_articles": random.randint(4500, 6000),
            "social_media_posts": random.randint(10000, 14000),
            "sensor_reports": random.randint(250, 400),
            "cyber_telemetry": random.randint(500, 800),
        })
        current += timedelta(hours=1)

    return {
        "period_start": start_time.isoformat(),
        "period_end": end_time.isoformat(),
        "metrics": metrics,
        "totals": {
            "satellite_images": sum(m["satellite_images"] for m in metrics),
            "osint_articles": sum(m["osint_articles"] for m in metrics),
            "social_media_posts": sum(m["social_media_posts"] for m in metrics),
            "sensor_reports": sum(m["sensor_reports"] for m in metrics),
            "cyber_telemetry": sum(m["cyber_telemetry"] for m in metrics),
        },
    }


@router.get("/regions")
async def get_region_summary(
    user: Annotated[dict, Depends(require_permission("dashboard:read"))],
) -> dict[str, Any]:
    """Get summary of all regions."""
    regions = [
        {
            "name": "Kabul Province",
            "threat_level": "HIGH",
            "threat_score": 68,
            "active_alerts": 5,
            "active_entities": 45,
            "recent_events": 12,
        },
        {
            "name": "Nangarhar Province",
            "threat_level": "CRITICAL",
            "threat_score": 78,
            "active_alerts": 8,
            "active_entities": 32,
            "recent_events": 18,
        },
        {
            "name": "Helmand Province",
            "threat_level": "HIGH",
            "threat_score": 72,
            "active_alerts": 6,
            "active_entities": 28,
            "recent_events": 15,
        },
        {
            "name": "Kandahar Province",
            "threat_level": "HIGH",
            "threat_score": 68,
            "active_alerts": 4,
            "active_entities": 35,
            "recent_events": 11,
        },
        {
            "name": "Herat Province",
            "threat_level": "MEDIUM",
            "threat_score": 52,
            "active_alerts": 2,
            "active_entities": 18,
            "recent_events": 6,
        },
        {
            "name": "Balkh Province",
            "threat_level": "MEDIUM",
            "threat_score": 48,
            "active_alerts": 2,
            "active_entities": 22,
            "recent_events": 5,
        },
    ]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "regions": regions,
        "summary": {
            "total_regions": len(regions),
            "critical_regions": len([r for r in regions if r["threat_level"] == "CRITICAL"]),
            "high_regions": len([r for r in regions if r["threat_level"] == "HIGH"]),
            "medium_regions": len([r for r in regions if r["threat_level"] == "MEDIUM"]),
            "total_alerts": sum(r["active_alerts"] for r in regions),
            "total_entities": sum(r["active_entities"] for r in regions),
        },
    }
