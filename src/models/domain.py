"""Domain models for ISR Platform.

These are simple dataclasses used for business logic.
For database persistence, see orm.py.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.models.enums import (
    AlertCategory,
    AlertStatus,
    AnomalyDomain,
    DataClassification,
    EntityStatus,
    EntityType,
    EventType,
    Severity,
    SourceType,
    ThreatCategory,
    UserRole,
)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class GeoPoint:
    """Geographic point with optional accuracy and altitude."""

    latitude: float
    longitude: float
    altitude: float | None = None
    accuracy: float | None = None


@dataclass
class Velocity:
    """Velocity information."""

    speed: float  # meters per second
    heading: float  # degrees (0-360)
    unit: str = "MPS"


@dataclass
class DataSource:
    """Information about a data source."""

    source_type: SourceType
    source_id: str
    weight: float = 1.0
    confidence: float = 0.5
    timestamp: datetime | None = None


@dataclass
class Entity:
    """Tracked entity in the ISR system."""

    entity_id: UUID = field(default_factory=uuid4)
    entity_type: EntityType = EntityType.UNKNOWN
    entity_subtype: str | None = None
    display_name: str | None = None
    status: EntityStatus = EntityStatus.ACTIVE
    confidence_score: float = 0.5
    first_observed: datetime = field(default_factory=utcnow)
    last_observed: datetime = field(default_factory=utcnow)
    current_position: GeoPoint | None = None
    current_velocity: Velocity | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    sources: list[DataSource] = field(default_factory=list)
    related_entities: list[UUID] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    classification: DataClassification = DataClassification.UNCLASSIFIED
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class Event:
    """Security or humanitarian event."""

    event_id: UUID = field(default_factory=uuid4)
    event_type: EventType = EventType.OTHER
    event_subtype: str | None = None
    severity: Severity = Severity.MEDIUM
    occurred_at: datetime | None = None
    reported_at: datetime = field(default_factory=utcnow)
    location: GeoPoint | None = None
    location_description: str | None = None
    region: str | None = None
    province: str | None = None
    district: str | None = None
    title: str = ""
    summary: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    casualties_killed: int | None = None
    casualties_wounded: int | None = None
    population_affected: int | None = None
    verification_status: str = "UNVERIFIED"
    sources: list[DataSource] = field(default_factory=list)
    related_entities: list[UUID] = field(default_factory=list)
    related_events: list[UUID] = field(default_factory=list)
    classification: DataClassification = DataClassification.UNCLASSIFIED
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class Alert:
    """System alert for security or operational events."""

    alert_id: UUID = field(default_factory=uuid4)
    category: AlertCategory = AlertCategory.SECURITY
    subcategory: str | None = None
    severity: Severity = Severity.MEDIUM
    title: str = ""
    summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    location: GeoPoint | None = None
    region: str | None = None
    threat_score: int | None = None
    confidence: float = 0.5
    trigger_type: str = "MANUAL"
    trigger_id: str | None = None
    sources: list[DataSource] = field(default_factory=list)
    status: AlertStatus = AlertStatus.OPEN
    assigned_to_user: str | None = None
    assigned_to_team: str | None = None
    response_deadline: datetime | None = None
    resolution_deadline: datetime | None = None
    related_entities: list[UUID] = field(default_factory=list)
    related_events: list[UUID] = field(default_factory=list)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class Anomaly:
    """Detected anomaly from analysis."""

    anomaly_id: UUID = field(default_factory=uuid4)
    domain: AnomalyDomain = AnomalyDomain.GEO_MOVEMENT
    anomaly_subtype: str | None = None
    severity: Severity = Severity.MEDIUM
    severity_score: int = 50
    detected_at: datetime = field(default_factory=utcnow)
    location: GeoPoint | None = None
    region: str | None = None
    description: str = ""
    baseline_stats: dict[str, Any] = field(default_factory=dict)
    observed_stats: dict[str, Any] = field(default_factory=dict)
    model_id: str | None = None
    anomaly_score: float = 0.0
    related_entities: list[UUID] = field(default_factory=list)
    status: str = "OPEN"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class ThreatScore:
    """Threat score calculation result."""

    entity_id: UUID
    overall_score: int
    category: ThreatCategory
    factor_scores: dict[str, dict[str, Any]] = field(default_factory=dict)
    explanation_summary: str | None = None
    key_indicators: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    model_id: str | None = None
    model_version: str | None = None
    context_window_start: datetime | None = None
    context_window_end: datetime | None = None
    trend_direction: str | None = None  # INCREASING, DECREASING, STABLE
    calculated_at: datetime = field(default_factory=utcnow)


@dataclass
class User:
    """User account in the system."""

    user_id: UUID = field(default_factory=uuid4)
    username: str = ""
    email: str | None = None
    display_name: str | None = None
    organization: str | None = None
    roles: list[UserRole] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    status: str = "ACTIVE"
    last_login: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class FieldReport:
    """Field intelligence report from field agents."""

    report_id: UUID = field(default_factory=uuid4)
    report_type: str = "HUMINT"  # HUMINT, OBSERVATION, INCIDENT, CONTACT, SITREP
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    title: str = ""
    description: str = ""
    location: GeoPoint | None = None
    observed_at: datetime | None = None
    confidence: str = "MEDIUM"  # LOW, MEDIUM, HIGH, VERIFIED
    classification: DataClassification = DataClassification.UNCLASSIFIED
    entities_mentioned: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_type: str = "HUMINT"
    additional_context: dict[str, Any] = field(default_factory=dict)
    submitted_by: str | None = None
    reference_number: str = ""
    status: str = "RECEIVED"  # RECEIVED, PROCESSING, ANALYZED, ARCHIVED
    processing_notes: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class FieldAlert:
    """Urgent alert from field agents."""

    alert_id: UUID = field(default_factory=uuid4)
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    alert_type: str = "SECURITY"  # SECURITY, HUMANITARIAN, ENVIRONMENTAL, INFRASTRUCTURE
    title: str = ""
    description: str = ""
    location: GeoPoint | None = None
    immediate_threat: bool = False
    estimated_impact: str | None = None
    recommended_actions: list[str] = field(default_factory=list)
    submitted_by: str | None = None
    reference_number: str = ""
    status: str = "URGENT_PROCESSING"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class Observation:
    """Routine observation from patrol."""

    observation_id: UUID = field(default_factory=uuid4)
    observation_type: str = "MOVEMENT"  # MOVEMENT, GATHERING, INFRASTRUCTURE, ENVIRONMENTAL
    description: str = ""
    location: GeoPoint | None = None
    observed_at: datetime | None = None
    entity_count: int | None = None
    movement_direction: str | None = None  # N, S, E, W, NE, NW, SE, SW
    notable_features: list[str] = field(default_factory=list)
    submitted_by: str | None = None
    reference_number: str = ""
    status: str = "RECEIVED"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class ContactReport:
    """Contact/meeting report from field."""

    contact_id: UUID = field(default_factory=uuid4)
    contact_type: str = "CIVILIAN"  # INFORMANT, LOCAL_OFFICIAL, NGO, CIVILIAN
    contact_name: str | None = None
    organization: str | None = None
    location: GeoPoint | None = None
    meeting_time: datetime | None = None
    duration_minutes: int | None = None
    topic: str = ""
    key_points: list[str] = field(default_factory=list)
    reliability_assessment: str = "UNKNOWN"  # RELIABLE, USUALLY_RELIABLE, UNRELIABLE, UNKNOWN
    follow_up_required: bool = False
    submitted_by: str | None = None
    reference_number: str = ""
    status: str = "RECEIVED"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class MediaAttachment:
    """Media attachment for a submission."""

    media_id: UUID = field(default_factory=uuid4)
    submission_id: UUID | None = None
    filename: str = ""
    size_bytes: int = 0
    media_type: str = "PHOTO"  # PHOTO, VIDEO, AUDIO, DOCUMENT
    content_type: str = ""
    storage_path: str | None = None
    uploaded_by: str | None = None
    uploaded_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationPreference:
    """User notification preferences."""

    user_id: UUID
    email_enabled: bool = True
    email_address: str | None = None
    slack_enabled: bool = False
    sms_enabled: bool = False
    phone_number: str | None = None
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_on_medium: bool = False
    notify_on_low: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    daily_briefing_enabled: bool = True
    daily_briefing_time: str = "08:00"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class NotificationLog:
    """Log of sent notifications."""

    log_id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    channel: str = "email"  # email, slack, sms, websocket
    notification_type: str = "alert"
    title: str = ""
    message: str = ""
    status: str = "sent"  # sent, failed, pending
    sent_at: datetime = field(default_factory=utcnow)
    error_message: str | None = None


@dataclass
class ConfigAuditLog:
    """Audit log for configuration changes."""

    log_id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    username: str = ""
    action: str = "updated"  # created, updated, deleted
    key: str = ""
    old_value: str | None = None
    new_value: str | None = None
    timestamp: datetime = field(default_factory=utcnow)
