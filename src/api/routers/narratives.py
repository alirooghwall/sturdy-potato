"""Narrative analysis and tracking endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.services.narrative_analysis import (
    Language,
    NarrativeDocument,
    NarrativeType,
    get_narrative_service,
)
from src.services.narrative_tracker import (
    NarrativeStatus,
    get_narrative_tracker,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class AnalyzeDocumentRequest(BaseModel):
    """Request to analyze a document."""
    content: str = Field(min_length=10, max_length=50000)
    source_id: str
    source_type: str = "SOCIAL_MEDIA"
    language: Language = Language.DARI
    author_id: str | None = None
    location: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyzeBatchRequest(BaseModel):
    """Request to analyze multiple documents."""
    documents: list[AnalyzeDocumentRequest] = Field(min_length=1, max_length=100)
    detect_campaigns: bool = True


class NarrativeAnalysisResponse(BaseModel):
    """Response for narrative analysis."""
    analysis_id: UUID
    document_id: UUID
    narrative_type: str
    confidence: float
    sentiment: dict[str, Any]
    entities: list[dict[str, Any]]
    topics: list[str]
    keywords: list[str]
    source_credibility: str
    propaganda_indicators: list[str]
    fact_check_flags: list[str]
    coordination_score: float
    virality_score: float
    threat_relevance: float
    analyzed_at: str


class CampaignResponse(BaseModel):
    """Response for coordinated campaign."""
    campaign_id: UUID
    name: str
    description: str
    narrative_type: str
    confidence: float
    source_count: int
    document_count: int
    target_topics: list[str]
    target_regions: list[str]
    estimated_reach: int
    coordination_indicators: list[str]
    status: str
    detected_at: str


class TrendResponse(BaseModel):
    """Response for narrative trend."""
    topic: str
    volume: int
    volume_change_pct: float
    sentiment_category: str
    sentiment_score: float
    top_sources: list[str]
    related_entities: list[str]


def _analysis_to_response(result) -> NarrativeAnalysisResponse:
    """Convert analysis result to response."""
    return NarrativeAnalysisResponse(
        analysis_id=result.analysis_id,
        document_id=result.document_id,
        narrative_type=result.narrative_type.value,
        confidence=result.confidence,
        sentiment={
            "category": result.sentiment.category.value,
            "score": result.sentiment.score,
            "confidence": result.sentiment.confidence,
            "emotions": result.sentiment.emotions,
        },
        entities=[
            {
                "text": e.text,
                "type": e.entity_type,
                "confidence": e.confidence,
            }
            for e in result.entities
        ],
        topics=result.topics,
        keywords=result.keywords,
        source_credibility=result.source_credibility.value,
        propaganda_indicators=result.propaganda_indicators,
        fact_check_flags=result.fact_check_flags,
        coordination_score=result.coordination_score,
        virality_score=result.virality_score,
        threat_relevance=result.threat_relevance,
        analyzed_at=result.analyzed_at.isoformat(),
    )


@router.post("/analyze", response_model=NarrativeAnalysisResponse)
async def analyze_document(
    request: AnalyzeDocumentRequest,
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
) -> NarrativeAnalysisResponse:
    """Analyze a single document for narrative characteristics."""
    service = get_narrative_service()

    document = NarrativeDocument(
        document_id=uuid4(),
        source_id=request.source_id,
        source_type=request.source_type,
        content=request.content,
        language=request.language,
        published_at=request.published_at or utcnow(),
        author_id=request.author_id,
        location=request.location,
        url=request.url,
        metadata=request.metadata,
    )

    result = service.analyze_document(document)
    return _analysis_to_response(result)


@router.post("/analyze/batch")
async def analyze_batch(
    request: AnalyzeBatchRequest,
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
) -> dict[str, Any]:
    """Analyze multiple documents and optionally detect campaigns."""
    service = get_narrative_service()

    # Convert requests to documents
    documents = []
    for doc_req in request.documents:
        doc = NarrativeDocument(
            document_id=uuid4(),
            source_id=doc_req.source_id,
            source_type=doc_req.source_type,
            content=doc_req.content,
            language=doc_req.language,
            published_at=doc_req.published_at or utcnow(),
            author_id=doc_req.author_id,
            location=doc_req.location,
            url=doc_req.url,
            metadata=doc_req.metadata,
        )
        documents.append(doc)

    # Analyze all documents
    results = [service.analyze_document(doc) for doc in documents]

    # Detect campaigns if requested
    campaign = None
    if request.detect_campaigns and len(documents) >= 5:
        campaign = service.detect_coordinated_campaign(documents)

    response: dict[str, Any] = {
        "document_count": len(documents),
        "analyses": [_analysis_to_response(r).model_dump() for r in results],
        "summary": {
            "narrative_types": {},
            "avg_threat_relevance": sum(r.threat_relevance for r in results) / len(results),
            "avg_coordination_score": sum(r.coordination_score for r in results) / len(results),
            "propaganda_detected": sum(1 for r in results if r.propaganda_indicators),
        },
        "timestamp": utcnow().isoformat(),
    }

    # Count narrative types
    for r in results:
        nt = r.narrative_type.value
        response["summary"]["narrative_types"][nt] = response["summary"]["narrative_types"].get(nt, 0) + 1

    # Add campaign if detected
    if campaign:
        response["campaign_detected"] = {
            "campaign_id": str(campaign.campaign_id),
            "name": campaign.name,
            "confidence": campaign.confidence,
            "indicators": campaign.coordination_indicators,
        }

    return response


@router.get("/trends", response_model=list[TrendResponse])
async def get_trending_narratives(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[TrendResponse]:
    """Get trending narratives/topics."""
    service = get_narrative_service()
    trends = service.get_trending_narratives(hours=hours, limit=limit)

    return [
        TrendResponse(
            topic=t.topic,
            volume=t.volume,
            volume_change_pct=t.volume_change_pct,
            sentiment_category=t.sentiment.category.value,
            sentiment_score=t.sentiment.score,
            top_sources=t.top_sources,
            related_entities=t.related_entities,
        )
        for t in trends
    ]


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[CampaignResponse]:
    """List detected coordinated campaigns."""
    service = get_narrative_service()
    campaigns = service.list_campaigns(status=status_filter)

    return [
        CampaignResponse(
            campaign_id=c.campaign_id,
            name=c.name,
            description=c.description,
            narrative_type=c.narrative_type.value,
            confidence=c.confidence,
            source_count=len(c.source_accounts),
            document_count=len(c.document_ids),
            target_topics=c.target_topics,
            target_regions=c.target_regions,
            estimated_reach=c.estimated_reach,
            coordination_indicators=c.coordination_indicators,
            status=c.status,
            detected_at=c.detected_at.isoformat(),
        )
        for c in campaigns
    ]


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
) -> CampaignResponse:
    """Get campaign by ID."""
    service = get_narrative_service()
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        name=campaign.name,
        description=campaign.description,
        narrative_type=campaign.narrative_type.value,
        confidence=campaign.confidence,
        source_count=len(campaign.source_accounts),
        document_count=len(campaign.document_ids),
        target_topics=campaign.target_topics,
        target_regions=campaign.target_regions,
        estimated_reach=campaign.estimated_reach,
        coordination_indicators=campaign.coordination_indicators,
        status=campaign.status,
        detected_at=campaign.detected_at.isoformat(),
    )


@router.get("/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: UUID,
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
) -> NarrativeAnalysisResponse:
    """Get analysis result by ID."""
    service = get_narrative_service()
    result = service.get_analysis(analysis_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )

    return _analysis_to_response(result)


@router.get("/disinformation/summary")
async def get_disinformation_summary(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    hours: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    """Get summary of disinformation detection."""
    # In production, aggregate from database
    return {
        "period_hours": hours,
        "total_documents_analyzed": 1250,
        "disinformation_detected": 45,
        "propaganda_detected": 89,
        "coordinated_campaigns": 2,
        "high_threat_narratives": 12,
        "top_disinformation_topics": [
            {"topic": "Economic manipulation", "count": 18},
            {"topic": "Security exaggeration", "count": 15},
            {"topic": "Political claims", "count": 12},
        ],
        "credibility_breakdown": {
            "verified": 320,
            "likely_credible": 450,
            "unknown": 380,
            "questionable": 78,
            "known_disinformation": 22,
        },
        "timestamp": utcnow().isoformat(),
    }


# ============================================================================
# Narrative Tracking Endpoints
# ============================================================================

@router.get("/tracking/active")
async def get_active_narratives(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    min_volume: int = Query(default=10, ge=1),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    """Get currently active tracked narratives."""
    tracker = get_narrative_tracker()
    
    # Parse status filter
    statuses = None
    if status:
        try:
            statuses = [NarrativeStatus(status)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )
    
    narratives = tracker.get_active_narratives(
        min_volume=min_volume,
        statuses=statuses,
    )
    
    return {
        "total": len(narratives),
        "narratives": [
            {
                "narrative_id": str(n.narrative_id),
                "name": n.narrative_name,
                "status": n.status.value,
                "propagation_pattern": n.propagation_pattern.value,
                "total_volume": n.total_volume,
                "peak_volume": n.peak_volume,
                "growth_rate": n.growth_rate,
                "velocity": n.velocity,
                "first_seen": n.first_seen.isoformat(),
                "last_seen": n.last_seen.isoformat(),
                "platforms": list(set(p for s in n.snapshots for p in s.platforms)) if n.snapshots else [],
                "mutation_count": len(n.mutation_events),
            }
            for n in narratives
        ],
        "timestamp": utcnow().isoformat(),
    }


@router.get("/tracking/emerging")
async def get_emerging_narratives(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    """Get emerging narratives to watch."""
    tracker = get_narrative_tracker()
    narratives = tracker.get_emerging_narratives(limit=limit)
    
    return {
        "total": len(narratives),
        "narratives": [
            {
                "narrative_id": str(n.narrative_id),
                "name": n.narrative_name,
                "status": n.status.value,
                "total_volume": n.total_volume,
                "growth_rate": n.growth_rate,
                "first_seen": n.first_seen.isoformat(),
                "last_seen": n.last_seen.isoformat(),
                "current_snapshot": {
                    "volume": n.snapshots[-1].volume,
                    "platforms": n.snapshots[-1].platforms,
                    "sentiment": n.snapshots[-1].sentiment_score,
                    "top_keywords": n.snapshots[-1].top_keywords[:5],
                } if n.snapshots else None,
            }
            for n in narratives
        ],
        "timestamp": utcnow().isoformat(),
    }


@router.get("/tracking/{narrative_id}")
async def get_narrative_evolution(
    narrative_id: UUID,
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
) -> dict[str, Any]:
    """Get detailed evolution data for a narrative."""
    tracker = get_narrative_tracker()
    evolution = tracker.get_narrative_evolution(narrative_id)
    
    if not evolution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Narrative {narrative_id} not found",
        )
    
    # Get cross-platform analysis
    cross_platform = tracker.get_cross_platform_analysis(narrative_id)
    
    # Get mutations
    mutations = tracker.get_mutations(narrative_id)
    
    return {
        "narrative_id": str(evolution.narrative_id),
        "name": evolution.narrative_name,
        "status": evolution.status.value,
        "propagation_pattern": evolution.propagation_pattern.value,
        "first_seen": evolution.first_seen.isoformat(),
        "last_seen": evolution.last_seen.isoformat(),
        "total_volume": evolution.total_volume,
        "peak_volume": evolution.peak_volume,
        "peak_timestamp": evolution.peak_timestamp.isoformat() if evolution.peak_timestamp else None,
        "growth_rate": evolution.growth_rate,
        "velocity": evolution.velocity,
        "acceleration": evolution.acceleration,
        "snapshots_count": len(evolution.snapshots),
        "snapshots": [
            {
                "snapshot_id": str(s.snapshot_id),
                "timestamp": s.timestamp.isoformat(),
                "volume": s.volume,
                "unique_sources": s.unique_sources,
                "platforms": s.platforms,
                "sentiment_score": s.sentiment_score,
                "coordination_score": s.coordination_score,
                "geographic_spread": s.geographic_spread,
                "top_keywords": s.top_keywords[:10],
                "top_entities": s.top_entities[:5],
            }
            for s in evolution.snapshots[-20:]  # Last 20 snapshots
        ],
        "mutations": [
            {
                "mutation_id": str(m.mutation_id),
                "type": m.mutation_type,
                "detected_at": m.detected_at.isoformat(),
                "description": m.description,
                "confidence": m.confidence,
                "before_keywords": m.before_keywords[:5],
                "after_keywords": m.after_keywords[:5],
                "sentiment_change": m.after_sentiment - m.before_sentiment,
            }
            for m in mutations
        ],
        "cross_platform": {
            "origin_platform": cross_platform.origin_platform,
            "origin_timestamp": cross_platform.origin_timestamp.isoformat(),
            "platform_sequence": cross_platform.platform_sequence,
            "time_to_spread": cross_platform.time_to_spread,
            "spread_timeline": cross_platform.spread_timeline,
        } if cross_platform else None,
        "key_amplifiers": evolution.key_amplifiers,
        "related_narratives": [str(rid) for rid in evolution.related_narratives],
        "mutation_events": evolution.mutation_events,
    }


@router.get("/tracking/{narrative_id}/timeline")
async def get_narrative_timeline(
    narrative_id: UUID,
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    hours: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    """Get narrative timeline for specified hours."""
    tracker = get_narrative_tracker()
    snapshots = tracker.get_narrative_timeline(narrative_id, hours=hours)
    
    if not snapshots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No timeline data for narrative {narrative_id}",
        )
    
    return {
        "narrative_id": str(narrative_id),
        "period_hours": hours,
        "snapshot_count": len(snapshots),
        "timeline": [
            {
                "timestamp": s.timestamp.isoformat(),
                "volume": s.volume,
                "platforms": s.platforms,
                "sentiment_score": s.sentiment_score,
                "coordination_score": s.coordination_score,
                "top_keywords": s.top_keywords[:5],
                "top_entities": s.top_entities[:3],
            }
            for s in snapshots
        ],
    }


@router.post("/tracking/compare")
async def compare_narratives(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
    narrative_id_1: UUID = Query(...),
    narrative_id_2: UUID = Query(...),
) -> dict[str, Any]:
    """Compare two narratives for similarities."""
    tracker = get_narrative_tracker()
    comparison = tracker.compare_narratives(narrative_id_1, narrative_id_2)
    
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both narratives not found",
        )
    
    return comparison


@router.get("/tracking/stats")
async def get_tracking_stats(
    user: Annotated[dict, Depends(require_permission("narrative:read"))],
) -> dict[str, Any]:
    """Get narrative tracking statistics."""
    tracker = get_narrative_tracker()
    return tracker.get_stats()
