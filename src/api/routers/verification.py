"""Source verification endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.services.source_verification import (
    SourceCategory,
    SourceIdentity,
    VerificationMethod,
    VerificationStatus,
    get_verification_service,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class SourceIdentityRequest(BaseModel):
    """Request for source identity information."""
    display_name: str
    legal_name: str | None = None
    category: SourceCategory
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    country: str | None = None
    city: str | None = None
    organization: str | None = None
    position: str | None = None
    registration_number: str | None = None
    twitter_handle: str | None = None
    telegram_username: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerifySourceRequest(BaseModel):
    """Request to verify a source."""
    source_id: str
    identity: SourceIdentityRequest
    methods: list[VerificationMethod]


class VerificationRequestRequest(BaseModel):
    """Request for verification."""
    source_id: str
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    reason: str
    methods: list[VerificationMethod]


class RevokeVerificationRequest(BaseModel):
    """Request to revoke verification."""
    source_id: str
    reason: str


@router.post("/verify")
async def verify_source(
    request: VerifySourceRequest,
    user: Annotated[dict, Depends(require_permission("verification:write"))],
) -> dict[str, Any]:
    """Verify a source."""
    service = get_verification_service()
    
    # Convert request to SourceIdentity
    identity = SourceIdentity(
        source_id=request.source_id,
        display_name=request.identity.display_name,
        legal_name=request.identity.legal_name,
        category=request.identity.category,
        email=request.identity.email,
        phone=request.identity.phone,
        website=request.identity.website,
        country=request.identity.country,
        city=request.identity.city,
        organization=request.identity.organization,
        position=request.identity.position,
        registration_number=request.identity.registration_number,
        twitter_handle=request.identity.twitter_handle,
        telegram_username=request.identity.telegram_username,
        metadata=request.identity.metadata,
    )
    
    # Perform verification
    record = service.verify_source(
        source_id=request.source_id,
        identity=identity,
        methods=request.methods,
        verified_by=user["username"],
    )
    
    return {
        "record_id": str(record.record_id),
        "source_id": record.source_id,
        "status": record.status.value,
        "verification_level": record.verification_level,
        "identity_confidence": record.identity_confidence,
        "legitimacy_score": record.legitimacy_score,
        "authenticity_score": record.authenticity_score,
        "badges": record.badges,
        "warnings": record.warnings,
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "checks_performed": len(record.checks),
        "checks": [
            {
                "check_id": str(c.check_id),
                "type": c.check_type.value,
                "status": c.status,
                "confidence": c.confidence,
                "details": c.details,
                "performed_at": c.performed_at.isoformat(),
            }
            for c in record.checks
        ],
    }


@router.get("/records/{source_id}")
async def get_verification_record(
    source_id: str,
    user: Annotated[dict, Depends(require_permission("verification:read"))],
) -> dict[str, Any]:
    """Get verification record for a source."""
    service = get_verification_service()
    record = service.get_verification_record(source_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification record for source {source_id} not found",
        )
    
    return {
        "record_id": str(record.record_id),
        "source_id": record.source_id,
        "status": record.status.value,
        "verification_level": record.verification_level,
        "identity": {
            "display_name": record.identity.display_name,
            "legal_name": record.identity.legal_name,
            "category": record.identity.category.value,
            "email": record.identity.email,
            "phone": record.identity.phone,
            "website": record.identity.website,
            "country": record.identity.country,
            "city": record.identity.city,
            "organization": record.identity.organization,
            "position": record.identity.position,
        },
        "scores": {
            "identity_confidence": record.identity_confidence,
            "legitimacy_score": record.legitimacy_score,
            "authenticity_score": record.authenticity_score,
        },
        "badges": record.badges,
        "certifications": record.certifications,
        "warnings": record.warnings,
        "created_at": record.created_at.isoformat(),
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "verified_by": record.verified_by,
        "checks": [
            {
                "check_id": str(c.check_id),
                "type": c.check_type.value,
                "status": c.status,
                "confidence": c.confidence,
                "details": c.details,
                "evidence": c.evidence,
                "performed_at": c.performed_at.isoformat(),
                "performed_by": c.performed_by,
            }
            for c in record.checks
        ],
        "history": record.history,
    }


@router.get("/check/{source_id}")
async def check_verification_status(
    source_id: str,
    user: Annotated[dict, Depends(require_permission("verification:read"))],
) -> dict[str, Any]:
    """Quick check if source is verified."""
    service = get_verification_service()
    
    is_verified = service.is_verified(source_id)
    verification_level = service.get_verification_level(source_id)
    
    record = service.get_verification_record(source_id) if is_verified else None
    
    return {
        "source_id": source_id,
        "is_verified": is_verified,
        "verification_level": verification_level,
        "status": record.status.value if record else "UNKNOWN",
        "badges": record.badges if record else [],
        "expires_at": record.expires_at.isoformat() if record and record.expires_at else None,
    }


@router.post("/requests/submit")
async def submit_verification_request(
    request: VerificationRequestRequest,
    user: Annotated[dict, Depends(require_permission("verification:request"))],
) -> dict[str, Any]:
    """Submit a verification request."""
    service = get_verification_service()
    
    # Validate priority
    if request.priority not in ["HIGH", "MEDIUM", "LOW"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority must be HIGH, MEDIUM, or LOW",
        )
    
    verification_request = service.request_verification(
        source_id=request.source_id,
        requested_by=user["username"],
        priority=request.priority,
        reason=request.reason,
        methods=request.methods,
    )
    
    return {
        "request_id": str(verification_request.request_id),
        "source_id": verification_request.source_id,
        "status": verification_request.status,
        "priority": verification_request.priority,
        "requested_at": verification_request.requested_at.isoformat(),
        "methods_requested": [m.value for m in verification_request.methods_requested],
    }


@router.get("/requests")
async def list_verification_requests(
    user: Annotated[dict, Depends(require_permission("verification:read"))],
    status_filter: str | None = Query(default=None, alias="status"),
    priority_filter: str | None = Query(default=None, alias="priority"),
) -> dict[str, Any]:
    """List verification requests."""
    service = get_verification_service()
    
    requests = service.list_verification_requests(
        status=status_filter,
        priority=priority_filter,
    )
    
    return {
        "total": len(requests),
        "requests": [
            {
                "request_id": str(r.request_id),
                "source_id": r.source_id,
                "requested_by": r.requested_by,
                "requested_at": r.requested_at.isoformat(),
                "priority": r.priority,
                "status": r.status,
                "reason": r.reason,
                "methods_requested": [m.value for m in r.methods_requested],
                "assigned_to": r.assigned_to,
            }
            for r in requests
        ],
    }


@router.post("/revoke")
async def revoke_verification(
    request: RevokeVerificationRequest,
    user: Annotated[dict, Depends(require_permission("verification:revoke"))],
) -> dict[str, Any]:
    """Revoke source verification."""
    service = get_verification_service()
    
    success = service.revoke_verification(
        source_id=request.source_id,
        reason=request.reason,
        revoked_by=user["username"],
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification record for source {request.source_id} not found",
        )
    
    return {
        "source_id": request.source_id,
        "revoked": True,
        "revoked_by": user["username"],
        "revoked_at": utcnow().isoformat(),
        "reason": request.reason,
    }


@router.get("/stats")
async def get_verification_stats(
    user: Annotated[dict, Depends(require_permission("verification:read"))],
) -> dict[str, Any]:
    """Get verification statistics."""
    service = get_verification_service()
    return service.get_stats()


@router.get("/methods")
async def get_verification_methods(
    user: Annotated[dict, Depends(require_permission("verification:read"))],
) -> dict[str, Any]:
    """Get available verification methods."""
    return {
        "methods": [
            {
                "name": method.value,
                "description": _get_method_description(method),
            }
            for method in VerificationMethod
        ]
    }


def _get_method_description(method: VerificationMethod) -> str:
    """Get description for verification method."""
    descriptions = {
        VerificationMethod.DOMAIN_VALIDATION: "Validate source's domain against trusted registries",
        VerificationMethod.IDENTITY_DOCUMENT: "Verify using official identity documents",
        VerificationMethod.PHONE_VERIFICATION: "Verify via phone number confirmation",
        VerificationMethod.EMAIL_VERIFICATION: "Verify email address and domain",
        VerificationMethod.GOVERNMENT_REGISTRY: "Check against government registries",
        VerificationMethod.ORGANIZATIONAL_BADGE: "Verify organizational credentials and badges",
        VerificationMethod.THIRD_PARTY_VERIFICATION: "Third-party verification service",
        VerificationMethod.MANUAL_REVIEW: "Manual review by verification team",
        VerificationMethod.CROSS_REFERENCE: "Cross-reference with verified sources",
    }
    return descriptions.get(method, "No description available")
