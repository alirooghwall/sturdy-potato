"""API request/response schemas for ISR Platform."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import (
    AlertCategory,
    AlertStatus,
    AnomalyDomain,
    EntityStatus,
    EntityType,
    EventType,
    Severity,
    SourceType,
)


# Base schemas
class GeoPointSchema(BaseModel):
    """Geographic point."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: float | None = None
    accuracy: float | None = None


class BoundingBoxSchema(BaseModel):
    """Geographic bounding box."""

    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)


class VelocitySchema(BaseModel):
    """Velocity information."""

    speed: float = Field(..., ge=0)
    heading: float = Field(..., ge=0, lt=360)
    unit: str = "MPS"


class DataSourceSchema(BaseModel):
    """Data source attribution."""

    source_type: SourceType
    source_id: str
    weight: float = Field(default=1.0, ge=0, le=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    timestamp: datetime | None = None


class PaginationSchema(BaseModel):
    """Pagination metadata."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    total_items: int = 0
    total_pages: int = 0


class MetaSchema(BaseModel):
    """Response metadata."""

    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pagination: PaginationSchema | None = None


class LinksSchema(BaseModel):
    """HATEOAS links."""

    self_link: str | None = Field(None, alias="self")
    next_link: str | None = Field(None, alias="next")
    prev_link: str | None = Field(None, alias="prev")


# Entity schemas
class EntityCreateSchema(BaseModel):
    """Schema for creating an entity."""

    entity_type: EntityType
    entity_subtype: str | None = None
    display_name: str | None = None
    status: EntityStatus = EntityStatus.ACTIVE
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    current_position: GeoPointSchema | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class EntityUpdateSchema(BaseModel):
    """Schema for updating an entity."""

    entity_subtype: str | None = None
    display_name: str | None = None
    status: EntityStatus | None = None
    confidence_score: float | None = Field(None, ge=0, le=1)
    current_position: GeoPointSchema | None = None
    attributes: dict[str, Any] | None = None


class EntityResponseSchema(BaseModel):
    """Schema for entity response."""

    entity_id: UUID
    entity_type: EntityType
    entity_subtype: str | None = None
    display_name: str | None = None
    status: EntityStatus
    confidence_score: float
    first_observed: datetime
    last_observed: datetime
    current_position: GeoPointSchema | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Track schemas
class TrackCreateSchema(BaseModel):
    """Schema for creating a track."""

    entity_id: UUID
    observation_time: datetime
    position: GeoPointSchema
    velocity: VelocitySchema | None = None
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    primary_source_type: SourceType
    primary_source_id: str | None = None
    contributing_sources: list[DataSourceSchema] = Field(default_factory=list)


class TrackResponseSchema(BaseModel):
    """Schema for track response."""

    track_id: UUID
    entity_id: UUID
    observation_time: datetime
    position: GeoPointSchema
    velocity: VelocitySchema | None = None
    confidence_score: float
    primary_source_type: SourceType
    primary_source_id: str | None = None
    contributing_sources: list[DataSourceSchema] = Field(default_factory=list)
    is_fused: bool = False


# Event schemas
class EventCreateSchema(BaseModel):
    """Schema for creating an event."""

    event_type: EventType
    event_subtype: str | None = None
    severity: Severity
    occurred_at: datetime | None = None
    location: GeoPointSchema | None = None
    location_description: str | None = None
    region: str | None = None
    province: str | None = None
    district: str | None = None
    title: str
    summary: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    casualties_killed: int | None = None
    casualties_wounded: int | None = None
    population_affected: int | None = None
    sources: list[DataSourceSchema] = Field(default_factory=list)


class EventResponseSchema(BaseModel):
    """Schema for event response."""

    event_id: UUID
    event_type: EventType
    event_subtype: str | None = None
    severity: Severity
    occurred_at: datetime | None = None
    reported_at: datetime
    location: GeoPointSchema | None = None
    location_description: str | None = None
    region: str | None = None
    province: str | None = None
    district: str | None = None
    title: str
    summary: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    casualties_killed: int | None = None
    casualties_wounded: int | None = None
    population_affected: int | None = None
    verification_status: str
    sources: list[DataSourceSchema] = Field(default_factory=list)


# Alert schemas
class AlertCreateSchema(BaseModel):
    """Schema for creating an alert."""

    category: AlertCategory
    subcategory: str | None = None
    severity: Severity
    title: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    location: GeoPointSchema | None = None
    region: str | None = None
    threat_score: int | None = Field(None, ge=0, le=100)
    confidence: float = Field(default=0.5, ge=0, le=1)
    trigger_type: str
    trigger_id: str | None = None
    sources: list[DataSourceSchema] = Field(default_factory=list)
    related_entities: list[UUID] = Field(default_factory=list)
    related_events: list[UUID] = Field(default_factory=list)


class AlertAcknowledgeSchema(BaseModel):
    """Schema for acknowledging an alert."""

    notes: str | None = None
    estimated_resolution_time: datetime | None = None


class AlertResolveSchema(BaseModel):
    """Schema for resolving an alert."""

    resolution_type: str  # CONFIRMED, FALSE_POSITIVE, DUPLICATE, RESOLVED
    notes: str | None = None


class AlertResponseSchema(BaseModel):
    """Schema for alert response."""

    alert_id: UUID
    category: AlertCategory
    subcategory: str | None = None
    severity: Severity
    title: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    location: GeoPointSchema | None = None
    region: str | None = None
    threat_score: int | None = None
    confidence: float
    trigger_type: str
    trigger_id: str | None = None
    sources: list[DataSourceSchema] = Field(default_factory=list)
    status: AlertStatus
    assigned_to_user: str | None = None
    assigned_to_team: str | None = None
    response_deadline: datetime | None = None
    resolution_deadline: datetime | None = None
    related_entities: list[UUID] = Field(default_factory=list)
    related_events: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None = None


# Threat score schemas
class ThreatScoreRequestSchema(BaseModel):
    """Schema for requesting threat score calculation."""

    entity_id: UUID
    context_window_start: datetime | None = None
    context_window_end: datetime | None = None
    include_explanation: bool = True


class FactorScoreSchema(BaseModel):
    """Schema for a threat score factor."""

    score: int = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    contribution: float
    details: str | None = None


class ThreatScoreResponseSchema(BaseModel):
    """Schema for threat score response."""

    entity_id: UUID
    overall_score: int = Field(..., ge=0, le=100)
    category: str  # LOW, MEDIUM, HIGH, CRITICAL
    factor_scores: dict[str, FactorScoreSchema]
    explanation_summary: str | None = None
    key_indicators: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    trend_direction: str | None = None
    calculated_at: datetime


# Anomaly schemas
class AnomalyResponseSchema(BaseModel):
    """Schema for anomaly response."""

    anomaly_id: UUID
    domain: AnomalyDomain
    anomaly_subtype: str | None = None
    severity: Severity
    severity_score: int
    detected_at: datetime
    location: GeoPointSchema | None = None
    region: str | None = None
    description: str
    baseline_stats: dict[str, Any] = Field(default_factory=dict)
    model_id: str | None = None
    anomaly_score: float
    related_entities: list[UUID] = Field(default_factory=list)
    status: str


# Dashboard schemas
class DashboardOverviewSchema(BaseModel):
    """Schema for dashboard overview."""

    timestamp: datetime
    active_alerts: dict[str, int]  # By severity
    active_tracks: int
    active_simulations: int
    data_ingestion_rate: dict[str, Any]
    threat_overview: dict[str, Any]
    recent_events: list[EventResponseSchema]
    narrative_trends: dict[str, Any]
    system_health: dict[str, Any]


# Authentication schemas
class TokenSchema(BaseModel):
    """Schema for authentication token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLoginSchema(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserResponseSchema(BaseModel):
    """Schema for user response."""

    user_id: UUID
    username: str
    email: str | None = None
    display_name: str | None = None
    organization: str | None = None
    roles: list[str] = Field(default_factory=list)
    status: str
    last_login: datetime | None = None


# Generic response wrapper
class ApiResponse[T](BaseModel):
    """Generic API response wrapper."""

    data: T
    meta: MetaSchema
    links: LinksSchema | None = None


class ApiErrorSchema(BaseModel):
    """Schema for API errors."""

    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None


class ApiErrorResponse(BaseModel):
    """Schema for API error response."""

    error: ApiErrorSchema
