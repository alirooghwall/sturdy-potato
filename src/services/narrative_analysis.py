"""Narrative Analysis Service for ISR Platform.

Provides NLP-based analysis for detecting information warfare,
propaganda, and coordinated campaigns in OSINT/social media data.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import numpy as np


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class NarrativeType(str, Enum):
    """Types of narratives detected."""
    PROPAGANDA = "PROPAGANDA"
    DISINFORMATION = "DISINFORMATION"
    MISINFORMATION = "MISINFORMATION"
    LEGITIMATE_NEWS = "LEGITIMATE_NEWS"
    OPINION = "OPINION"
    RUMOR = "RUMOR"
    COORDINATED_CAMPAIGN = "COORDINATED_CAMPAIGN"


class SentimentCategory(str, Enum):
    """Sentiment categories."""
    VERY_NEGATIVE = "VERY_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    VERY_POSITIVE = "VERY_POSITIVE"


class SourceCredibility(str, Enum):
    """Source credibility levels."""
    VERIFIED = "VERIFIED"
    LIKELY_CREDIBLE = "LIKELY_CREDIBLE"
    UNKNOWN = "UNKNOWN"
    QUESTIONABLE = "QUESTIONABLE"
    KNOWN_DISINFORMATION = "KNOWN_DISINFORMATION"


class Language(str, Enum):
    """Supported languages."""
    DARI = "DARI"
    PASHTO = "PASHTO"
    ENGLISH = "ENGLISH"
    PERSIAN = "PERSIAN"
    URDU = "URDU"
    ARABIC = "ARABIC"


@dataclass
class Entity:
    """Named entity extracted from text."""
    text: str
    entity_type: str  # PERSON, ORGANIZATION, LOCATION, EVENT, etc.
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class NarrativeDocument:
    """A document/post for narrative analysis."""
    document_id: UUID
    source_id: str
    source_type: str  # SOCIAL_MEDIA, NEWS, RADIO_TRANSCRIPT, etc.
    content: str
    language: Language
    published_at: datetime
    author_id: str | None = None
    location: str | None = None
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    category: SentimentCategory
    score: float  # -1.0 to 1.0
    confidence: float
    emotions: dict[str, float] = field(default_factory=dict)  # anger, fear, joy, etc.


@dataclass
class NarrativeAnalysisResult:
    """Result of narrative analysis on a document."""
    analysis_id: UUID
    document_id: UUID
    narrative_type: NarrativeType
    confidence: float
    sentiment: SentimentResult
    entities: list[Entity] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    source_credibility: SourceCredibility = SourceCredibility.UNKNOWN
    propaganda_indicators: list[str] = field(default_factory=list)
    fact_check_flags: list[str] = field(default_factory=list)
    coordination_score: float = 0.0  # 0-1, likelihood of coordinated activity
    virality_score: float = 0.0  # 0-1, potential for viral spread
    threat_relevance: float = 0.0  # 0-1, relevance to security threats
    analyzed_at: datetime = field(default_factory=utcnow)
    model_id: str = "narrative-analyzer-v1"


@dataclass
class CoordinatedCampaign:
    """Detected coordinated information campaign."""
    campaign_id: UUID
    name: str
    description: str
    detected_at: datetime
    narrative_type: NarrativeType
    confidence: float
    source_accounts: list[str] = field(default_factory=list)
    document_ids: list[UUID] = field(default_factory=list)
    target_topics: list[str] = field(default_factory=list)
    target_regions: list[str] = field(default_factory=list)
    estimated_reach: int = 0
    coordination_indicators: list[str] = field(default_factory=list)
    status: str = "ACTIVE"


@dataclass
class NarrativeTrend:
    """Trending narrative/topic."""
    topic: str
    volume: int
    volume_change_pct: float
    sentiment: SentimentResult
    top_sources: list[str] = field(default_factory=list)
    related_entities: list[str] = field(default_factory=list)
    time_series: list[dict[str, Any]] = field(default_factory=list)


class NarrativeAnalysisService:
    """Service for analyzing narratives and detecting information warfare."""

    def __init__(self) -> None:
        """Initialize narrative analysis service."""
        self.model_id = "narrative-analyzer-v1"
        self.model_version = "1.0.0"
        
        # Known propaganda indicators
        self.propaganda_patterns = [
            "loaded_language",
            "appeal_to_authority",
            "bandwagon",
            "false_dilemma",
            "name_calling",
            "repetition",
            "scapegoating",
            "oversimplification",
            "emotional_appeal",
            "cherry_picking",
        ]
        
        # Known disinformation sources (simplified for demo)
        self.known_disinfo_sources: set[str] = set()
        
        # Verified sources
        self.verified_sources: set[str] = {"reuters", "ap_news", "bbc", "un_news"}
        
        # Analysis cache
        self._analysis_cache: dict[UUID, NarrativeAnalysisResult] = {}
        self._campaigns: dict[UUID, CoordinatedCampaign] = {}

    def analyze_document(
        self,
        document: NarrativeDocument,
    ) -> NarrativeAnalysisResult:
        """Analyze a single document for narrative characteristics."""
        # Extract entities
        entities = self._extract_entities(document.content, document.language)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(document.content, document.language)
        
        # Extract topics and keywords
        topics = self._extract_topics(document.content)
        keywords = self._extract_keywords(document.content)
        
        # Detect propaganda indicators
        propaganda_indicators = self._detect_propaganda(document.content)
        
        # Assess source credibility
        source_credibility = self._assess_source_credibility(document.source_id)
        
        # Classify narrative type
        narrative_type, type_confidence = self._classify_narrative(
            document, sentiment, propaganda_indicators, source_credibility
        )
        
        # Calculate coordination score
        coordination_score = self._calculate_coordination_score(document)
        
        # Calculate virality potential
        virality_score = self._calculate_virality_score(
            document, sentiment, topics
        )
        
        # Calculate threat relevance
        threat_relevance = self._calculate_threat_relevance(
            entities, topics, keywords
        )
        
        # Generate fact check flags
        fact_check_flags = self._generate_fact_check_flags(
            document, entities, propaganda_indicators
        )
        
        result = NarrativeAnalysisResult(
            analysis_id=uuid4(),
            document_id=document.document_id,
            narrative_type=narrative_type,
            confidence=type_confidence,
            sentiment=sentiment,
            entities=entities,
            topics=topics,
            keywords=keywords,
            source_credibility=source_credibility,
            propaganda_indicators=propaganda_indicators,
            fact_check_flags=fact_check_flags,
            coordination_score=coordination_score,
            virality_score=virality_score,
            threat_relevance=threat_relevance,
            model_id=self.model_id,
        )
        
        self._analysis_cache[result.analysis_id] = result
        return result

    def _extract_entities(
        self,
        text: str,
        language: Language,
    ) -> list[Entity]:
        """Extract named entities from text."""
        # Simplified entity extraction for demo
        # In production, use XLM-R or language-specific NER models
        entities = []
        
        # Simple pattern matching for demo
        # Afghan regions/provinces
        afghan_locations = [
            "Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad",
            "Nangarhar", "Helmand", "Balkh", "Kunduz", "Paktia",
            "Tora Bora", "Panjshir", "Baghlan", "Ghazni", "Zabul",
        ]
        
        for location in afghan_locations:
            if location.lower() in text.lower():
                start = text.lower().find(location.lower())
                entities.append(Entity(
                    text=location,
                    entity_type="LOCATION",
                    confidence=0.85,
                    start_pos=start,
                    end_pos=start + len(location),
                ))
        
        # Organization patterns
        org_patterns = ["Taliban", "ISIS", "ISIL", "NATO", "UN", "UNHCR", "WFP"]
        for org in org_patterns:
            if org.lower() in text.lower():
                start = text.lower().find(org.lower())
                entities.append(Entity(
                    text=org,
                    entity_type="ORGANIZATION",
                    confidence=0.9,
                    start_pos=start,
                    end_pos=start + len(org),
                ))
        
        return entities

    def _analyze_sentiment(
        self,
        text: str,
        language: Language,
    ) -> SentimentResult:
        """Analyze sentiment of text."""
        # Simplified sentiment analysis for demo
        # In production, use XLM-R or language-specific models
        
        # Simple keyword-based sentiment
        negative_words = [
            "attack", "killed", "bomb", "explosion", "war", "death",
            "terror", "threat", "danger", "crisis", "violence", "fear",
        ]
        positive_words = [
            "peace", "aid", "help", "support", "agreement", "progress",
            "hope", "cooperation", "development", "security", "safe",
        ]
        
        text_lower = text.lower()
        neg_count = sum(1 for w in negative_words if w in text_lower)
        pos_count = sum(1 for w in positive_words if w in text_lower)
        
        total = neg_count + pos_count
        if total == 0:
            score = 0.0
        else:
            score = (pos_count - neg_count) / total
        
        # Map to category
        if score < -0.5:
            category = SentimentCategory.VERY_NEGATIVE
        elif score < -0.1:
            category = SentimentCategory.NEGATIVE
        elif score < 0.1:
            category = SentimentCategory.NEUTRAL
        elif score < 0.5:
            category = SentimentCategory.POSITIVE
        else:
            category = SentimentCategory.VERY_POSITIVE
        
        # Estimate emotions
        emotions = {
            "anger": min(neg_count * 0.15, 1.0),
            "fear": min(neg_count * 0.1, 1.0),
            "sadness": min(neg_count * 0.1, 1.0),
            "joy": min(pos_count * 0.15, 1.0),
            "trust": min(pos_count * 0.1, 1.0),
        }
        
        return SentimentResult(
            category=category,
            score=score,
            confidence=0.7,
            emotions=emotions,
        )

    def _extract_topics(self, text: str) -> list[str]:
        """Extract topics from text."""
        # Simplified topic extraction
        topic_keywords = {
            "security": ["attack", "military", "soldier", "weapon", "bomb", "security"],
            "humanitarian": ["aid", "refugee", "food", "water", "shelter", "humanitarian"],
            "economic": ["economy", "trade", "market", "currency", "price", "business"],
            "political": ["government", "election", "leader", "policy", "minister"],
            "social": ["education", "health", "women", "children", "community"],
            "border": ["border", "crossing", "pakistan", "iran", "migration"],
        }
        
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected_topics.append(topic)
        
        return detected_topics

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction
        # In production, use TF-IDF or KeyBERT
        words = text.lower().split()
        # Filter short words and common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        keywords = [w for w in words if len(w) > 4 and w not in stop_words]
        
        # Get unique keywords by frequency
        from collections import Counter
        word_counts = Counter(keywords)
        return [w for w, _ in word_counts.most_common(10)]

    def _detect_propaganda(self, text: str) -> list[str]:
        """Detect propaganda techniques in text."""
        detected = []
        text_lower = text.lower()
        
        # Check for loaded language
        loaded_terms = ["extremist", "terrorist", "hero", "martyr", "enemy", "traitor"]
        if any(term in text_lower for term in loaded_terms):
            detected.append("loaded_language")
        
        # Check for emotional appeal
        emotional_terms = ["outrage", "shocking", "horrific", "devastating", "triumphant"]
        if any(term in text_lower for term in emotional_terms):
            detected.append("emotional_appeal")
        
        # Check for oversimplification
        if any(phrase in text_lower for phrase in ["only solution", "simple truth", "obvious"]):
            detected.append("oversimplification")
        
        # Check for repetition (simplified)
        words = text_lower.split()
        from collections import Counter
        word_counts = Counter(words)
        if any(count > 3 for word, count in word_counts.items() if len(word) > 4):
            detected.append("repetition")
        
        return detected

    def _assess_source_credibility(self, source_id: str) -> SourceCredibility:
        """Assess credibility of a source."""
        source_lower = source_id.lower()
        
        if source_lower in self.verified_sources:
            return SourceCredibility.VERIFIED
        
        if source_lower in self.known_disinfo_sources:
            return SourceCredibility.KNOWN_DISINFORMATION
        
        # Simple heuristics
        if any(term in source_lower for term in ["official", "gov", "ministry"]):
            return SourceCredibility.LIKELY_CREDIBLE
        
        if any(term in source_lower for term in ["anon", "leak", "insider"]):
            return SourceCredibility.QUESTIONABLE
        
        return SourceCredibility.UNKNOWN

    def _classify_narrative(
        self,
        document: NarrativeDocument,
        sentiment: SentimentResult,
        propaganda_indicators: list[str],
        source_credibility: SourceCredibility,
    ) -> tuple[NarrativeType, float]:
        """Classify the type of narrative."""
        confidence = 0.5
        
        # Check for disinformation indicators
        if source_credibility == SourceCredibility.KNOWN_DISINFORMATION:
            return NarrativeType.DISINFORMATION, 0.9
        
        # Check propaganda
        if len(propaganda_indicators) >= 3:
            return NarrativeType.PROPAGANDA, 0.8
        
        if len(propaganda_indicators) >= 1:
            confidence = 0.6
            if source_credibility == SourceCredibility.QUESTIONABLE:
                return NarrativeType.PROPAGANDA, 0.7
        
        # Check for rumor patterns
        rumor_indicators = ["reportedly", "unconfirmed", "sources say", "allegedly"]
        if any(ind in document.content.lower() for ind in rumor_indicators):
            return NarrativeType.RUMOR, 0.65
        
        # Verified source = legitimate
        if source_credibility == SourceCredibility.VERIFIED:
            return NarrativeType.LEGITIMATE_NEWS, 0.85
        
        # Check for opinion
        opinion_indicators = ["i think", "in my opinion", "i believe", "we should"]
        if any(ind in document.content.lower() for ind in opinion_indicators):
            return NarrativeType.OPINION, 0.7
        
        return NarrativeType.LEGITIMATE_NEWS, confidence

    def _calculate_coordination_score(self, document: NarrativeDocument) -> float:
        """Calculate likelihood of coordinated activity."""
        # In production, this would analyze posting patterns,
        # account creation dates, content similarity, etc.
        score = 0.0
        
        # Check metadata for coordination indicators
        metadata = document.metadata
        
        if metadata.get("is_retweet") or metadata.get("is_share"):
            score += 0.1
        
        if metadata.get("hashtag_count", 0) > 5:
            score += 0.2
        
        if metadata.get("mentions_count", 0) > 3:
            score += 0.1
        
        # Account age (if available)
        if metadata.get("account_age_days", 365) < 30:
            score += 0.3
        
        return min(score, 1.0)

    def _calculate_virality_score(
        self,
        document: NarrativeDocument,
        sentiment: SentimentResult,
        topics: list[str],
    ) -> float:
        """Calculate potential for viral spread."""
        score = 0.0
        
        # Strong sentiment increases virality
        if sentiment.category in [SentimentCategory.VERY_NEGATIVE, SentimentCategory.VERY_POSITIVE]:
            score += 0.3
        
        # Emotional content
        if sentiment.emotions.get("anger", 0) > 0.5:
            score += 0.2
        if sentiment.emotions.get("fear", 0) > 0.5:
            score += 0.2
        
        # Hot topics
        hot_topics = ["security", "political"]
        if any(t in topics for t in hot_topics):
            score += 0.2
        
        # Engagement metrics from metadata
        metadata = document.metadata
        if metadata.get("share_count", 0) > 100:
            score += 0.2
        
        return min(score, 1.0)

    def _calculate_threat_relevance(
        self,
        entities: list[Entity],
        topics: list[str],
        keywords: list[str],
    ) -> float:
        """Calculate relevance to security threats."""
        score = 0.0
        
        # Check for threat-related entities
        threat_orgs = ["taliban", "isis", "isil", "al-qaeda"]
        for entity in entities:
            if entity.entity_type == "ORGANIZATION":
                if entity.text.lower() in threat_orgs:
                    score += 0.3
        
        # Check topics
        if "security" in topics:
            score += 0.2
        if "border" in topics:
            score += 0.1
        
        # Check keywords
        threat_keywords = ["attack", "bomb", "weapon", "militant", "insurgent"]
        for kw in keywords:
            if kw in threat_keywords:
                score += 0.1
        
        return min(score, 1.0)

    def _generate_fact_check_flags(
        self,
        document: NarrativeDocument,
        entities: list[Entity],
        propaganda_indicators: list[str],
    ) -> list[str]:
        """Generate flags for fact-checking."""
        flags = []
        
        if propaganda_indicators:
            flags.append("Contains propaganda techniques - verify claims")
        
        # Check for specific claims
        claim_patterns = ["confirmed", "breaking", "exclusive", "official statement"]
        if any(pattern in document.content.lower() for pattern in claim_patterns):
            flags.append("Contains specific claims - verify with official sources")
        
        # Check for statistics
        if any(char.isdigit() for char in document.content):
            flags.append("Contains statistics/numbers - verify accuracy")
        
        return flags

    def detect_coordinated_campaign(
        self,
        documents: list[NarrativeDocument],
        similarity_threshold: float = 0.7,
    ) -> CoordinatedCampaign | None:
        """Detect coordinated information campaigns across documents."""
        if len(documents) < 5:
            return None
        
        # Analyze all documents
        results = [self.analyze_document(doc) for doc in documents]
        
        # Check for coordination indicators
        # 1. Similar content/topics
        all_topics: list[str] = []
        for r in results:
            all_topics.extend(r.topics)
        
        from collections import Counter
        topic_counts = Counter(all_topics)
        common_topics = [t for t, c in topic_counts.items() if c >= len(documents) * 0.5]
        
        # 2. Similar sentiment
        avg_sentiment = np.mean([r.sentiment.score for r in results])
        sentiment_std = np.std([r.sentiment.score for r in results])
        
        # 3. Temporal clustering
        timestamps = [doc.published_at for doc in documents]
        time_range = max(timestamps) - min(timestamps)
        
        # Detect campaign if indicators are strong
        if (
            len(common_topics) >= 2
            and sentiment_std < 0.3  # Similar sentiment
            and time_range < timedelta(hours=24)  # Clustered in time
        ):
            # Likely coordinated
            avg_coordination = np.mean([r.coordination_score for r in results])
            if avg_coordination > 0.3:
                campaign = CoordinatedCampaign(
                    campaign_id=uuid4(),
                    name=f"Coordinated Campaign: {', '.join(common_topics[:2])}",
                    description=f"Detected coordinated activity across {len(documents)} sources",
                    detected_at=utcnow(),
                    narrative_type=results[0].narrative_type,
                    confidence=min(avg_coordination + 0.2, 1.0),
                    source_accounts=[doc.author_id for doc in documents if doc.author_id],
                    document_ids=[doc.document_id for doc in documents],
                    target_topics=common_topics,
                    estimated_reach=len(documents) * 1000,  # Simplified estimate
                    coordination_indicators=[
                        f"Common topics: {', '.join(common_topics)}",
                        f"Sentiment alignment: {sentiment_std:.2f} std dev",
                        f"Temporal clustering: {time_range.total_seconds()/3600:.1f} hours",
                    ],
                )
                self._campaigns[campaign.campaign_id] = campaign
                return campaign
        
        return None

    def get_trending_narratives(
        self,
        hours: int = 24,
        limit: int = 10,
    ) -> list[NarrativeTrend]:
        """Get trending narratives/topics."""
        # Simplified trending calculation
        # In production, aggregate from time-series database
        
        trends = [
            NarrativeTrend(
                topic="Border Security",
                volume=2450,
                volume_change_pct=35.2,
                sentiment=SentimentResult(
                    category=SentimentCategory.NEGATIVE,
                    score=-0.35,
                    confidence=0.75,
                ),
                top_sources=["local_news", "social_media", "radio"],
                related_entities=["Pakistan", "Torkham", "Border Police"],
            ),
            NarrativeTrend(
                topic="Humanitarian Aid",
                volume=1890,
                volume_change_pct=12.5,
                sentiment=SentimentResult(
                    category=SentimentCategory.NEUTRAL,
                    score=0.05,
                    confidence=0.72,
                ),
                top_sources=["un_news", "ngo_reports", "social_media"],
                related_entities=["UNHCR", "WFP", "Kabul"],
            ),
            NarrativeTrend(
                topic="Economic Crisis",
                volume=3200,
                volume_change_pct=28.7,
                sentiment=SentimentResult(
                    category=SentimentCategory.VERY_NEGATIVE,
                    score=-0.62,
                    confidence=0.8,
                ),
                top_sources=["local_news", "economic_reports", "social_media"],
                related_entities=["Central Bank", "Currency", "Markets"],
            ),
        ]
        
        return trends[:limit]

    def get_analysis(self, analysis_id: UUID) -> NarrativeAnalysisResult | None:
        """Get analysis result by ID."""
        return self._analysis_cache.get(analysis_id)

    def get_campaign(self, campaign_id: UUID) -> CoordinatedCampaign | None:
        """Get campaign by ID."""
        return self._campaigns.get(campaign_id)

    def list_campaigns(self, status: str | None = None) -> list[CoordinatedCampaign]:
        """List detected campaigns."""
        campaigns = list(self._campaigns.values())
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return campaigns


# Global instance
_narrative_service: NarrativeAnalysisService | None = None


def get_narrative_service() -> NarrativeAnalysisService:
    """Get the narrative analysis service instance."""
    global _narrative_service
    if _narrative_service is None:
        _narrative_service = NarrativeAnalysisService()
    return _narrative_service
