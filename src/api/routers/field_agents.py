"""Field agent submission endpoints for HUMINT and field intelligence."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Dependency for getting current user
async def get_current_user(token: str = Depends(lambda: "mock_user")) -> dict:
    """Get current authenticated user. TODO: Implement proper auth dependency."""
    return {"user_id": "mock_user", "username": "mock_user", "roles": ["analyst"]}


class LocationModel(BaseModel):
    """Location information."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude_meters: float | None = None
    accuracy_meters: float | None = None
    description: str | None = Field(None, max_length=500)


class FieldReportSubmission(BaseModel):
    """Field intelligence report submission."""

    report_type: str = Field(..., description="HUMINT, OBSERVATION, INCIDENT, CONTACT, SITREP")
    priority: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    location: LocationModel
    observed_at: datetime
    confidence: str = Field(..., description="LOW, MEDIUM, HIGH, VERIFIED")
    classification: str = Field("UNCLASSIFIED", description="UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP_SECRET")
    entities_mentioned: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_type: str = Field("HUMINT", description="HUMINT, IMINT, SIGINT, OSINT")
    additional_context: dict[str, Any] = Field(default_factory=dict)


class AlertSubmission(BaseModel):
    """Urgent alert submission from field."""

    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    alert_type: str = Field(..., description="SECURITY, HUMANITARIAN, ENVIRONMENTAL, INFRASTRUCTURE")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    location: LocationModel
    immediate_threat: bool = Field(False, description="Requires immediate action")
    estimated_impact: str | None = Field(None, description="Expected impact assessment")
    recommended_actions: list[str] = Field(default_factory=list)


class ObservationSubmission(BaseModel):
    """Routine observation submission."""

    observation_type: str = Field(..., description="MOVEMENT, GATHERING, INFRASTRUCTURE, ENVIRONMENTAL")
    description: str = Field(..., min_length=10, max_length=2000)
    location: LocationModel
    observed_at: datetime
    entity_count: int | None = Field(None, ge=0, description="Number of people/vehicles observed")
    movement_direction: str | None = Field(None, description="N, S, E, W, NE, NW, SE, SW")
    notable_features: list[str] = Field(default_factory=list)


class ContactReportSubmission(BaseModel):
    """Contact/meeting report from field."""

    contact_type: str = Field(..., description="INFORMANT, LOCAL_OFFICIAL, NGO, CIVILIAN")
    contact_name: str | None = Field(None, max_length=100, description="Optional, can be anonymous")
    organization: str | None = Field(None, max_length=200)
    location: LocationModel
    meeting_time: datetime
    duration_minutes: int | None = Field(None, ge=0)
    topic: str = Field(..., min_length=5, max_length=200)
    key_points: list[str] = Field(..., min_items=1)
    reliability_assessment: str = Field(..., description="RELIABLE, USUALLY_RELIABLE, UNRELIABLE, UNKNOWN")
    follow_up_required: bool = False


class SubmissionResponse(BaseModel):
    """Response after submission."""

    submission_id: str
    status: str
    message: str
    timestamp: datetime
    reference_number: str


class MediaUploadResponse(BaseModel):
    """Response after media upload."""

    media_id: str
    filename: str
    size_bytes: int
    media_type: str
    uploaded_at: datetime


@router.post("/submit-report", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_field_report(
    report: FieldReportSubmission,
    current_user: dict = Depends(get_current_user),
) -> SubmissionResponse:
    """Submit intelligence report from field agent.
    
    This endpoint allows field agents to submit HUMINT and other intelligence reports
    from the field with location, time, and classification information.
    """
    # Generate unique IDs
    submission_id = str(uuid4())
    reference_number = f"FR-{utcnow().strftime('%Y%m%d')}-{submission_id[:8].upper()}"
    
    # TODO: Save to database
    # TODO: Publish to Kafka topic: isr.field.reports
    # TODO: Trigger ML analysis pipeline
    # TODO: If priority HIGH/CRITICAL, generate alert
    
    # Mock response
    return SubmissionResponse(
        submission_id=submission_id,
        status="RECEIVED",
        message=f"Field report received and queued for processing. Priority: {report.priority}",
        timestamp=utcnow(),
        reference_number=reference_number,
    )


@router.post("/submit-alert", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_field_alert(
    alert: AlertSubmission,
    current_user: dict = Depends(get_current_user),
) -> SubmissionResponse:
    """Submit urgent alert from field.
    
    For time-sensitive security threats requiring immediate attention.
    Triggers high-priority notification workflow.
    """
    submission_id = str(uuid4())
    reference_number = f"FA-{utcnow().strftime('%Y%m%d')}-{submission_id[:8].upper()}"
    
    # TODO: Save to database with URGENT flag
    # TODO: Publish to: isr.alerts.field
    # TODO: Trigger immediate notification (email, SMS, Slack)
    # TODO: Escalate if immediate_threat=True
    
    return SubmissionResponse(
        submission_id=submission_id,
        status="URGENT_PROCESSING",
        message=f"Alert received. Severity: {alert.severity}. Notifying duty officer.",
        timestamp=utcnow(),
        reference_number=reference_number,
    )


@router.post("/submit-observation", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_observation(
    observation: ObservationSubmission,
    current_user: dict = Depends(get_current_user),
) -> SubmissionResponse:
    """Submit routine observation from patrol."""
    submission_id = str(uuid4())
    reference_number = f"OB-{utcnow().strftime('%Y%m%d')}-{submission_id[:8].upper()}"
    
    # TODO: Save to database
    # TODO: Aggregate observations for pattern analysis
    # TODO: Check for anomalies
    
    return SubmissionResponse(
        submission_id=submission_id,
        status="RECEIVED",
        message="Observation recorded and added to analysis queue.",
        timestamp=utcnow(),
        reference_number=reference_number,
    )


@router.post("/submit-contact-report", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_report(
    contact: ContactReportSubmission,
    current_user: dict = Depends(get_current_user),
) -> SubmissionResponse:
    """Submit contact/meeting report."""
    submission_id = str(uuid4())
    reference_number = f"CR-{utcnow().strftime('%Y%m%d')}-{submission_id[:8].upper()}"
    
    # TODO: Save to database
    # TODO: Track source reliability over time
    # TODO: Link to source management system
    # TODO: Schedule follow-up if required
    
    return SubmissionResponse(
        submission_id=submission_id,
        status="RECEIVED",
        message="Contact report received. Source reliability noted.",
        timestamp=utcnow(),
        reference_number=reference_number,
    )


@router.post("/upload-media", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    submission_id: str = None,
    media_type: str = "PHOTO",
    current_user: dict = Depends(get_current_user),
) -> MediaUploadResponse:
    """Upload photo/video evidence for a submission.
    
    Supports: PHOTO, VIDEO, AUDIO, DOCUMENT
    Max size: 50MB per file
    """
    # Validate file type
    allowed_types = {
        "PHOTO": ["image/jpeg", "image/png", "image/webp"],
        "VIDEO": ["video/mp4", "video/quicktime"],
        "AUDIO": ["audio/mpeg", "audio/wav"],
        "DOCUMENT": ["application/pdf", "application/msword"],
    }
    
    if file.content_type not in allowed_types.get(media_type, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type for {media_type}",
        )
    
    # Check file size (50MB max)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Max 50MB.",
        )
    
    # TODO: Save file to storage (S3/MinIO/local)
    # TODO: Extract metadata (EXIF for photos)
    # TODO: Link to submission_id if provided
    # TODO: Run virus scan
    # TODO: Generate thumbnail for images
    
    media_id = str(uuid4())
    
    return MediaUploadResponse(
        media_id=media_id,
        filename=file.filename,
        size_bytes=file_size,
        media_type=media_type,
        uploaded_at=utcnow(),
    )


@router.get("/my-submissions")
async def get_my_submissions(
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get submissions made by current user."""
    # TODO: Query database for user's submissions
    # TODO: Filter by status if provided
    # TODO: Return paginated results
    
    return {
        "submissions": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/submission/{submission_id}")
async def get_submission_status(
    submission_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get status of a specific submission."""
    # TODO: Query database
    # TODO: Check user has access (own submission or admin)
    # TODO: Return full submission details
    
    return {
        "submission_id": str(submission_id),
        "status": "PROCESSED",
        "submitted_at": utcnow().isoformat(),
        "processed_at": utcnow().isoformat(),
        "feedback": "Report analyzed. No immediate action required.",
    }


@router.get("/templates")
async def get_submission_templates(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get quick submission templates for common scenarios."""
    return {
        "templates": [
            {
                "id": "suspicious_vehicle",
                "name": "Suspicious Vehicle",
                "type": "OBSERVATION",
                "fields": ["vehicle_type", "occupants", "direction", "weapons_visible"],
            },
            {
                "id": "ied_threat",
                "name": "IED Threat",
                "type": "ALERT",
                "priority": "CRITICAL",
                "fields": ["location", "description", "confidence"],
            },
            {
                "id": "crowd_gathering",
                "name": "Crowd Gathering",
                "type": "OBSERVATION",
                "fields": ["size", "behavior", "purpose"],
            },
            {
                "id": "checkpoint_activity",
                "name": "Checkpoint Activity",
                "type": "OBSERVATION",
                "fields": ["location", "personnel_count", "equipment"],
            },
            {
                "id": "humanitarian_need",
                "name": "Humanitarian Need",
                "type": "ALERT",
                "priority": "HIGH",
                "fields": ["affected_population", "need_type", "urgency"],
            },
        ]
    }


@router.get("/quick-intel")
async def submit_quick_intel(
    text: str,
    priority: str = "MEDIUM",
    current_user: dict = Depends(get_current_user),
) -> SubmissionResponse:
    """Ultra-fast intelligence submission - just text and priority.
    
    For urgent situations where full form is too slow.
    System will auto-detect location, entities, and threat level.
    """
    submission_id = str(uuid4())
    reference_number = f"QI-{utcnow().strftime('%Y%m%d')}-{submission_id[:8].upper()}"
    
    # TODO: Use ML to extract:
    # - Entities (NER)
    # - Location (if mentioned)
    # - Threat level
    # - Classification suggestion
    
    return SubmissionResponse(
        submission_id=submission_id,
        status="AUTO_PROCESSING",
        message="Quick intel received. Auto-analyzing content.",
        timestamp=utcnow(),
        reference_number=reference_number,
    )
