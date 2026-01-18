"""Service for field agent submissions and operations."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import (
    ContactReport,
    FieldAlert,
    FieldReport,
    GeoPoint,
    MediaAttachment,
    Observation,
)
from src.models.orm import (
    ContactReportORM,
    FieldAlertORM,
    FieldReportORM,
    MediaAttachmentORM,
    ObservationORM,
)
from src.services.database import get_db_service
from src.services.kafka_bus import get_message_bus


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


logger = logging.getLogger(__name__)


class FieldAgentService:
    """Service for managing field agent submissions."""

    def __init__(self):
        """Initialize the service."""
        self._db_service = None
        self._message_bus = None

    @property
    def db_service(self):
        """Get database service lazily."""
        if self._db_service is None:
            self._db_service = get_db_service()
        return self._db_service

    @property
    def message_bus(self):
        """Get message bus lazily."""
        if self._message_bus is None:
            self._message_bus = get_message_bus()
        return self._message_bus

    async def save_field_report(
        self,
        report_type: str,
        priority: str,
        title: str,
        description: str,
        location: dict[str, Any] | None,
        observed_at: datetime | None,
        confidence: str,
        classification: str,
        entities_mentioned: list[str],
        tags: list[str],
        source_type: str,
        additional_context: dict[str, Any],
        submitted_by: str | None,
        reference_number: str,
    ) -> FieldReport:
        """Save a field report to the database.
        
        Args:
            report_type: Type of report (HUMINT, OBSERVATION, etc.)
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            title: Report title
            description: Report description
            location: Location data dictionary
            observed_at: When the observation was made
            confidence: Confidence level
            classification: Security classification
            entities_mentioned: List of entity names mentioned
            tags: List of tags
            source_type: Type of source
            additional_context: Additional context data
            submitted_by: User ID who submitted
            reference_number: Unique reference number
            
        Returns:
            FieldReport domain object
        """
        report_id = uuid4()
        
        # Create domain object
        geo_point = None
        if location:
            geo_point = GeoPoint(
                latitude=location.get("latitude", 0),
                longitude=location.get("longitude", 0),
                altitude=location.get("altitude_meters"),
                accuracy=location.get("accuracy_meters"),
            )
        
        report = FieldReport(
            report_id=report_id,
            report_type=report_type,
            priority=priority,
            title=title,
            description=description,
            location=geo_point,
            observed_at=observed_at,
            confidence=confidence,
            classification=classification,
            entities_mentioned=entities_mentioned,
            tags=tags,
            source_type=source_type,
            additional_context=additional_context,
            submitted_by=submitted_by,
            reference_number=reference_number,
            status="RECEIVED",
        )
        
        # Save to database
        try:
            async with self.db_service.session() as session:
                orm_report = FieldReportORM(
                    report_id=report_id,
                    report_type=report_type,
                    priority=priority,
                    title=title,
                    description=description,
                    latitude=location.get("latitude") if location else None,
                    longitude=location.get("longitude") if location else None,
                    altitude_meters=location.get("altitude_meters") if location else None,
                    accuracy_meters=location.get("accuracy_meters") if location else None,
                    location_description=location.get("description") if location else None,
                    observed_at=observed_at,
                    confidence=confidence,
                    classification=classification,
                    entities_mentioned=entities_mentioned,
                    tags=tags,
                    source_type=source_type,
                    additional_context=additional_context,
                    submitted_by_id=submitted_by,
                    reference_number=reference_number,
                    status="RECEIVED",
                )
                session.add(orm_report)
                await session.commit()
                logger.info(f"Field report saved to database: {reference_number}")
        except Exception as e:
            logger.warning(f"Failed to save field report to database: {e}")
            # Continue without database - report is still created in memory
        
        # Publish to Kafka
        try:
            await self.message_bus.publish(
                topic="isr.field.reports",
                message={
                    "report_id": str(report_id),
                    "report_type": report_type,
                    "priority": priority,
                    "title": title,
                    "reference_number": reference_number,
                    "submitted_by": submitted_by,
                    "timestamp": utcnow().isoformat(),
                },
            )
            logger.info(f"Field report published to Kafka: {reference_number}")
        except Exception as e:
            logger.warning(f"Failed to publish field report to Kafka: {e}")
        
        # Trigger ML analysis for high priority reports
        if priority in ("HIGH", "CRITICAL"):
            try:
                await self._trigger_ml_analysis(report)
                logger.info(f"ML analysis triggered for high-priority report: {reference_number}")
            except Exception as e:
                logger.warning(f"Failed to trigger ML analysis: {e}")
        
        return report

    async def save_field_alert(
        self,
        severity: str,
        alert_type: str,
        title: str,
        description: str,
        location: dict[str, Any] | None,
        immediate_threat: bool,
        estimated_impact: str | None,
        recommended_actions: list[str],
        submitted_by: str | None,
        reference_number: str,
    ) -> FieldAlert:
        """Save a field alert to the database.
        
        Args:
            severity: Alert severity
            alert_type: Type of alert
            title: Alert title
            description: Alert description
            location: Location data
            immediate_threat: Whether this is an immediate threat
            estimated_impact: Estimated impact assessment
            recommended_actions: List of recommended actions
            submitted_by: User ID who submitted
            reference_number: Unique reference number
            
        Returns:
            FieldAlert domain object
        """
        alert_id = uuid4()
        
        geo_point = None
        if location:
            geo_point = GeoPoint(
                latitude=location.get("latitude", 0),
                longitude=location.get("longitude", 0),
                altitude=location.get("altitude_meters"),
                accuracy=location.get("accuracy_meters"),
            )
        
        alert = FieldAlert(
            alert_id=alert_id,
            severity=severity,
            alert_type=alert_type,
            title=title,
            description=description,
            location=geo_point,
            immediate_threat=immediate_threat,
            estimated_impact=estimated_impact,
            recommended_actions=recommended_actions,
            submitted_by=submitted_by,
            reference_number=reference_number,
            status="URGENT_PROCESSING",
        )
        
        # Save to database
        try:
            async with self.db_service.session() as session:
                orm_alert = FieldAlertORM(
                    alert_id=alert_id,
                    severity=severity,
                    alert_type=alert_type,
                    title=title,
                    description=description,
                    latitude=location.get("latitude") if location else None,
                    longitude=location.get("longitude") if location else None,
                    altitude_meters=location.get("altitude_meters") if location else None,
                    accuracy_meters=location.get("accuracy_meters") if location else None,
                    location_description=location.get("description") if location else None,
                    immediate_threat=immediate_threat,
                    estimated_impact=estimated_impact,
                    recommended_actions=recommended_actions,
                    submitted_by_id=submitted_by,
                    reference_number=reference_number,
                    status="URGENT_PROCESSING",
                )
                session.add(orm_alert)
                await session.commit()
                logger.info(f"Field alert saved to database: {reference_number}")
        except Exception as e:
            logger.warning(f"Failed to save field alert to database: {e}")
        
        # Publish to Kafka for immediate processing
        try:
            await self.message_bus.publish(
                topic="isr.alerts.field",
                message={
                    "alert_id": str(alert_id),
                    "severity": severity,
                    "alert_type": alert_type,
                    "title": title,
                    "immediate_threat": immediate_threat,
                    "reference_number": reference_number,
                    "timestamp": utcnow().isoformat(),
                },
            )
            logger.info(f"Field alert published to Kafka: {reference_number}")
        except Exception as e:
            logger.warning(f"Failed to publish field alert to Kafka: {e}")
        
        # Trigger notifications for immediate threats
        if immediate_threat or severity == "CRITICAL":
            try:
                await self._trigger_immediate_notification(alert)
                logger.info(f"Immediate notification triggered for alert: {reference_number}")
            except Exception as e:
                logger.warning(f"Failed to trigger immediate notification: {e}")
        
        return alert

    async def save_observation(
        self,
        observation_type: str,
        description: str,
        location: dict[str, Any] | None,
        observed_at: datetime | None,
        entity_count: int | None,
        movement_direction: str | None,
        notable_features: list[str],
        submitted_by: str | None,
        reference_number: str,
    ) -> Observation:
        """Save an observation to the database.
        
        Args:
            observation_type: Type of observation
            description: Observation description
            location: Location data
            observed_at: When observed
            entity_count: Number of entities observed
            movement_direction: Direction of movement
            notable_features: Notable features list
            submitted_by: User ID who submitted
            reference_number: Unique reference number
            
        Returns:
            Observation domain object
        """
        observation_id = uuid4()
        
        geo_point = None
        if location:
            geo_point = GeoPoint(
                latitude=location.get("latitude", 0),
                longitude=location.get("longitude", 0),
                altitude=location.get("altitude_meters"),
                accuracy=location.get("accuracy_meters"),
            )
        
        observation = Observation(
            observation_id=observation_id,
            observation_type=observation_type,
            description=description,
            location=geo_point,
            observed_at=observed_at,
            entity_count=entity_count,
            movement_direction=movement_direction,
            notable_features=notable_features,
            submitted_by=submitted_by,
            reference_number=reference_number,
            status="RECEIVED",
        )
        
        # Save to database
        try:
            async with self.db_service.session() as session:
                orm_observation = ObservationORM(
                    observation_id=observation_id,
                    observation_type=observation_type,
                    description=description,
                    latitude=location.get("latitude") if location else None,
                    longitude=location.get("longitude") if location else None,
                    altitude_meters=location.get("altitude_meters") if location else None,
                    accuracy_meters=location.get("accuracy_meters") if location else None,
                    location_description=location.get("description") if location else None,
                    observed_at=observed_at,
                    entity_count=entity_count,
                    movement_direction=movement_direction,
                    notable_features=notable_features,
                    submitted_by_id=submitted_by,
                    reference_number=reference_number,
                    status="RECEIVED",
                )
                session.add(orm_observation)
                await session.commit()
                logger.info(f"Observation saved to database: {reference_number}")
        except Exception as e:
            logger.warning(f"Failed to save observation to database: {e}")
        
        # Publish to Kafka
        try:
            await self.message_bus.publish(
                topic="isr.observations",
                message={
                    "observation_id": str(observation_id),
                    "observation_type": observation_type,
                    "reference_number": reference_number,
                    "timestamp": utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish observation to Kafka: {e}")
        
        return observation

    async def save_contact_report(
        self,
        contact_type: str,
        contact_name: str | None,
        organization: str | None,
        location: dict[str, Any] | None,
        meeting_time: datetime | None,
        duration_minutes: int | None,
        topic: str,
        key_points: list[str],
        reliability_assessment: str,
        follow_up_required: bool,
        submitted_by: str | None,
        reference_number: str,
    ) -> ContactReport:
        """Save a contact report to the database.
        
        Args:
            contact_type: Type of contact
            contact_name: Name of contact (optional)
            organization: Contact's organization
            location: Location data
            meeting_time: When meeting occurred
            duration_minutes: Meeting duration
            topic: Topic of discussion
            key_points: Key points from meeting
            reliability_assessment: Reliability of source
            follow_up_required: Whether follow-up is needed
            submitted_by: User ID who submitted
            reference_number: Unique reference number
            
        Returns:
            ContactReport domain object
        """
        contact_id = uuid4()
        
        geo_point = None
        if location:
            geo_point = GeoPoint(
                latitude=location.get("latitude", 0),
                longitude=location.get("longitude", 0),
            )
        
        contact = ContactReport(
            contact_id=contact_id,
            contact_type=contact_type,
            contact_name=contact_name,
            organization=organization,
            location=geo_point,
            meeting_time=meeting_time,
            duration_minutes=duration_minutes,
            topic=topic,
            key_points=key_points,
            reliability_assessment=reliability_assessment,
            follow_up_required=follow_up_required,
            submitted_by=submitted_by,
            reference_number=reference_number,
            status="RECEIVED",
        )
        
        # Save to database
        try:
            async with self.db_service.session() as session:
                orm_contact = ContactReportORM(
                    contact_id=contact_id,
                    contact_type=contact_type,
                    contact_name=contact_name,
                    organization=organization,
                    latitude=location.get("latitude") if location else None,
                    longitude=location.get("longitude") if location else None,
                    location_description=location.get("description") if location else None,
                    meeting_time=meeting_time,
                    duration_minutes=duration_minutes,
                    topic=topic,
                    key_points=key_points,
                    reliability_assessment=reliability_assessment,
                    follow_up_required=follow_up_required,
                    submitted_by_id=submitted_by,
                    reference_number=reference_number,
                    status="RECEIVED",
                )
                session.add(orm_contact)
                await session.commit()
                logger.info(f"Contact report saved to database: {reference_number}")
        except Exception as e:
            logger.warning(f"Failed to save contact report to database: {e}")
        
        # Publish to Kafka
        try:
            await self.message_bus.publish(
                topic="isr.contacts",
                message={
                    "contact_id": str(contact_id),
                    "contact_type": contact_type,
                    "reliability": reliability_assessment,
                    "follow_up_required": follow_up_required,
                    "reference_number": reference_number,
                    "timestamp": utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish contact report to Kafka: {e}")
        
        return contact

    async def save_media_attachment(
        self,
        submission_id: str | None,
        filename: str,
        size_bytes: int,
        media_type: str,
        content_type: str,
        storage_path: str | None,
        uploaded_by: str | None,
        metadata: dict[str, Any] | None,
    ) -> MediaAttachment:
        """Save a media attachment record to the database.
        
        Args:
            submission_id: ID of the submission this is attached to
            filename: Original filename
            size_bytes: File size in bytes
            media_type: Type of media (PHOTO, VIDEO, etc.)
            content_type: MIME content type
            storage_path: Path where file is stored
            uploaded_by: User ID who uploaded
            metadata: Additional metadata
            
        Returns:
            MediaAttachment domain object
        """
        media_id = uuid4()
        
        attachment = MediaAttachment(
            media_id=media_id,
            submission_id=UUID(submission_id) if submission_id else None,
            filename=filename,
            size_bytes=size_bytes,
            media_type=media_type,
            content_type=content_type,
            storage_path=storage_path,
            uploaded_by=uploaded_by,
            metadata=metadata or {},
        )
        
        # Save to database
        try:
            async with self.db_service.session() as session:
                orm_attachment = MediaAttachmentORM(
                    media_id=media_id,
                    submission_id=submission_id,
                    filename=filename,
                    size_bytes=size_bytes,
                    media_type=media_type,
                    content_type=content_type,
                    storage_path=storage_path,
                    uploaded_by_id=uploaded_by,
                    file_metadata=metadata or {},
                )
                session.add(orm_attachment)
                await session.commit()
                logger.info(f"Media attachment saved to database: {filename}")
        except Exception as e:
            logger.warning(f"Failed to save media attachment to database: {e}")
        
        return attachment

    async def get_user_submissions(
        self,
        user_id: str,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get submissions made by a user.
        
        Args:
            user_id: User ID to query
            status_filter: Optional status filter
            limit: Maximum results
            offset: Results offset
            
        Returns:
            Dictionary with submissions and pagination info
        """
        submissions = []
        total = 0
        
        try:
            async with self.db_service.session() as session:
                # Query field reports
                query = select(FieldReportORM).where(
                    FieldReportORM.submitted_by_id == user_id
                )
                if status_filter:
                    query = query.where(FieldReportORM.status == status_filter)
                query = query.order_by(FieldReportORM.created_at.desc())
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                reports = result.scalars().all()
                
                for report in reports:
                    submissions.append({
                        "submission_id": str(report.report_id),
                        "type": "FIELD_REPORT",
                        "subtype": report.report_type,
                        "title": report.title,
                        "reference_number": report.reference_number,
                        "status": report.status,
                        "priority": report.priority,
                        "created_at": report.created_at.isoformat() if report.created_at else None,
                    })
                
                # Count total
                count_query = select(FieldReportORM).where(
                    FieldReportORM.submitted_by_id == user_id
                )
                if status_filter:
                    count_query = count_query.where(FieldReportORM.status == status_filter)
                count_result = await session.execute(count_query)
                total = len(count_result.scalars().all())
                
        except Exception as e:
            logger.warning(f"Failed to query user submissions from database: {e}")
        
        return {
            "submissions": submissions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_submission_by_id(
        self,
        submission_id: str,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific submission by ID.
        
        Args:
            submission_id: Submission ID
            user_id: Optional user ID for access check
            
        Returns:
            Submission data dictionary or None
        """
        try:
            async with self.db_service.session() as session:
                # Try field report first
                query = select(FieldReportORM).where(
                    FieldReportORM.report_id == submission_id
                )
                result = await session.execute(query)
                report = result.scalar_one_or_none()
                
                if report:
                    # Check user access if user_id provided
                    if user_id and str(report.submitted_by_id) != user_id:
                        return None
                    
                    return {
                        "submission_id": str(report.report_id),
                        "type": "FIELD_REPORT",
                        "subtype": report.report_type,
                        "title": report.title,
                        "description": report.description,
                        "reference_number": report.reference_number,
                        "status": report.status,
                        "priority": report.priority,
                        "confidence": report.confidence,
                        "classification": report.classification,
                        "location": {
                            "latitude": report.latitude,
                            "longitude": report.longitude,
                            "description": report.location_description,
                        } if report.latitude else None,
                        "observed_at": report.observed_at.isoformat() if report.observed_at else None,
                        "submitted_at": report.created_at.isoformat() if report.created_at else None,
                        "processed_at": report.updated_at.isoformat() if report.updated_at else None,
                        "feedback": report.processing_notes,
                    }
                
        except Exception as e:
            logger.warning(f"Failed to query submission from database: {e}")
        
        return None

    async def _trigger_ml_analysis(self, report: FieldReport) -> None:
        """Trigger ML analysis pipeline for a field report.
        
        Args:
            report: The field report to analyze
        """
        await self.message_bus.publish(
            topic="isr.ml.analysis",
            message={
                "type": "FIELD_REPORT_ANALYSIS",
                "report_id": str(report.report_id),
                "title": report.title,
                "description": report.description,
                "priority": report.priority,
                "entities_mentioned": report.entities_mentioned,
                "tags": report.tags,
                "timestamp": utcnow().isoformat(),
            },
        )

    async def _trigger_immediate_notification(self, alert: FieldAlert) -> None:
        """Trigger immediate notification for a critical alert.
        
        Args:
            alert: The field alert
        """
        from src.services.notification_service import get_notification_service
        
        notification_service = get_notification_service()
        
        alert_data = {
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "reference_number": alert.reference_number,
            "location": {
                "description": f"{alert.location.latitude}, {alert.location.longitude}" 
                if alert.location else "Unknown"
            },
            "immediate_threat": alert.immediate_threat,
        }
        
        # Send to all channels for critical alerts
        await notification_service.send_alert_notification(
            alert_data,
            channels=["email", "slack", "sms", "websocket"],
        )


# Global service instance
_field_agent_service: FieldAgentService | None = None


def get_field_agent_service() -> FieldAgentService:
    """Get the field agent service instance."""
    global _field_agent_service
    if _field_agent_service is None:
        _field_agent_service = FieldAgentService()
    return _field_agent_service
