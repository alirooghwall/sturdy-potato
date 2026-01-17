"""Analytics endpoints (threat scoring, anomaly detection)."""

from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.domain import Entity, GeoPoint
from src.models.enums import EntityStatus, EntityType, Severity
from src.schemas.api import (
    AnomalyResponseSchema,
    ApiResponse,
    FactorScoreSchema,
    GeoPointSchema,
    MetaSchema,
    PaginationSchema,
    ThreatScoreRequestSchema,
    ThreatScoreResponseSchema,
)
from src.services.anomaly_detection import BaselineStats, get_anomaly_service
from src.services.threat_scoring import get_threat_service

from .auth import require_permission

router = APIRouter()


@router.post("/threat-score", response_model=ApiResponse[ThreatScoreResponseSchema])
async def calculate_threat_score(
    request: ThreatScoreRequestSchema,
    user: Annotated[dict, Depends(require_permission("entity:read"))],
) -> ApiResponse[ThreatScoreResponseSchema]:
    """Calculate threat score for an entity."""
    threat_service = get_threat_service()

    # In production, fetch entity from database
    # For demo, create a sample entity
    entity = Entity(
        entity_id=request.entity_id,
        entity_type=EntityType.INSURGENT_CELL,
        display_name="Sample Entity",
        status=EntityStatus.ACTIVE,
        confidence_score=0.75,
        current_position=GeoPoint(latitude=34.5, longitude=69.1),
        attributes={
            "estimated_size": 25,
            "light_weapons": True,
            "heavy_weapons": False,
        },
    )

    # Context for threat scoring
    context: dict[str, Any] = {
        "window_start": request.context_window_start or datetime.utcnow() - timedelta(days=7),
        "window_end": request.context_window_end or datetime.utcnow(),
        "num_corroborating_sources": 3,
        "distance_to_population_center_km": 15,
        "near_critical_infrastructure": True,
        "security_presence_level": "MEDIUM",
        "civilian_density": "MEDIUM",
        "intelligence_age_hours": 12,
        "imminent_threat_indicators": False,
        "recent_activity_detected": True,
    }

    # Calculate threat score
    threat_score = threat_service.calculate_score(entity, context)

    # Convert to response
    factor_responses = {
        factor_name: FactorScoreSchema(
            score=factor_data["score"],
            weight=factor_data["weight"],
            contribution=factor_data["contribution"],
            details=factor_data.get("details"),
        )
        for factor_name, factor_data in threat_score.factor_scores.items()
    }

    return ApiResponse(
        data=ThreatScoreResponseSchema(
            entity_id=threat_score.entity_id,
            overall_score=threat_score.overall_score,
            category=threat_score.category.value,
            factor_scores=factor_responses,
            explanation_summary=threat_score.explanation_summary if request.include_explanation else None,
            key_indicators=threat_score.key_indicators,
            recommendations=threat_score.recommendations,
            trend_direction=threat_score.trend_direction,
            calculated_at=threat_score.calculated_at,
        ),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.post("/anomaly-detection/geo-movement")
async def detect_geo_movement_anomaly(
    user: Annotated[dict, Depends(require_permission("entity:read"))],
    location_id: str = Query(..., description="Location identifier"),
    current_count: int = Query(..., description="Current observation count"),
    baseline_mean: float = Query(..., description="Baseline average count"),
    baseline_std: float = Query(..., description="Baseline standard deviation"),
    baseline_days: int = Query(default=30, description="Baseline period in days"),
) -> dict[str, Any]:
    """Detect anomaly in geo-movement data."""
    anomaly_service = get_anomaly_service()

    baseline = BaselineStats(
        mean=baseline_mean,
        std=baseline_std,
        min_val=0,
        max_val=baseline_mean * 3,
        period_days=baseline_days,
        sample_count=baseline_days,
    )

    metadata = {
        "location_id": location_id,
        "region": "Kabul Province",
    }

    anomaly = anomaly_service.detect_geo_movement_anomaly(
        location_id=location_id,
        current_count=current_count,
        baseline=baseline,
        metadata=metadata,
    )

    if anomaly is None:
        return {
            "anomaly_detected": False,
            "message": "No anomaly detected - activity within normal range",
            "timestamp": datetime.utcnow().isoformat(),
        }

    return {
        "anomaly_detected": True,
        "anomaly": {
            "anomaly_id": str(anomaly.anomaly_id),
            "domain": anomaly.domain,
            "severity": anomaly.severity.value,
            "severity_score": anomaly.severity_score,
            "description": anomaly.description,
            "anomaly_score": anomaly.anomaly_score,
            "baseline_stats": anomaly.baseline_stats,
            "detected_at": anomaly.detected_at.isoformat(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/anomaly-detection/social-media")
async def detect_social_media_anomaly(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    topic: str = Query(..., description="Topic to analyze"),
    current_volume: int = Query(..., description="Current volume of posts"),
    baseline_mean: float = Query(..., description="Baseline average volume"),
    baseline_std: float = Query(..., description="Baseline standard deviation"),
    sentiment_shift: float | None = Query(
        default=None, description="Sentiment shift from baseline (-1 to 1)"
    ),
) -> dict[str, Any]:
    """Detect anomaly in social media activity."""
    anomaly_service = get_anomaly_service()

    baseline = BaselineStats(
        mean=baseline_mean,
        std=baseline_std,
        min_val=0,
        max_val=baseline_mean * 5,
        period_days=14,
        sample_count=14,
    )

    anomaly = anomaly_service.detect_social_media_anomaly(
        topic=topic,
        current_volume=current_volume,
        baseline=baseline,
        sentiment_shift=sentiment_shift,
    )

    if anomaly is None:
        return {
            "anomaly_detected": False,
            "message": "No anomaly detected - social media activity within normal range",
            "timestamp": datetime.utcnow().isoformat(),
        }

    return {
        "anomaly_detected": True,
        "anomaly": {
            "anomaly_id": str(anomaly.anomaly_id),
            "domain": anomaly.domain,
            "severity": anomaly.severity.value,
            "severity_score": anomaly.severity_score,
            "description": anomaly.description,
            "anomaly_score": anomaly.anomaly_score,
            "baseline_stats": anomaly.baseline_stats,
            "detected_at": anomaly.detected_at.isoformat(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/trends/threats")
async def get_threat_trends(
    user: Annotated[dict, Depends(require_permission("dashboard:read"))],
    region: str | None = None,
    days: int = Query(default=7, ge=1, le=90),
) -> dict[str, Any]:
    """Get threat score trends over time."""
    # In production, fetch from database
    # For demo, generate sample data
    import random

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    trends = []
    current = start_date
    base_score = 45

    while current <= end_date:
        # Simulate some variation
        score = base_score + random.randint(-10, 15)
        score = max(0, min(100, score))

        trends.append({
            "date": current.date().isoformat(),
            "average_score": score,
            "critical_count": random.randint(0, 3),
            "high_count": random.randint(2, 8),
            "medium_count": random.randint(5, 15),
            "low_count": random.randint(10, 25),
        })

        current += timedelta(days=1)
        base_score += random.randint(-3, 3)

    return {
        "region": region or "All Regions",
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "trends": trends,
        "summary": {
            "average_score": sum(t["average_score"] for t in trends) // len(trends),
            "trend_direction": "INCREASING" if trends[-1]["average_score"] > trends[0]["average_score"] else "DECREASING",
            "total_critical": sum(t["critical_count"] for t in trends),
            "total_high": sum(t["high_count"] for t in trends),
        },
    }
