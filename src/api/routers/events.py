"""Event management endpoints."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.domain import DataSource, Event, GeoPoint
from src.models.enums import EventType, Severity, SourceType
from src.schemas.api import (
    ApiResponse,
    DataSourceSchema,
    EventCreateSchema,
    EventResponseSchema,
    GeoPointSchema,
    MetaSchema,
    PaginationSchema,
)

from .auth import get_current_user_payload, require_permission

router = APIRouter()

# In-memory storage for demo
_events: dict[UUID, Event] = {}


def _event_to_response(event: Event) -> EventResponseSchema:
    """Convert domain event to response schema."""
    location = None
    if event.location:
        location = GeoPointSchema(
            latitude=event.location.latitude,
            longitude=event.location.longitude,
            altitude=event.location.altitude,
            accuracy=event.location.accuracy,
        )

    sources = [
        DataSourceSchema(
            source_type=s.source_type,
            source_id=s.source_id,
            weight=s.weight,
            confidence=s.confidence,
            timestamp=s.timestamp,
        )
        for s in event.sources
    ]

    return EventResponseSchema(
        event_id=event.event_id,
        event_type=event.event_type,
        event_subtype=event.event_subtype,
        severity=event.severity,
        occurred_at=event.occurred_at,
        reported_at=event.reported_at,
        location=location,
        location_description=event.location_description,
        region=event.region,
        province=event.province,
        district=event.district,
        title=event.title,
        summary=event.summary,
        details=event.details,
        casualties_killed=event.casualties_killed,
        casualties_wounded=event.casualties_wounded,
        population_affected=event.population_affected,
        verification_status=event.verification_status,
        sources=sources,
    )


@router.get("", response_model=ApiResponse[list[EventResponseSchema]])
async def list_events(
    user: Annotated[dict, Depends(require_permission("event:read"))],
    event_type: EventType | None = None,
    severity: Severity | None = None,
    region: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[EventResponseSchema]]:
    """List events with optional filtering."""
    # Filter events
    filtered = list(_events.values())

    if event_type:
        filtered = [e for e in filtered if e.event_type == event_type]

    if severity:
        filtered = [e for e in filtered if e.severity == severity]

    if region:
        filtered = [e for e in filtered if e.region == region]

    if start_time:
        filtered = [
            e for e in filtered if e.occurred_at and e.occurred_at >= start_time
        ]

    if end_time:
        filtered = [e for e in filtered if e.occurred_at and e.occurred_at <= end_time]

    # Sort by occurred_at descending
    filtered.sort(key=lambda e: e.occurred_at or e.reported_at, reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    # Convert to response
    events = [_event_to_response(e) for e in paginated]

    return ApiResponse(
        data=events,
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=utcnow(),
            pagination=PaginationSchema(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
        ),
    )


@router.post(
    "", response_model=ApiResponse[EventResponseSchema], status_code=status.HTTP_201_CREATED
)
async def create_event(
    event_data: EventCreateSchema,
    user: Annotated[dict, Depends(require_permission("event:read"))],
) -> ApiResponse[EventResponseSchema]:
    """Create a new event."""
    # Create location if provided
    location = None
    if event_data.location:
        location = GeoPoint(
            latitude=event_data.location.latitude,
            longitude=event_data.location.longitude,
            altitude=event_data.location.altitude,
            accuracy=event_data.location.accuracy,
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
        for s in event_data.sources
    ]

    # Create event
    event = Event(
        event_id=uuid4(),
        event_type=event_data.event_type,
        event_subtype=event_data.event_subtype,
        severity=event_data.severity,
        occurred_at=event_data.occurred_at,
        location=location,
        location_description=event_data.location_description,
        region=event_data.region,
        province=event_data.province,
        district=event_data.district,
        title=event_data.title,
        summary=event_data.summary,
        details=event_data.details,
        casualties_killed=event_data.casualties_killed,
        casualties_wounded=event_data.casualties_wounded,
        population_affected=event_data.population_affected,
        sources=sources,
    )

    # Store event
    _events[event.event_id] = event

    return ApiResponse(
        data=_event_to_response(event),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=utcnow(),
        ),
    )


@router.get("/{event_id}", response_model=ApiResponse[EventResponseSchema])
async def get_event(
    event_id: UUID,
    user: Annotated[dict, Depends(require_permission("event:read"))],
) -> ApiResponse[EventResponseSchema]:
    """Get event by ID."""
    event = _events.get(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )

    return ApiResponse(
        data=_event_to_response(event),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=utcnow(),
        ),
    )


@router.patch("/{event_id}/verify", response_model=ApiResponse[EventResponseSchema])
async def verify_event(
    event_id: UUID,
    verification_status: str,
    user: Annotated[dict, Depends(require_permission("event:read"))],
) -> ApiResponse[EventResponseSchema]:
    """Update event verification status."""
    event = _events.get(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )

    event.verification_status = verification_status

    return ApiResponse(
        data=_event_to_response(event),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=utcnow(),
        ),
    )
