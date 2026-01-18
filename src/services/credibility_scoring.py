"""Credibility Scoring System for ISR Platform.

Evaluates the trustworthiness and reliability of sources, content, and claims
using multiple factors including source history, content analysis, and verification.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from collections import defaultdict

import numpy as np


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class CredibilityLevel(str, Enum):
    """Overall credibility levels."""
    VERIFIED = "VERIFIED"  # 90-100%
    HIGH = "HIGH"  # 75-89%
    MEDIUM = "MEDIUM"  # 50-74%
    LOW = "LOW"  # 25-49%
    VERY_LOW = "VERY_LOW"  # 10-24%
    UNTRUSTWORTHY = "UNTRUSTWORTHY"  # 0-9%


class SourceType(str, Enum):
    """Types of information sources."""
    NEWS_ORGANIZATION = "NEWS_ORGANIZATION"
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    SOCIAL_MEDIA_ACCOUNT = "SOCIAL_MEDIA_ACCOUNT"
    NGO = "NGO"
    ACADEMIC = "ACADEMIC"
    INDEPENDENT_JOURNALIST = "INDEPENDENT_JOURNALIST"
    ANONYMOUS = "ANONYMOUS"
    UNKNOWN = "UNKNOWN"


@dataclass
class CredibilityFactor:
    """Individual factor contributing to credibility score."""
    factor_name: str
    score: float  # 0-1
    weight: float  # 0-1
    description: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class SourceProfile:
    """Profile of an information source."""
    source_id: str
    source_type: SourceType
    display_name: str
    created_at: datetime
    verified_identity: bool = False
    verification_date: datetime | None = None
    verification_method: str | None = None
    
    # Historical metrics
    total_posts: int = 0
    accurate_posts: int = 0
    inaccurate_posts: int = 0
    unverified_posts: int = 0
    
    # Behavioral indicators
    account_age_days: int = 0
    posting_frequency: float = 0.0  # Posts per day
    engagement_rate: float = 0.0  # Average engagement
    bot_probability: float = 0.0  # 0-1
    
    # Network metrics
    follower_count: int = 0
    following_count: int = 0
    follower_quality_score: float = 0.5  # 0-1
    
    # Reputation
    cited_by_verified_sources: int = 0
    flagged_by_fact_checkers: int = 0
    community_reports: int = 0
    
    # Platform-specific
    platform: str = "unknown"
    badges: list[str] = field(default_factory=list)  # "verified", "government", etc.
    
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentCredibility:
    """Credibility assessment for specific content."""
    content_id: UUID
    source_id: str
    assessed_at: datetime
    overall_score: float  # 0-1
    credibility_level: CredibilityLevel
    factors: list[CredibilityFactor] = field(default_factory=list)
    
    # Component scores
    source_credibility: float = 0.5
    content_quality: float = 0.5
    verification_status: float = 0.5
    consistency_score: float = 0.5
    
    # Flags and warnings
    red_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    positive_indicators: list[str] = field(default_factory=list)
    
    # Recommendations
    fact_check_recommended: bool = False
    manual_review_recommended: bool = False
    confidence: float = 0.7


@dataclass
class VerificationRecord:
    """Record of fact-checking or verification."""
    verification_id: UUID
    content_id: UUID
    verified_by: str
    verification_date: datetime
    verdict: str  # TRUE, FALSE, MISLEADING, UNVERIFIABLE, MIXED
    confidence: float
    evidence: list[str] = field(default_factory=list)
    sources_checked: list[str] = field(default_factory=list)
    notes: str = ""


class CredibilityScorer:
    """Service for scoring source and content credibility."""

    def __init__(self):
        """Initialize credibility scorer."""
        self.source_profiles: dict[str, SourceProfile] = {}
        self.content_assessments: dict[UUID, ContentCredibility] = {}
        self.verification_records: dict[UUID, VerificationRecord] = {}
        
        # Known verified sources (would be loaded from database)
        self.verified_sources = {
            "reuters", "ap_news", "bbc", "cnn", "aljazeera",
            "un_news", "unhcr", "wfp", "who", "icrc",
        }
        
        # Known unreliable sources
        self.unreliable_sources = {
            # Would be populated based on fact-checking organizations
        }
        
        # Credibility weights for different factors
        self.weights = {
            "source_reputation": 0.30,
            "content_quality": 0.25,
            "verification_status": 0.20,
            "consistency": 0.15,
            "behavioral_indicators": 0.10,
        }
    
    def score_source(
        self,
        source_id: str,
        source_type: SourceType = SourceType.UNKNOWN,
        metadata: dict[str, Any] | None = None,
    ) -> float:
        """Score a source's overall credibility."""
        metadata = metadata or {}
        
        # Get or create source profile
        if source_id not in self.source_profiles:
            profile = self._create_source_profile(source_id, source_type, metadata)
            self.source_profiles[source_id] = profile
        else:
            profile = self.source_profiles[source_id]
        
        factors = []
        
        # Factor 1: Verification status
        if profile.verified_identity:
            verification_score = 0.9
            factors.append(CredibilityFactor(
                factor_name="Verified Identity",
                score=verification_score,
                weight=0.25,
                description="Source identity has been verified",
                evidence=[f"Verified on {profile.verification_date}"],
            ))
        else:
            verification_score = 0.3
            factors.append(CredibilityFactor(
                factor_name="Unverified Identity",
                score=verification_score,
                weight=0.25,
                description="Source identity not verified",
                evidence=["No verification on record"],
            ))
        
        # Factor 2: Historical accuracy
        if profile.total_posts > 0:
            accuracy_rate = profile.accurate_posts / profile.total_posts
            factors.append(CredibilityFactor(
                factor_name="Historical Accuracy",
                score=accuracy_rate,
                weight=0.30,
                description=f"{accuracy_rate*100:.1f}% accuracy rate",
                evidence=[f"{profile.accurate_posts}/{profile.total_posts} accurate posts"],
            ))
        else:
            accuracy_rate = 0.5  # Neutral for new sources
            factors.append(CredibilityFactor(
                factor_name="No History",
                score=accuracy_rate,
                weight=0.30,
                description="No historical posts to evaluate",
                evidence=["New or unknown source"],
            ))
        
        # Factor 3: Account age and behavior
        behavior_score = self._calculate_behavioral_score(profile)
        factors.append(CredibilityFactor(
            factor_name="Behavioral Indicators",
            score=behavior_score,
            weight=0.15,
            description="Account age, posting patterns, bot indicators",
            evidence=[
                f"Account age: {profile.account_age_days} days",
                f"Bot probability: {profile.bot_probability:.2f}",
            ],
        ))
        
        # Factor 4: Network and reputation
        reputation_score = self._calculate_reputation_score(profile)
        factors.append(CredibilityFactor(
            factor_name="Reputation",
            score=reputation_score,
            weight=0.20,
            description="Citations, fact-checker flags, community reports",
            evidence=[
                f"Cited by verified sources: {profile.cited_by_verified_sources}",
                f"Flagged by fact-checkers: {profile.flagged_by_fact_checkers}",
                f"Community reports: {profile.community_reports}",
            ],
        ))
        
        # Factor 5: Source type reliability
        type_score = self._get_source_type_score(profile.source_type)
        factors.append(CredibilityFactor(
            factor_name="Source Type",
            score=type_score,
            weight=0.10,
            description=f"Baseline credibility for {profile.source_type.value}",
            evidence=[f"Source type: {profile.source_type.value}"],
        ))
        
        # Calculate weighted score
        total_score = sum(f.score * f.weight for f in factors)
        
        return total_score
    
    def score_content(
        self,
        content_id: UUID,
        source_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContentCredibility:
        """Score specific content for credibility."""
        metadata = metadata or {}
        
        # Get source credibility
        source_score = self.score_source(source_id, metadata=metadata)
        
        # Analyze content quality
        content_quality = self._analyze_content_quality(content)
        
        # Check verification status
        verification_status = self._check_verification_status(content_id)
        
        # Check consistency with other sources
        consistency_score = self._check_consistency(content, metadata)
        
        # Combine scores
        overall_score = (
            source_score * self.weights["source_reputation"] +
            content_quality * self.weights["content_quality"] +
            verification_status * self.weights["verification_status"] +
            consistency_score * self.weights["consistency"]
        )
        
        # Determine credibility level
        credibility_level = self._score_to_level(overall_score)
        
        # Identify red flags and warnings
        red_flags, warnings, positive_indicators = self._identify_flags(
            content, source_id, source_score, content_quality
        )
        
        # Build factors list
        factors = [
            CredibilityFactor(
                factor_name="Source Credibility",
                score=source_score,
                weight=self.weights["source_reputation"],
                description="Overall source trustworthiness",
                evidence=[f"Source score: {source_score:.2f}"],
            ),
            CredibilityFactor(
                factor_name="Content Quality",
                score=content_quality,
                weight=self.weights["content_quality"],
                description="Writing quality, structure, evidence",
                evidence=[],
            ),
            CredibilityFactor(
                factor_name="Verification Status",
                score=verification_status,
                weight=self.weights["verification_status"],
                description="Fact-checking and verification",
                evidence=[],
            ),
            CredibilityFactor(
                factor_name="Consistency",
                score=consistency_score,
                weight=self.weights["consistency"],
                description="Consistency with other reliable sources",
                evidence=[],
            ),
        ]
        
        # Determine if manual review needed
        fact_check_recommended = (
            overall_score < 0.6 or
            len(red_flags) > 0 or
            metadata.get("high_impact", False)
        )
        
        manual_review_recommended = (
            overall_score < 0.4 or
            len(red_flags) > 2
        )
        
        assessment = ContentCredibility(
            content_id=content_id,
            source_id=source_id,
            assessed_at=utcnow(),
            overall_score=overall_score,
            credibility_level=credibility_level,
            factors=factors,
            source_credibility=source_score,
            content_quality=content_quality,
            verification_status=verification_status,
            consistency_score=consistency_score,
            red_flags=red_flags,
            warnings=warnings,
            positive_indicators=positive_indicators,
            fact_check_recommended=fact_check_recommended,
            manual_review_recommended=manual_review_recommended,
            confidence=0.75,
        )
        
        self.content_assessments[content_id] = assessment
        return assessment
    
    def _create_source_profile(
        self,
        source_id: str,
        source_type: SourceType,
        metadata: dict[str, Any],
    ) -> SourceProfile:
        """Create a new source profile."""
        source_lower = source_id.lower()
        
        # Check if verified source
        verified = source_lower in self.verified_sources
        
        # Extract metadata
        account_created = metadata.get("account_created")
        if account_created:
            if isinstance(account_created, str):
                account_created = datetime.fromisoformat(account_created.replace('Z', '+00:00'))
            account_age = (utcnow() - account_created).days
        else:
            account_age = metadata.get("account_age_days", 365)
        
        profile = SourceProfile(
            source_id=source_id,
            source_type=source_type,
            display_name=metadata.get("display_name", source_id),
            created_at=utcnow(),
            verified_identity=verified,
            verification_date=utcnow() if verified else None,
            verification_method="manual" if verified else None,
            account_age_days=account_age,
            posting_frequency=metadata.get("posting_frequency", 1.0),
            bot_probability=metadata.get("bot_probability", 0.1),
            follower_count=metadata.get("follower_count", 0),
            following_count=metadata.get("following_count", 0),
            follower_quality_score=metadata.get("follower_quality", 0.5),
            platform=metadata.get("platform", "unknown"),
            badges=metadata.get("badges", []),
            metadata=metadata,
        )
        
        return profile
    
    def _calculate_behavioral_score(self, profile: SourceProfile) -> float:
        """Calculate behavioral credibility score."""
        score = 0.5  # Baseline
        
        # Account age (older is better)
        if profile.account_age_days > 365:
            score += 0.2
        elif profile.account_age_days > 180:
            score += 0.1
        elif profile.account_age_days < 30:
            score -= 0.2
        
        # Bot probability (lower is better)
        score -= profile.bot_probability * 0.3
        
        # Posting frequency (too high or too low is suspicious)
        if 0.5 <= profile.posting_frequency <= 5.0:  # Reasonable range
            score += 0.1
        elif profile.posting_frequency > 50:  # Very high frequency
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_reputation_score(self, profile: SourceProfile) -> float:
        """Calculate reputation score."""
        score = 0.5  # Baseline
        
        # Cited by verified sources (positive)
        if profile.cited_by_verified_sources > 10:
            score += 0.3
        elif profile.cited_by_verified_sources > 5:
            score += 0.2
        elif profile.cited_by_verified_sources > 0:
            score += 0.1
        
        # Flagged by fact-checkers (negative)
        if profile.flagged_by_fact_checkers > 5:
            score -= 0.4
        elif profile.flagged_by_fact_checkers > 2:
            score -= 0.2
        elif profile.flagged_by_fact_checkers > 0:
            score -= 0.1
        
        # Community reports (negative)
        if profile.community_reports > 10:
            score -= 0.3
        elif profile.community_reports > 5:
            score -= 0.2
        elif profile.community_reports > 0:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _get_source_type_score(self, source_type: SourceType) -> float:
        """Get baseline score for source type."""
        type_scores = {
            SourceType.NEWS_ORGANIZATION: 0.7,
            SourceType.GOVERNMENT_OFFICIAL: 0.65,
            SourceType.NGO: 0.7,
            SourceType.ACADEMIC: 0.75,
            SourceType.INDEPENDENT_JOURNALIST: 0.6,
            SourceType.SOCIAL_MEDIA_ACCOUNT: 0.4,
            SourceType.ANONYMOUS: 0.2,
            SourceType.UNKNOWN: 0.3,
        }
        return type_scores.get(source_type, 0.5)
    
    def _analyze_content_quality(self, content: str) -> float:
        """Analyze content quality indicators."""
        score = 0.5
        
        # Length (too short may lack detail)
        if len(content) > 500:
            score += 0.1
        elif len(content) < 100:
            score -= 0.1
        
        # Check for sources/citations
        if any(phrase in content.lower() for phrase in ["according to", "source:", "reported by"]):
            score += 0.15
        
        # Check for balanced language
        sensational_words = ["shocking", "unbelievable", "you won't believe", "breaking", "urgent"]
        if sum(1 for w in sensational_words if w in content.lower()) > 2:
            score -= 0.2
        
        # Check for proper structure
        sentences = content.count('.') + content.count('!') + content.count('?')
        if sentences >= 3:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_verification_status(self, content_id: UUID) -> float:
        """Check if content has been verified."""
        # Check for verification records
        verification = self.verification_records.get(content_id)
        
        if verification:
            if verification.verdict == "TRUE":
                return 0.9
            elif verification.verdict == "FALSE":
                return 0.1
            elif verification.verdict == "MISLEADING":
                return 0.3
            elif verification.verdict == "MIXED":
                return 0.5
            else:  # UNVERIFIABLE
                return 0.4
        
        # No verification yet
        return 0.5
    
    def _check_consistency(
        self,
        content: str,
        metadata: dict[str, Any],
    ) -> float:
        """Check consistency with other sources."""
        # Simplified consistency check
        # In production, would compare with verified sources
        
        # Check if similar content from multiple sources
        corroboration_count = metadata.get("corroboration_count", 0)
        
        if corroboration_count >= 3:
            return 0.8
        elif corroboration_count >= 2:
            return 0.6
        elif corroboration_count == 1:
            return 0.5
        else:
            return 0.4
    
    def _identify_flags(
        self,
        content: str,
        source_id: str,
        source_score: float,
        content_quality: float,
    ) -> tuple[list[str], list[str], list[str]]:
        """Identify red flags, warnings, and positive indicators."""
        red_flags = []
        warnings = []
        positive_indicators = []
        
        content_lower = content.lower()
        
        # Red flags
        if source_score < 0.3:
            red_flags.append("Unreliable source")
        
        if source_id.lower() in self.unreliable_sources:
            red_flags.append("Known disinformation source")
        
        if any(phrase in content_lower for phrase in ["unconfirmed", "rumor", "allegedly"]):
            warnings.append("Contains unverified claims")
        
        # Warnings
        if content_quality < 0.4:
            warnings.append("Low content quality")
        
        if len(content) < 100:
            warnings.append("Very short content - may lack context")
        
        # Positive indicators
        if source_score > 0.75:
            positive_indicators.append("Credible source")
        
        if any(phrase in content_lower for phrase in ["verified", "confirmed", "official"]):
            positive_indicators.append("Contains verified claims")
        
        if content_quality > 0.7:
            positive_indicators.append("High content quality")
        
        return red_flags, warnings, positive_indicators
    
    def _score_to_level(self, score: float) -> CredibilityLevel:
        """Convert numeric score to credibility level."""
        if score >= 0.90:
            return CredibilityLevel.VERIFIED
        elif score >= 0.75:
            return CredibilityLevel.HIGH
        elif score >= 0.50:
            return CredibilityLevel.MEDIUM
        elif score >= 0.25:
            return CredibilityLevel.LOW
        elif score >= 0.10:
            return CredibilityLevel.VERY_LOW
        else:
            return CredibilityLevel.UNTRUSTWORTHY
    
    def add_verification_record(
        self,
        content_id: UUID,
        verdict: str,
        verified_by: str,
        confidence: float = 0.8,
        evidence: list[str] | None = None,
        sources_checked: list[str] | None = None,
        notes: str = "",
    ) -> VerificationRecord:
        """Add a fact-checking verification record."""
        record = VerificationRecord(
            verification_id=uuid4(),
            content_id=content_id,
            verified_by=verified_by,
            verification_date=utcnow(),
            verdict=verdict,
            confidence=confidence,
            evidence=evidence or [],
            sources_checked=sources_checked or [],
            notes=notes,
        )
        
        self.verification_records[content_id] = record
        return record
    
    def update_source_accuracy(
        self,
        source_id: str,
        accurate: bool,
    ) -> None:
        """Update source's accuracy record."""
        if source_id not in self.source_profiles:
            return
        
        profile = self.source_profiles[source_id]
        profile.total_posts += 1
        
        if accurate:
            profile.accurate_posts += 1
        else:
            profile.inaccurate_posts += 1
    
    def flag_source(
        self,
        source_id: str,
        reason: str,
        flagged_by: str,
    ) -> None:
        """Flag a source for issues."""
        if source_id not in self.source_profiles:
            return
        
        profile = self.source_profiles[source_id]
        
        if "fact-checker" in flagged_by.lower():
            profile.flagged_by_fact_checkers += 1
        else:
            profile.community_reports += 1
    
    def get_source_profile(self, source_id: str) -> SourceProfile | None:
        """Get source profile."""
        return self.source_profiles.get(source_id)
    
    def get_content_assessment(self, content_id: UUID) -> ContentCredibility | None:
        """Get content credibility assessment."""
        return self.content_assessments.get(content_id)
    
    def get_stats(self) -> dict[str, Any]:
        """Get scorer statistics."""
        return {
            "total_sources": len(self.source_profiles),
            "verified_sources": sum(1 for p in self.source_profiles.values() if p.verified_identity),
            "total_assessments": len(self.content_assessments),
            "verification_records": len(self.verification_records),
            "credibility_distribution": {
                level.value: sum(
                    1 for a in self.content_assessments.values()
                    if a.credibility_level == level
                )
                for level in CredibilityLevel
            },
        }


# Global instance
_credibility_scorer: CredibilityScorer | None = None


def get_credibility_scorer() -> CredibilityScorer:
    """Get the credibility scorer instance."""
    global _credibility_scorer
    if _credibility_scorer is None:
        _credibility_scorer = CredibilityScorer()
    return _credibility_scorer
