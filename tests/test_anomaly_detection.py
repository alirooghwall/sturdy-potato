"""Tests for anomaly detection service."""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.enums import Severity
from src.services.anomaly_detection import AnomalyDetectionService, BaselineStats


@pytest.fixture
def anomaly_service():
    """Create anomaly detection service instance."""
    return AnomalyDetectionService()


@pytest.fixture
def normal_baseline():
    """Create a normal baseline for testing."""
    return BaselineStats(
        mean=100.0,
        std=10.0,
        min_val=70.0,
        max_val=130.0,
        period_days=30,
        sample_count=30,
    )


class TestAnomalyDetectionService:
    """Tests for AnomalyDetectionService."""

    def test_no_anomaly_for_normal_value(self, anomaly_service, normal_baseline):
        """Test that no anomaly is detected for normal values."""
        result = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=105,  # Within 1 std of mean
            baseline=normal_baseline,
        )

        assert result is None

    def test_anomaly_detected_for_high_value(self, anomaly_service, normal_baseline):
        """Test that anomaly is detected for abnormally high values."""
        result = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=150,  # 5 std above mean
            baseline=normal_baseline,
        )

        assert result is not None
        assert result.domain == "GEO_MOVEMENT"
        assert "increase" in result.description.lower()

    def test_anomaly_detected_for_low_value(self, anomaly_service, normal_baseline):
        """Test that anomaly is detected for abnormally low values."""
        result = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=50,  # 5 std below mean
            baseline=normal_baseline,
        )

        assert result is not None
        assert "decrease" in result.description.lower()

    def test_severity_based_on_score(self, anomaly_service, normal_baseline):
        """Test that severity is determined by anomaly score."""
        # Moderate anomaly
        moderate = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=140,  # 4 std above
            baseline=normal_baseline,
        )

        # Extreme anomaly
        extreme = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=200,  # 10 std above
            baseline=normal_baseline,
        )

        assert moderate is not None
        assert extreme is not None
        assert extreme.severity_score >= moderate.severity_score

    def test_baseline_stats_included(self, anomaly_service, normal_baseline):
        """Test that baseline stats are included in anomaly."""
        result = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=150,
            baseline=normal_baseline,
        )

        assert result is not None
        assert "average_count" in result.baseline_stats
        assert "z_score" in result.baseline_stats
        assert "percent_change" in result.baseline_stats

    def test_metadata_included(self, anomaly_service, normal_baseline):
        """Test that metadata is included in anomaly."""
        metadata = {
            "region": "Test Region",
            "location_id": "test-loc-123",
        }

        result = anomaly_service.detect_geo_movement_anomaly(
            location_id="test-location",
            current_count=150,
            baseline=normal_baseline,
            metadata=metadata,
        )

        assert result is not None
        assert result.region == "Test Region"


class TestSocialMediaAnomalyDetection:
    """Tests for social media anomaly detection."""

    def test_volume_anomaly_detected(self, anomaly_service, normal_baseline):
        """Test that volume anomaly is detected."""
        result = anomaly_service.detect_social_media_anomaly(
            topic="test-topic",
            current_volume=200,  # 10 std above mean
            baseline=normal_baseline,
        )

        assert result is not None
        assert result.domain == "SOCIAL_MEDIA"
        assert "surge" in result.description.lower()

    def test_sentiment_shift_anomaly(self, anomaly_service, normal_baseline):
        """Test that sentiment shift triggers anomaly."""
        result = anomaly_service.detect_social_media_anomaly(
            topic="test-topic",
            current_volume=100,  # Normal volume
            baseline=normal_baseline,
            sentiment_shift=-0.5,  # Significant negative shift
        )

        assert result is not None
        assert "sentiment" in result.description.lower()

    def test_no_anomaly_normal_sentiment(self, anomaly_service, normal_baseline):
        """Test no anomaly for normal sentiment and volume."""
        result = anomaly_service.detect_social_media_anomaly(
            topic="test-topic",
            current_volume=100,
            baseline=normal_baseline,
            sentiment_shift=0.1,  # Minor shift
        )

        assert result is None


class TestNetworkTrafficAnomalyDetection:
    """Tests for network traffic anomaly detection."""

    def test_single_metric_anomaly(self, anomaly_service):
        """Test anomaly detection with single metric."""
        baseline = {
            "bytes_in": BaselineStats(
                mean=1000000, std=100000, min_val=0, max_val=2000000, period_days=7, sample_count=168
            ),
            "bytes_out": BaselineStats(
                mean=500000, std=50000, min_val=0, max_val=1000000, period_days=7, sample_count=168
            ),
        }

        metrics = {
            "bytes_in": 1500000,  # 5 std above
            "bytes_out": 500000,  # Normal
        }

        result = anomaly_service.detect_network_traffic_anomaly(
            source_id="test-network",
            metrics=metrics,
            baseline=baseline,
        )

        assert result is not None
        assert result.domain == "NETWORK_TRAFFIC"

    def test_no_anomaly_normal_traffic(self, anomaly_service):
        """Test no anomaly for normal traffic."""
        baseline = {
            "bytes_in": BaselineStats(
                mean=1000000, std=100000, min_val=0, max_val=2000000, period_days=7, sample_count=168
            ),
        }

        metrics = {"bytes_in": 1050000}  # Within normal range

        result = anomaly_service.detect_network_traffic_anomaly(
            source_id="test-network",
            metrics=metrics,
            baseline=baseline,
        )

        assert result is None


class TestEconomicAnomalyDetection:
    """Tests for economic indicator anomaly detection."""

    def test_economic_anomaly_detected(self, anomaly_service, normal_baseline):
        """Test economic anomaly detection."""
        result = anomaly_service.detect_economic_anomaly(
            indicator_name="exchange_rate",
            current_value=150.0,
            baseline=normal_baseline,
        )

        assert result is not None
        assert result.domain == "ECONOMIC"
        assert "exchange_rate" in result.description.lower()

    def test_no_anomaly_stable_indicator(self, anomaly_service, normal_baseline):
        """Test no anomaly for stable economic indicator."""
        result = anomaly_service.detect_economic_anomaly(
            indicator_name="exchange_rate",
            current_value=102.0,  # Within normal range
            baseline=normal_baseline,
        )

        assert result is None


class TestSeverityDetermination:
    """Tests for severity determination logic."""

    def test_severity_thresholds(self, anomaly_service):
        """Test severity is determined by thresholds."""
        assert anomaly_service._determine_severity(0.4) == Severity.LOW
        assert anomaly_service._determine_severity(0.75) == Severity.MEDIUM
        assert anomaly_service._determine_severity(0.9) == Severity.HIGH
        assert anomaly_service._determine_severity(0.98) == Severity.CRITICAL
