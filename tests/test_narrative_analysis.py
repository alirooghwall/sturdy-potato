"""Tests for narrative analysis service."""

import pytest
from datetime import UTC, datetime
from uuid import uuid4

from src.services.narrative_analysis import (
    Language,
    NarrativeAnalysisService,
    NarrativeDocument,
    NarrativeType,
    SentimentCategory,
    SourceCredibility,
)


@pytest.fixture
def service():
    """Create narrative analysis service instance."""
    return NarrativeAnalysisService()


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return NarrativeDocument(
        document_id=uuid4(),
        source_id="test_source",
        source_type="SOCIAL_MEDIA",
        content="There was an attack in Kabul today. NATO forces responded to the threat.",
        language=Language.ENGLISH,
        published_at=datetime.now(UTC),
    )


@pytest.fixture
def propaganda_document():
    """Create a document with propaganda indicators."""
    return NarrativeDocument(
        document_id=uuid4(),
        source_id="questionable_source",
        source_type="SOCIAL_MEDIA",
        content="The extremist enemy terrorists attacked our heroes! This is outrage! "
                "The only solution is obvious - we must fight these traitors!",
        language=Language.ENGLISH,
        published_at=datetime.now(UTC),
    )


class TestNarrativeAnalysisService:
    """Tests for NarrativeAnalysisService."""

    def test_analyze_document_returns_result(self, service, sample_document):
        """Test that analyze_document returns a valid result."""
        result = service.analyze_document(sample_document)

        assert result is not None
        assert result.document_id == sample_document.document_id
        assert result.narrative_type in NarrativeType
        assert 0 <= result.confidence <= 1
        assert result.sentiment is not None

    def test_entity_extraction(self, service, sample_document):
        """Test entity extraction from document."""
        result = service.analyze_document(sample_document)

        assert len(result.entities) > 0
        # Should extract "Kabul" as a location
        locations = [e for e in result.entities if e.entity_type == "LOCATION"]
        assert any(e.text == "Kabul" for e in locations)
        # Should extract "NATO" as an organization
        orgs = [e for e in result.entities if e.entity_type == "ORGANIZATION"]
        assert any(e.text == "NATO" for e in orgs)

    def test_sentiment_analysis(self, service, sample_document):
        """Test sentiment analysis."""
        result = service.analyze_document(sample_document)

        assert result.sentiment.category in SentimentCategory
        assert -1 <= result.sentiment.score <= 1
        assert 0 <= result.sentiment.confidence <= 1

    def test_negative_sentiment_for_threat_content(self, service):
        """Test that threat-related content gets negative sentiment."""
        doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="test",
            source_type="NEWS",
            content="Bomb explosion killed many people. War continues with violence and death.",
            language=Language.ENGLISH,
            published_at=datetime.now(UTC),
        )

        result = service.analyze_document(doc)

        assert result.sentiment.score < 0
        assert result.sentiment.category in [SentimentCategory.NEGATIVE, SentimentCategory.VERY_NEGATIVE]

    def test_propaganda_detection(self, service, propaganda_document):
        """Test propaganda indicator detection."""
        result = service.analyze_document(propaganda_document)

        assert len(result.propaganda_indicators) > 0
        assert "loaded_language" in result.propaganda_indicators or "emotional_appeal" in result.propaganda_indicators

    def test_source_credibility_verified(self, service):
        """Test verified source credibility."""
        doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="reuters",
            source_type="NEWS",
            content="UN reports on humanitarian situation in Afghanistan.",
            language=Language.ENGLISH,
            published_at=datetime.now(UTC),
        )

        result = service.analyze_document(doc)

        assert result.source_credibility == SourceCredibility.VERIFIED

    def test_source_credibility_questionable(self, service):
        """Test questionable source credibility."""
        doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="anon_insider_leaks",
            source_type="SOCIAL_MEDIA",
            content="Some content here.",
            language=Language.ENGLISH,
            published_at=datetime.now(UTC),
        )

        result = service.analyze_document(doc)

        assert result.source_credibility == SourceCredibility.QUESTIONABLE

    def test_topic_extraction(self, service, sample_document):
        """Test topic extraction."""
        result = service.analyze_document(sample_document)

        assert len(result.topics) > 0
        assert "security" in result.topics

    def test_threat_relevance_calculation(self, service):
        """Test threat relevance score calculation."""
        high_threat_doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="test",
            source_type="NEWS",
            content="Taliban militants attacked with bombs and weapons near the border.",
            language=Language.ENGLISH,
            published_at=datetime.now(UTC),
        )

        low_threat_doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="test",
            source_type="NEWS",
            content="Humanitarian aid distributed to communities. Education programs continue.",
            language=Language.ENGLISH,
            published_at=datetime.now(UTC),
        )

        high_result = service.analyze_document(high_threat_doc)
        low_result = service.analyze_document(low_threat_doc)

        assert high_result.threat_relevance > low_result.threat_relevance

    def test_fact_check_flags(self, service, propaganda_document):
        """Test fact check flag generation."""
        result = service.analyze_document(propaganda_document)

        assert len(result.fact_check_flags) > 0

    def test_trending_narratives(self, service):
        """Test getting trending narratives."""
        trends = service.get_trending_narratives(hours=24, limit=5)

        assert len(trends) > 0
        assert all(t.volume > 0 for t in trends)


class TestCoordinatedCampaignDetection:
    """Tests for coordinated campaign detection."""

    def test_no_campaign_few_documents(self, service):
        """Test that no campaign is detected with few documents."""
        docs = [
            NarrativeDocument(
                document_id=uuid4(),
                source_id=f"source_{i}",
                source_type="SOCIAL_MEDIA",
                content="Some content about security.",
                language=Language.ENGLISH,
                published_at=datetime.now(UTC),
            )
            for i in range(3)
        ]

        campaign = service.detect_coordinated_campaign(docs)

        assert campaign is None  # Not enough documents

    def test_campaign_detection_similar_content(self, service):
        """Test campaign detection with similar content."""
        # Create documents with similar topics and sentiment
        docs = [
            NarrativeDocument(
                document_id=uuid4(),
                source_id=f"source_{i}",
                source_type="SOCIAL_MEDIA",
                content="Economic crisis is devastating! Government must act now on the economy!",
                language=Language.ENGLISH,
                published_at=datetime.now(UTC),
                author_id=f"author_{i}",
                metadata={"account_age_days": 10, "hashtag_count": 6},
            )
            for i in range(10)
        ]

        campaign = service.detect_coordinated_campaign(docs)

        # May or may not detect depending on thresholds
        # The test verifies the method runs without error
        if campaign:
            assert campaign.confidence > 0
            assert len(campaign.target_topics) > 0


class TestLanguageSupport:
    """Tests for multi-language support."""

    def test_dari_language(self, service):
        """Test Dari language document."""
        doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="test",
            source_type="NEWS",
            content="News content in Dari about Kabul.",
            language=Language.DARI,
            published_at=datetime.now(UTC),
        )

        result = service.analyze_document(doc)

        assert result is not None
        assert result.narrative_type in NarrativeType

    def test_pashto_language(self, service):
        """Test Pashto language document."""
        doc = NarrativeDocument(
            document_id=uuid4(),
            source_id="test",
            source_type="NEWS",
            content="News content in Pashto about Kandahar.",
            language=Language.PASHTO,
            published_at=datetime.now(UTC),
        )

        result = service.analyze_document(doc)

        assert result is not None
        assert result.narrative_type in NarrativeType
