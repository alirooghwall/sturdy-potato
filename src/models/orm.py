"""SQLAlchemy ORM models for ISR Platform.

These models define the database schema and are used with Alembic for migrations.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
        list[str]: ARRAY(String),
    }


class UserORM(Base):
    """User account in the database."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    field_reports: Mapped[list["FieldReportORM"]] = relationship(back_populates="submitted_by_user")
    notification_preferences: Mapped["NotificationPreferenceORM | None"] = relationship(back_populates="user")


class FieldReportORM(Base):
    """Field intelligence report in the database."""

    __tablename__ = "field_reports"

    report_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    classification: Mapped[str] = mapped_column(String(50), default="UNCLASSIFIED")
    entities_mentioned: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    source_type: Mapped[str] = mapped_column(String(50), default="HUMINT")
    additional_context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Submission info
    submitted_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", index=True)
    processing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    # Relationships
    submitted_by_user: Mapped["UserORM | None"] = relationship(back_populates="field_reports")
    media_attachments: Mapped[list["MediaAttachmentORM"]] = relationship(back_populates="field_report")


class FieldAlertORM(Base):
    """Urgent field alert in the database."""

    __tablename__ = "field_alerts"

    alert_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    immediate_threat: Mapped[bool] = mapped_column(Boolean, default=False)
    estimated_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_actions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    
    submitted_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="URGENT_PROCESSING", index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ObservationORM(Base):
    """Routine observation in the database."""

    __tablename__ = "observations"

    observation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    observation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entity_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    movement_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notable_features: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    
    submitted_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ContactReportORM(Base):
    """Contact/meeting report in the database."""

    __tablename__ = "contact_reports"

    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    meeting_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    key_points: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    reliability_assessment: Mapped[str] = mapped_column(String(50), default="UNKNOWN")
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    submitted_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MediaAttachmentORM(Base):
    """Media attachment in the database."""

    __tablename__ = "media_attachments"

    media_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_reports.report_id"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    uploaded_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    file_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    field_report: Mapped["FieldReportORM | None"] = relationship(back_populates="media_attachments")


class NotificationPreferenceORM(Base):
    """User notification preferences in the database."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slack_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notify_on_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_high: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_medium: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_on_low: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[str] = mapped_column(String(10), default="22:00")
    quiet_hours_end: Mapped[str] = mapped_column(String(10), default="07:00")
    daily_briefing_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_briefing_time: Mapped[str] = mapped_column(String(10), default="08:00")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    # Relationships
    user: Mapped["UserORM"] = relationship(back_populates="notification_preferences")


class NotificationLogORM(Base):
    """Log of sent notifications in the database."""

    __tablename__ = "notification_logs"

    log_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="sent", index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ConfigAuditLogORM(Base):
    """Audit log for configuration changes in the database."""

    __tablename__ = "config_audit_logs"

    log_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ConfigurationORM(Base):
    """Configuration key-value storage in the database."""

    __tablename__ = "configurations"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EntityORM(Base):
    """Tracked entity in the database."""

    __tablename__ = "entities"

    entity_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    first_observed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_observed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    # Position
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Velocity
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    classification: Mapped[str] = mapped_column(String(50), default="UNCLASSIFIED")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EventORM(Base):
    """Security or humanitarian event in the database."""

    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    casualties_killed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    casualties_wounded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    population_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AlertORM(Base):
    """System alert in the database."""

    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    threat_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    trigger_type: Mapped[str] = mapped_column(String(50), default="MANUAL")
    trigger_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True)
    assigned_to_user: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_to_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
