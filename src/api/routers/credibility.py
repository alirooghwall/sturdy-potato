"""Credibility scoring and source verification endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.services.credibility_scoring import (
    CredibilityLevel,
    SourceType,
    get_credibility_scorer,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class ScoreSourceRequest(BaseModel):
    """Request to score a source."""
    source_id: str
    source_type: SourceType = SourceType.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreContentRequest(BaseModel):
    """Request to score content."""
    content_id: UUID
    source_id: str
    content: str = Field(min_length=10, max_length=50000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerifyContentRequest(BaseModel):
    """Request to add verification record."""
    content_id: UUID
    verdict: str  # TRUE, FALSE, MISLEADING, UNVERIFIABLE, MIXED
    verified_by: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    evidence: list[str] = Field(default_factory=list)
    sources_checked: list[str] = Field(default_factory=list)
    notes: str = ""


class UpdateSourceAccuracyRequest(BaseModel):
    """Request to update source accuracy."""
    source_id: str
    accurate: bool


class FlagSourceRequest(BaseModel):
    """Request to flag a source."""
    source_id: str
    reason: str
    flagged_by: str


class CredibilityFactorResponse(BaseModel):
    """Response for credibility factor."""
    factor_name: str
    score: float
    weight: float
    description: str
    evidence: list[str]


class ContentCredibilityResponse(BaseModel):
    """Response for content credibility assessment."""
    content_id: UUID
    source_id: str
    assessed_at: str
    overall_score: float
    credibility_level: str
    source_credibility: float
    content_quality: float
    verification_status: float
    consistency_score: float
    factors: list[CredibilityFactorResponse]
    red_flags: list[str]
    warnings: list[str]
    positive_indicators: list[str]
    fact_check_recommended: bool
    manual_review_recommended: bool
    confidence: float


class SourceProfileResponse(BaseModel):
    """Response for source profile."""
    source_id: str
    source_type: str
    display_name: str
    verified_identity: bool
    account_age_days: int
    total_posts: int
    accurate_posts: int
    inaccurate_posts: int
    accuracy_rate: float
    bot_probability: float
    cited_by_verified_sources: int
    flagged_by_fact_checkers: int
    community_reports: int
    platform: str
    badges: list[str]


@router.post("/sources/score")
async def score_source(
    request: ScoreSourceRequest,
    user: Annotated[dict, Depends(require_permission("credibility:write"))],
) -> dict[str, Any]:
    """Score a source's credibility."""
    scorer = get_credibility_scorer()
    
    score = scorer.score_source(
        source_id=request.source_id,
        source_type=request.source_type,
        metadata=request.metadata,
    )
    
    level = scorer._score_to_level(score)
    
    return {
        "source_id": request.source_id,
        "credibility_score": score,
        "credibility_level": level.value,
        "timestamp": utcnow().isoformat(),
    }


@router.get("/sources/{source_id}")
async def get_source_profile(
    source_id: str,
    user: Annotated[dict, Depends(require_permission("credibility:read"))],
) -> SourceProfileResponse:
    """Get source profile and credibility information."""
    scorer = get_credibility_scorer()
    profile = scorer.get_source_profile(source_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    
    accuracy_rate = (
        profile.accurate_posts / profile.total_posts
        if profile.total_posts > 0
        else 0.0
    )
    
    return SourceProfileResponse(
        source_id=profile.source_id,
        source_type=profile.source_type.value,
        display_name=profile.display_name,
        verified_identity=profile.verified_identity,
        account_age_days=profile.account_age_days,
        total_posts=profile.total_posts,
        accurate_posts=profile.accurate_posts,
        inaccurate_posts=profile.inaccurate_posts,
        accuracy_rate=accuracy_rate,
        bot_probability=profile.bot_probability,
        cited_by_verified_sources=profile.cited_by_verified_sources,
        flagged_by_fact_checkers=profile.flagged_by_fact_checkers,
        community_reports=profile.community_reports,
        platform=profile.platform,
        badges=profile.badges,
    )


@router.post("/content/score")
async def score_content(
    request: ScoreContentRequest,
    user: Annotated[dict, Depends(require_permission("credibility:write"))],
) -> ContentCredibilityResponse:
    """Score content for credibility."""
    scorer = get_credibility_scorer()
    
    assessment = scorer.score_content(
        content_id=request.content_id,
        source_id=request.source_id,
        content=request.content,
        metadata=request.metadata,
    )
    
    return ContentCredibilityResponse(
        content_id=assessment.content_id,
        source_id=assessment.source_id,
        assessed_at=assessment.assessed_at.isoformat(),
        overall_score=assessment.overall_score,
        credibility_level=assessment.credibility_level.value,
        source_credibility=assessment.source_credibility,
        content_quality=assessment.content_quality,
        verification_status=assessment.verification_status,
        consistency_score=assessment.consistency_score,
        factors=[
            CredibilityFactorResponse(
                factor_name=f.factor_name,
                score=f.score,
                weight=f.weight,
                description=f.description,
                evidence=f.evidence,
            )
            for f in assessment.factors
        ],
        red_flags=assessment.red_flags,
        warnings=assessment.warnings,
        positive_indicators=assessment.positive_indicators,
        fact_check_recommended=assessment.fact_check_recommended,
        manual_review_recommended=assessment.manual_review_recommended,
        confidence=assessment.confidence,
    )


@router.get("/content/{content_id}")
async def get_content_assessment(
    content_id: UUID,
    user: Annotated[dict, Depends(require_permission("credibility:read"))],
) -> ContentCredibilityResponse:
    """Get content credibility assessment."""
    scorer = get_credibility_scorer()
    assessment = scorer.get_content_assessment(content_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment for content {content_id} not found",
        )
    
    return ContentCredibilityResponse(
        content_id=assessment.content_id,
        source_id=assessment.source_id,
        assessed_at=assessment.assessed_at.isoformat(),
        overall_score=assessment.overall_score,
        credibility_level=assessment.credibility_level.value,
        source_credibility=assessment.source_credibility,
        content_quality=assessment.content_quality,
        verification_status=assessment.verification_status,
        consistency_score=assessment.consistency_score,
        factors=[
            CredibilityFactorResponse(
                factor_name=f.factor_name,
                score=f.score,
                weight=f.weight,
                description=f.description,
                evidence=f.evidence,
            )
            for f in assessment.factors
        ],
        red_flags=assessment.red_flags,
        warnings=assessment.warnings,
        positive_indicators=assessment.positive_indicators,
        fact_check_recommended=assessment.fact_check_recommended,
        manual_review_recommended=assessment.manual_review_recommended,
        confidence=assessment.confidence,
    )


@router.post("/verification/add")
async def add_verification(
    request: VerifyContentRequest,
    user: Annotated[dict, Depends(require_permission("credibility:verify"))],
) -> dict[str, Any]:
    """Add fact-checking verification record."""
    scorer = get_credibility_scorer()
    
    # Validate verdict
    valid_verdicts = ["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE", "MIXED"]
    if request.verdict.upper() not in valid_verdicts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verdict. Must be one of: {', '.join(valid_verdicts)}",
        )
    
    record = scorer.add_verification_record(
        content_id=request.content_id,
        verdict=request.verdict.upper(),
        verified_by=request.verified_by,
        confidence=request.confidence,
        evidence=request.evidence,
        sources_checked=request.sources_checked,
        notes=request.notes,
    )
    
    return {
        "verification_id": str(record.verification_id),
        "content_id": str(record.content_id),
        "verdict": record.verdict,
        "verified_by": record.verified_by,
        "verification_date": record.verification_date.isoformat(),
        "confidence": record.confidence,
    }


@router.post("/sources/update-accuracy")
async def update_source_accuracy(
    request: UpdateSourceAccuracyRequest,
    user: Annotated[dict, Depends(require_permission("credibility:write"))],
) -> dict[str, Any]:
    """Update source's accuracy record."""
    scorer = get_credibility_scorer()
    
    scorer.update_source_accuracy(
        source_id=request.source_id,
        accurate=request.accurate,
    )
    
    # Get updated profile
    profile = scorer.get_source_profile(request.source_id)
    
    if profile:
        accuracy_rate = (
            profile.accurate_posts / profile.total_posts
            if profile.total_posts > 0
            else 0.0
        )
        
        return {
            "source_id": request.source_id,
            "total_posts": profile.total_posts,
            "accurate_posts": profile.accurate_posts,
            "inaccurate_posts": profile.inaccurate_posts,
            "accuracy_rate": accuracy_rate,
            "updated_at": utcnow().isoformat(),
        }
    
    return {
        "source_id": request.source_id,
        "message": "Source not found in profiles",
    }


@router.post("/sources/flag")
async def flag_source(
    request: FlagSourceRequest,
    user: Annotated[dict, Depends(require_permission("credibility:write"))],
) -> dict[str, Any]:
    """Flag a source for issues."""
    scorer = get_credibility_scorer()
    
    scorer.flag_source(
        source_id=request.source_id,
        reason=request.reason,
        flagged_by=request.flagged_by,
    )
    
    return {
        "source_id": request.source_id,
        "reason": request.reason,
        "flagged_by": request.flagged_by,
        "timestamp": utcnow().isoformat(),
    }


@router.get("/stats")
async def get_credibility_stats(
    user: Annotated[dict, Depends(require_permission("credibility:read"))],
) -> dict[str, Any]:
    """Get credibility scoring statistics."""
    scorer = get_credibility_scorer()
    return scorer.get_stats()


@router.get("/sources")
async def list_sources(
    user: Annotated[dict, Depends(require_permission("credibility:read"))],
    verified_only: bool = Query(default=False),
    min_posts: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """List sources with filtering."""
    scorer = get_credibility_scorer()
    
    sources = []
    for profile in scorer.source_profiles.values():
        if verified_only and not profile.verified_identity:
            continue
        
        if profile.total_posts < min_posts:
            continue
        
        accuracy_rate = (
            profile.accurate_posts / profile.total_posts
            if profile.total_posts > 0
            else 0.0
        )
        
        sources.append({
            "source_id": profile.source_id,
            "source_type": profile.source_type.value,
            "display_name": profile.display_name,
            "verified_identity": profile.verified_identity,
            "accuracy_rate": accuracy_rate,
            "total_posts": profile.total_posts,
            "flagged_by_fact_checkers": profile.flagged_by_fact_checkers,
        })
    
    # Sort by accuracy rate
    sources.sort(key=lambda x: x["accuracy_rate"], reverse=True)
    
    return {
        "total": len(sources),
        "sources": sources[:limit],
    }
