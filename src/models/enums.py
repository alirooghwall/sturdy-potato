"""Enumeration types for ISR Platform."""

from enum import Enum


class Severity(str, Enum):
    """Severity levels for events, alerts, and anomalies."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntityType(str, Enum):
    """Types of tracked entities."""

    VEHICLE = "VEHICLE"
    PERSONNEL = "PERSONNEL"
    FACILITY = "FACILITY"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    AIRCRAFT = "AIRCRAFT"
    WATERCRAFT = "WATERCRAFT"
    INSURGENT_CELL = "INSURGENT_CELL"
    BORDER_CROSSING = "BORDER_CROSSING"
    REFUGEE_GROUP = "REFUGEE_GROUP"
    UNKNOWN = "UNKNOWN"


class EntityStatus(str, Enum):
    """Status of tracked entities."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"


class EventType(str, Enum):
    """Types of security and humanitarian events."""

    EXPLOSION = "EXPLOSION"
    GUNFIRE = "GUNFIRE"
    IED = "IED"
    ATTACK = "ATTACK"
    PROTEST = "PROTEST"
    CHECKPOINT = "CHECKPOINT"
    BORDER_INCIDENT = "BORDER_INCIDENT"
    EARTHQUAKE = "EARTHQUAKE"
    FLOOD = "FLOOD"
    DROUGHT = "DROUGHT"
    LANDSLIDE = "LANDSLIDE"
    HUMANITARIAN = "HUMANITARIAN"
    CYBER = "CYBER"
    DISINFORMATION = "DISINFORMATION"
    OTHER = "OTHER"


class AlertCategory(str, Enum):
    """Categories of alerts."""

    SECURITY = "SECURITY"
    HUMANITARIAN = "HUMANITARIAN"
    CYBER = "CYBER"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DISASTER = "DISASTER"
    DISINFORMATION = "DISINFORMATION"
    INTELLIGENCE = "INTELLIGENCE"
    SYSTEM = "SYSTEM"


class AlertStatus(str, Enum):
    """Status of alerts."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ESCALATED = "ESCALATED"


class SourceType(str, Enum):
    """Types of intelligence sources."""

    SATELLITE = "SATELLITE"
    UAV = "UAV"
    SIGINT = "SIGINT"
    HUMINT = "HUMINT"
    OSINT = "OSINT"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    CYBER_TELEMETRY = "CYBER_TELEMETRY"
    GROUND_SENSOR = "GROUND_SENSOR"
    TRAFFIC_CAMERA = "TRAFFIC_CAMERA"
    HUMANITARIAN = "HUMANITARIAN"
    NEWS = "NEWS"
    RADIO = "RADIO"
    UNKNOWN = "UNKNOWN"


class AnomalyDomain(str, Enum):
    """Domains for anomaly detection."""

    GEO_MOVEMENT = "GEO_MOVEMENT"
    NETWORK_TRAFFIC = "NETWORK_TRAFFIC"
    ECONOMIC = "ECONOMIC"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    CYBER = "CYBER"
    HUMANITARIAN = "HUMANITARIAN"


class ThreatCategory(str, Enum):
    """Threat level categories."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
