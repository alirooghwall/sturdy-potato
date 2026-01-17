"""Alert management endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.domain import Alert, DataSource, GeoPoint
from src.models.enums import AlertCategory, AlertStatus, Severity
from src.schemas.api import (
    AlertAcknowledgeSchema,
    AlertCreateSchema,
    AlertResolveSchema,
    AlertResponseSchema,
    ApiResponse,
    DataSourceSchema,
    GeoPointSchema,
    MetaSchema,
    PaginationSchema,
)

from .auth import get_current_user_payload, require_permission

router = APIRouter()

# In-memory storage for demo
_alerts: dict[UUID, Alert] = {}


def _alert_to_response(alert: Alert) -> AlertResponseSchema:
    """Convert domain alert to response schema."""
    location = None
    if alert.location:
        location = GeoPointSchema(
            latitude=alert.location.latitude,
            longitude=alert.location.longitude,
            altitude=alert.location.altitude,
            accuracy=alert.location.accuracy,
        )

    sources = [
        DataSourceSchema(
            source_type=s.source_type,
            source_id=s.source_id,
            weight=s.weight,
            confidence=s.confidence,
            timestamp=s.timestamp,
        )
        for s in alert.sources
    ]

    return AlertResponseSchema(
        alert_id=alert.alert_id,
        category=alert.category,
        subcategory=alert.subcategory,
        severity=alert.severity,
        title=alert.title,
        summary=alert.summary,
        details=alert.details,
        location=location,
        region=alert.region,
        threat_score=alert.threat_score,
        confidence=alert.confidence,
        trigger_type=alert.trigger_type,
        trigger_id=alert.trigger_id,
        sources=sources,
        status=alert.status,
        assigned_to_user=alert.assigned_to_user,
        assigned_to_team=alert.assigned_to_team,
        response_deadline=alert.response_deadline,
        resolution_deadline=alert.resolution_deadline,
        related_entities=alert.related_entities,
        related_events=alert.related_events,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        acknowledged_at=alert.acknowledged_at,
    )


@router.get("", response_model=ApiResponse[list[AlertResponseSchema]])
async def list_alerts(
    user: Annotated[dict, Depends(require_permission("alert:read"))],
    severity: list[Severity] | None = Query(default=None),
    status_filter: list[AlertStatus] | None = Query(default=None, alias="status"),
    category: AlertCategory | None = None,
    region: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[AlertResponseSchema]]:
    """List alerts with optional filtering."""
    # Filter alerts
    filtered = list(_alerts.values())

    if severity:
        filtered = [a for a in filtered if a.severity in severity]

    if status_filter:
        filtered = [a for a in filtered if a.status in status_filter]

    if category:
        filtered = [a for a in filtered if a.category == category]

    if region:
        filtered = [a for a in filtered if a.region == region]

    # Sort by created_at descending
    filtered.sort(key=lambda a: a.created_at, reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    # Convert to response
    alerts = [_alert_to_response(a) for a in paginated]

    return ApiResponse(
        data=alerts,
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            pagination=PaginationSchema(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
        ),
    )


@router.post(
    "", response_model=ApiResponse[AlertResponseSchema], status_code=status.HTTP_201_CREATED
)
async def create_alert(
    alert_data: AlertCreateSchema,
    user: Annotated[dict, Depends(require_permission("alert:create"))],
) -> ApiResponse[AlertResponseSchema]:
    """Create a new alert."""
    # Create location if provided
    location = None
    if alert_data.location:
        location = GeoPoint(
            latitude=alert_data.location.latitude,
            longitude=alert_data.location.longitude,
            altitude=alert_data.location.altitude,
            accuracy=alert_data.location.accuracy,
        )

    # Create sources
    sources = [
        DataSource(
            source_type=s.source_type,
            source_id=s.source_id,
            weight=s.weight,
            confidence=s.confidence,
            timestamp=s.timestamp,
        )
        for s in alert_data.sources
    ]

    # Create alert
    alert = Alert(
        alert_id=uuid4(),
        category=alert_data.category,
        subcategory=alert_data.subcategory,
        severity=alert_data.severity,
        title=alert_data.title,
        summary=alert_data.summary,
        details=alert_data.details,
        location=location,
        region=alert_data.region,
        threat_score=alert_data.threat_score,
        confidence=alert_data.confidence,
        trigger_type=alert_data.trigger_type,
        trigger_id=alert_data.trigger_id,
        sources=sources,
        related_entities=alert_data.related_entities,
        related_events=alert_data.related_events,
    )

    # Store alert
    _alerts[alert.alert_id] = alert

    return ApiResponse(
        data=_alert_to_response(alert),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.get("/{alert_id}", response_model=ApiResponse[AlertResponseSchema])
async def get_alert(
    alert_id: UUID,
    user: Annotated[dict, Depends(require_permission("alert:read"))],
) -> ApiResponse[AlertResponseSchema]:
    """Get alert by ID."""
    alert = _alerts.get(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )

    return ApiResponse(
        data=_alert_to_response(alert),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.post("/{alert_id}/acknowledge", response_model=ApiResponse[AlertResponseSchema])
async def acknowledge_alert(
    alert_id: UUID,
    acknowledge_data: AlertAcknowledgeSchema,
    user: Annotated[dict, Depends(require_permission("alert:acknowledge"))],
) -> ApiResponse[AlertResponseSchema]:
    """Acknowledge an alert."""
    alert = _alerts.get(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )

    if alert.status != AlertStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only OPEN alerts can be acknowledged",
        )

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    alert.assigned_to_user = user.get("username")
    alert.updated_at = datetime.utcnow()

    if acknowledge_data.notes:
        alert.details["acknowledgement_notes"] = acknowledge_data.notes

    return ApiResponse(
        data=_alert_to_response(alert),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.post("/{alert_id}/resolve", response_model=ApiResponse[AlertResponseSchema])
async def resolve_alert(
    alert_id: UUID,
    resolve_data: AlertResolveSchema,
    user: Annotated[dict, Depends(require_permission("alert:resolve"))],
) -> ApiResponse[AlertResponseSchema]:
    """Resolve an alert."""
    alert = _alerts.get(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )

    if alert.status in [AlertStatus.RESOLVED, AlertStatus.CLOSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved or closed",
        )

    # Set appropriate status based on resolution type
    if resolve_data.resolution_type == "FALSE_POSITIVE":
        alert.status = AlertStatus.FALSE_POSITIVE
    else:
        alert.status = AlertStatus.RESOLVED

    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = user.get("username")
    alert.resolution_notes = resolve_data.notes
    alert.updated_at = datetime.utcnow()

    return ApiResponse(
        data=_alert_to_response(alert),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.get("/summary/by-severity")
async def get_alert_summary_by_severity(
    user: Annotated[dict, Depends(require_permission("alert:read"))],
) -> dict:
    """Get alert count summary by severity."""
    summary = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for alert in _alerts.values():
        if alert.status not in [AlertStatus.RESOLVED, AlertStatus.CLOSED, AlertStatus.FALSE_POSITIVE]:
            summary[alert.severity.value] += 1

    return {"data": summary, "timestamp": datetime.utcnow().isoformat()}
