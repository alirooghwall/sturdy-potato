"""Enumeration types for ISR Platform."""

from enum import Enum


class EntityType(str, Enum):
    """Types of entities tracked by the platform."""

    VEHICLE = "VEHICLE"
    PERSONNEL = "PERSONNEL"
    AIRCRAFT = "AIRCRAFT"
    WATERCRAFT = "WATERCRAFT"
    INSTALLATION = "INSTALLATION"
    EQUIPMENT = "EQUIPMENT"
    WEAPON_SYSTEM = "WEAPON_SYSTEM"
    COMMUNICATION_NODE = "COMMUNICATION_NODE"
    INSURGENT_CELL = "INSURGENT_CELL"
    CIVILIAN_GROUP = "CIVILIAN_GROUP"
    MILITARY_UNIT = "MILITARY_UNIT"
    CONVOY = "CONVOY"
    CHECKPOINT = "CHECKPOINT"
    UNKNOWN = "UNKNOWN"


class EntityStatus(str, Enum):
    """Status of an entity."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    TRACKED = "TRACKED"
    LOST = "LOST"


class EventType(str, Enum):
    """Types of security/humanitarian events."""

    EXPLOSION = "EXPLOSION"
    GUNFIRE = "GUNFIRE"
    IED_DETONATION = "IED_DETONATION"
    BORDER_CROSSING = "BORDER_CROSSING"
    ATTACK = "ATTACK"
    ASSASSINATION = "ASSASSINATION"
    KIDNAPPING = "KIDNAPPING"
    PROTEST = "PROTEST"
    DISPLACEMENT = "DISPLACEMENT"
    HUMANITARIAN_CRISIS = "HUMANITARIAN_CRISIS"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    EARTHQUAKE = "EARTHQUAKE"
    FLOOD = "FLOOD"
    DROUGHT = "DROUGHT"
    INFRASTRUCTURE_DAMAGE = "INFRASTRUCTURE_DAMAGE"
    SUPPLY_DISTRIBUTION = "SUPPLY_DISTRIBUTION"
    MEETING = "MEETING"
    COMMUNICATION = "COMMUNICATION"
    OTHER = "OTHER"


class Severity(str, Enum):
    """Severity levels for events and alerts."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceType(str, Enum):
    """Types of data sources."""

    HUMINT = "HUMINT"
    SIGINT = "SIGINT"
    IMINT = "IMINT"
    OSINT = "OSINT"
    SATELLITE = "SATELLITE"
    DRONE = "DRONE"
    SENSOR = "SENSOR"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    NEWS = "NEWS"
    FIELD_REPORT = "FIELD_REPORT"
    ANALYSIS = "ANALYSIS"
    FUSION = "FUSION"
    UNKNOWN = "UNKNOWN"


class AlertCategory(str, Enum):
    """Categories of alerts."""

    SECURITY = "SECURITY"
    THREAT = "THREAT"
    ANOMALY = "ANOMALY"
    HUMANITARIAN = "HUMANITARIAN"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    COMMUNICATION = "COMMUNICATION"
    LOGISTICS = "LOGISTICS"
    INTELLIGENCE = "INTELLIGENCE"
    SYSTEM = "SYSTEM"


class AlertStatus(str, Enum):
    """Status of an alert."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ESCALATED = "ESCALATED"


class AnomalyDomain(str, Enum):
    """Domains for anomaly detection."""

    GEO_MOVEMENT = "GEO_MOVEMENT"
    NETWORK_TRAFFIC = "NETWORK_TRAFFIC"
    COMMUNICATION = "COMMUNICATION"
    ECONOMIC = "ECONOMIC"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    POPULATION = "POPULATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class ThreatCategory(str, Enum):
    """Threat level categories based on score."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DataClassification(str, Enum):
    """Data classification levels."""

    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"


class UserRole(str, Enum):
    """User roles in the system."""

    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    SENIOR_ANALYST = "SENIOR_ANALYST"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
