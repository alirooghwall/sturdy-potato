"""Tests for threat scoring service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.models.domain import Entity, GeoPoint
from src.models.enums import EntityStatus, EntityType, ThreatCategory
from src.services.threat_scoring import ThreatScoringService


@pytest.fixture
def threat_service():
    """Create threat scoring service instance."""
    return ThreatScoringService()


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    return Entity(
        entity_id=uuid4(),
        entity_type=EntityType.INSURGENT_CELL,
        display_name="Test Entity",
        status=EntityStatus.ACTIVE,
        confidence_score=0.75,
        current_position=GeoPoint(latitude=34.5, longitude=69.1),
        attributes={
            "estimated_size": 25,
            "light_weapons": True,
            "heavy_weapons": False,
        },
    )


class TestThreatScoringService:
    """Tests for ThreatScoringService."""

    def test_calculate_score_returns_valid_score(self, threat_service, sample_entity):
        """Test that calculate_score returns a valid ThreatScore."""
        context = {
            "num_corroborating_sources": 3,
            "distance_to_population_center_km": 15,
            "security_presence_level": "MEDIUM",
            "intelligence_age_hours": 12,
        }

        result = threat_service.calculate_score(sample_entity, context)

        assert result is not None
        assert 0 <= result.overall_score <= 100
        assert result.entity_id == sample_entity.entity_id
        assert result.category in ThreatCategory
        assert len(result.factor_scores) == 5
        assert result.model_id == "threat-scorer-ensemble-v1"

    def test_score_category_mapping(self, threat_service):
        """Test that score categories are mapped correctly."""
        assert threat_service._determine_category(10) == ThreatCategory.LOW
        assert threat_service._determine_category(30) == ThreatCategory.LOW
        assert threat_service._determine_category(31) == ThreatCategory.MEDIUM
        assert threat_service._determine_category(60) == ThreatCategory.MEDIUM
        assert threat_service._determine_category(61) == ThreatCategory.HIGH
        assert threat_service._determine_category(85) == ThreatCategory.HIGH
        assert threat_service._determine_category(86) == ThreatCategory.CRITICAL
        assert threat_service._determine_category(100) == ThreatCategory.CRITICAL

    def test_high_threat_context_increases_score(self, threat_service, sample_entity):
        """Test that high-threat context increases score."""
        low_threat_context = {
            "num_corroborating_sources": 0,
            "distance_to_population_center_km": 200,
            "security_presence_level": "HIGH",
            "intelligence_age_hours": 168,
            "civilian_density": "LOW",
        }

        high_threat_context = {
            "num_corroborating_sources": 5,
            "distance_to_population_center_km": 5,
            "near_critical_infrastructure": True,
            "security_presence_level": "LOW",
            "intelligence_age_hours": 2,
            "imminent_threat_indicators": True,
            "civilian_density": "HIGH",
        }

        low_score = threat_service.calculate_score(sample_entity, low_threat_context)
        high_score = threat_service.calculate_score(sample_entity, high_threat_context)

        assert high_score.overall_score > low_score.overall_score

    def test_factor_weights_sum_to_one(self, threat_service):
        """Test that factor weights sum to 1.0."""
        total_weight = sum(threat_service.weights.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_explanation_generated(self, threat_service, sample_entity):
        """Test that explanation is generated."""
        result = threat_service.calculate_score(sample_entity, {})

        assert result.explanation_summary is not None
        assert len(result.explanation_summary) > 0
        assert str(result.overall_score) in result.explanation_summary

    def test_recommendations_generated(self, threat_service, sample_entity):
        """Test that recommendations are generated."""
        context = {
            "num_corroborating_sources": 5,
            "distance_to_population_center_km": 5,
            "intelligence_age_hours": 2,
        }

        result = threat_service.calculate_score(sample_entity, context)

        assert result.recommendations is not None
        assert len(result.recommendations) > 0

    def test_large_group_increases_capability_score(self, threat_service):
        """Test that larger group size increases capability score."""
        small_entity = Entity(
            entity_id=uuid4(),
            entity_type=EntityType.INSURGENT_CELL,
            status=EntityStatus.ACTIVE,
            confidence_score=0.7,
            attributes={"estimated_size": 5},
        )

        large_entity = Entity(
            entity_id=uuid4(),
            entity_type=EntityType.INSURGENT_CELL,
            status=EntityStatus.ACTIVE,
            confidence_score=0.7,
            attributes={"estimated_size": 100},
        )

        small_score = threat_service.calculate_score(small_entity, {})
        large_score = threat_service.calculate_score(large_entity, {})

        # Verify factor_scores structure exists
        assert "capability" in large_score.factor_scores
        assert "capability" in small_score.factor_scores
        assert "score" in large_score.factor_scores["capability"]
        assert "score" in small_score.factor_scores["capability"]

        assert large_score.factor_scores["capability"]["score"] > small_score.factor_scores["capability"]["score"]


class TestThreatScoreFactors:
    """Tests for individual threat score factors."""

    def test_credibility_factor_with_sources(self, threat_service, sample_entity):
        """Test credibility factor calculation with sources."""
        context_no_sources = {"num_corroborating_sources": 0}
        context_many_sources = {"num_corroborating_sources": 5}

        score_no_sources = threat_service._calculate_credibility(sample_entity, context_no_sources)
        score_many_sources = threat_service._calculate_credibility(sample_entity, context_many_sources)

        assert score_many_sources > score_no_sources

    def test_tactical_impact_near_population(self, threat_service, sample_entity):
        """Test tactical impact is higher near population centers."""
        far_context = {"distance_to_population_center_km": 100}
        near_context = {"distance_to_population_center_km": 5}

        far_score = threat_service._calculate_tactical_impact(sample_entity, far_context)
        near_score = threat_service._calculate_tactical_impact(sample_entity, near_context)

        assert near_score > far_score

    def test_time_sensitivity_recent_intel(self, threat_service, sample_entity):
        """Test time sensitivity is higher for recent intelligence."""
        old_context = {"intelligence_age_hours": 168}
        recent_context = {"intelligence_age_hours": 2}

        old_score = threat_service._calculate_time_sensitivity(sample_entity, old_context)
        recent_score = threat_service._calculate_time_sensitivity(sample_entity, recent_context)

        assert recent_score > old_score
