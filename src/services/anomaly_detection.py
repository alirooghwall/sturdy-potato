"""Anomaly detection service for ISR Platform."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import numpy as np

from src.models.domain import Anomaly
from src.models.enums import AnomalyDomain, Severity


@dataclass
class BaselineStats:
    """Baseline statistics for anomaly detection."""

    mean: float
    std: float
    min_val: float
    max_val: float
    period_days: int
    sample_count: int


class AnomalyDetectionService:
    """Service for detecting anomalies across domains."""

    def __init__(self) -> None:
        """Initialize anomaly detection service."""
        self.model_id = "anomaly-detector-v1"
        self.model_version = "1.0.0"

        # Z-score threshold for anomaly detection
        self.z_score_threshold = 3.0

        # Severity thresholds based on anomaly score
        self.severity_thresholds = {
            Severity.LOW: 0.5,
            Severity.MEDIUM: 0.7,
            Severity.HIGH: 0.85,
            Severity.CRITICAL: 0.95,
        }

    def detect_geo_movement_anomaly(
        self,
        location_id: str,
        current_count: int,
        baseline: BaselineStats,
        metadata: dict[str, Any] | None = None,
    ) -> Anomaly | None:
        """Detect anomaly in geo-movement data."""
        metadata = metadata or {}

        # Calculate z-score
        if baseline.std == 0:
            z_score = 0 if current_count == baseline.mean else float("inf")
        else:
            z_score = (current_count - baseline.mean) / baseline.std

        # Check if anomalous
        if abs(z_score) < self.z_score_threshold:
            return None

        # Calculate anomaly score (normalized)
        anomaly_score = min(abs(z_score) / 5.0, 1.0)  # Cap at z=5

        # Determine severity
        severity = self._determine_severity(anomaly_score)

        # Calculate severity score (0-100)
        severity_score = int(anomaly_score * 100)

        # Calculate percent change
        if baseline.mean > 0:
            percent_change = ((current_count - baseline.mean) / baseline.mean) * 100
        else:
            percent_change = float("inf") if current_count > 0 else 0

        # Generate description
        direction = "increase" if z_score > 0 else "decrease"
        description = (
            f"Unusual {direction} in movement activity detected. "
            f"Observed count: {current_count}, baseline average: {baseline.mean:.1f}. "
            f"{abs(percent_change):.0f}% {direction} over {baseline.period_days}-day baseline."
        )

        return Anomaly(
            anomaly_id=uuid4(),
            domain=AnomalyDomain.GEO_MOVEMENT.value,
            anomaly_subtype="UNUSUAL_ACTIVITY_LEVEL",
            severity=severity,
            severity_score=severity_score,
            detected_at=datetime.utcnow(),
            location=metadata.get("location"),
            region=metadata.get("region"),
            description=description,
            baseline_stats={
                "period": f"{baseline.period_days}_DAYS",
                "average_count": baseline.mean,
                "standard_deviation": baseline.std,
                "observed_count": current_count,
                "z_score": z_score,
                "percent_change": percent_change,
            },
            model_id=self.model_id,
            model_version=self.model_version,
            anomaly_score=anomaly_score,
            related_entities=metadata.get("related_entities", []),
            related_events=metadata.get("related_events", []),
        )

    def detect_network_traffic_anomaly(
        self,
        source_id: str,
        metrics: dict[str, float],
        baseline: dict[str, BaselineStats],
        metadata: dict[str, Any] | None = None,
    ) -> Anomaly | None:
        """Detect anomaly in network traffic data."""
        metadata = metadata or {}

        # Check each metric for anomalies
        anomalous_metrics = []
        max_z_score = 0

        for metric_name, current_value in metrics.items():
            if metric_name not in baseline:
                continue

            metric_baseline = baseline[metric_name]
            if metric_baseline.std == 0:
                z_score = 0 if current_value == metric_baseline.mean else float("inf")
            else:
                z_score = (current_value - metric_baseline.mean) / metric_baseline.std

            if abs(z_score) >= self.z_score_threshold:
                anomalous_metrics.append({
                    "metric": metric_name,
                    "z_score": z_score,
                    "current": current_value,
                    "baseline_mean": metric_baseline.mean,
                })
                max_z_score = max(max_z_score, abs(z_score))

        if not anomalous_metrics:
            return None

        # Calculate overall anomaly score
        anomaly_score = min(max_z_score / 5.0, 1.0)
        severity = self._determine_severity(anomaly_score)
        severity_score = int(anomaly_score * 100)

        # Generate description
        metric_list = ", ".join([m["metric"] for m in anomalous_metrics])
        description = (
            f"Network traffic anomaly detected. "
            f"Anomalous metrics: {metric_list}. "
            f"Maximum deviation: {max_z_score:.1f} standard deviations from baseline."
        )

        return Anomaly(
            anomaly_id=uuid4(),
            domain=AnomalyDomain.NETWORK_TRAFFIC.value,
            anomaly_subtype="UNUSUAL_TRAFFIC_PATTERN",
            severity=severity,
            severity_score=severity_score,
            detected_at=datetime.utcnow(),
            region=metadata.get("region"),
            description=description,
            baseline_stats={
                "anomalous_metrics": anomalous_metrics,
                "max_z_score": max_z_score,
            },
            model_id=self.model_id,
            model_version=self.model_version,
            anomaly_score=anomaly_score,
        )

    def detect_economic_anomaly(
        self,
        indicator_name: str,
        current_value: float,
        baseline: BaselineStats,
        metadata: dict[str, Any] | None = None,
    ) -> Anomaly | None:
        """Detect anomaly in economic indicators."""
        metadata = metadata or {}

        # Calculate z-score
        if baseline.std == 0:
            z_score = 0 if current_value == baseline.mean else float("inf")
        else:
            z_score = (current_value - baseline.mean) / baseline.std

        if abs(z_score) < self.z_score_threshold:
            return None

        anomaly_score = min(abs(z_score) / 5.0, 1.0)
        severity = self._determine_severity(anomaly_score)
        severity_score = int(anomaly_score * 100)

        direction = "increase" if z_score > 0 else "decrease"
        description = (
            f"Economic indicator anomaly detected in {indicator_name}. "
            f"Unusual {direction}: current value {current_value:.2f}, "
            f"baseline average {baseline.mean:.2f}."
        )

        return Anomaly(
            anomaly_id=uuid4(),
            domain=AnomalyDomain.ECONOMIC.value,
            anomaly_subtype=f"UNUSUAL_{indicator_name.upper()}",
            severity=severity,
            severity_score=severity_score,
            detected_at=datetime.utcnow(),
            region=metadata.get("region"),
            description=description,
            baseline_stats={
                "indicator": indicator_name,
                "current_value": current_value,
                "baseline_mean": baseline.mean,
                "baseline_std": baseline.std,
                "z_score": z_score,
                "period_days": baseline.period_days,
            },
            model_id=self.model_id,
            model_version=self.model_version,
            anomaly_score=anomaly_score,
        )

    def detect_social_media_anomaly(
        self,
        topic: str,
        current_volume: int,
        baseline: BaselineStats,
        sentiment_shift: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Anomaly | None:
        """Detect anomaly in social media activity."""
        metadata = metadata or {}

        # Calculate z-score for volume
        if baseline.std == 0:
            z_score = 0 if current_volume == baseline.mean else float("inf")
        else:
            z_score = (current_volume - baseline.mean) / baseline.std

        # Also consider sentiment shift as an anomaly signal
        sentiment_anomaly = sentiment_shift is not None and abs(sentiment_shift) > 0.3

        if abs(z_score) < self.z_score_threshold and not sentiment_anomaly:
            return None

        # Combine signals for anomaly score
        volume_score = min(abs(z_score) / 5.0, 1.0) if abs(z_score) >= self.z_score_threshold else 0
        sentiment_score = min(abs(sentiment_shift) / 0.5, 1.0) if sentiment_anomaly else 0
        anomaly_score = max(volume_score, sentiment_score)

        severity = self._determine_severity(anomaly_score)
        severity_score = int(anomaly_score * 100)

        # Generate description
        description_parts = [f"Social media anomaly detected for topic '{topic}'."]
        if abs(z_score) >= self.z_score_threshold:
            direction = "surge" if z_score > 0 else "drop"
            description_parts.append(
                f"Volume {direction}: {current_volume} posts vs baseline {baseline.mean:.0f}."
            )
        if sentiment_anomaly:
            sentiment_dir = "positive" if sentiment_shift > 0 else "negative"
            description_parts.append(f"Significant {sentiment_dir} sentiment shift detected.")

        return Anomaly(
            anomaly_id=uuid4(),
            domain=AnomalyDomain.SOCIAL_MEDIA.value,
            anomaly_subtype="UNUSUAL_SOCIAL_ACTIVITY",
            severity=severity,
            severity_score=severity_score,
            detected_at=datetime.utcnow(),
            region=metadata.get("region"),
            description=" ".join(description_parts),
            baseline_stats={
                "topic": topic,
                "current_volume": current_volume,
                "baseline_mean": baseline.mean,
                "baseline_std": baseline.std,
                "z_score": z_score,
                "sentiment_shift": sentiment_shift,
            },
            model_id=self.model_id,
            model_version=self.model_version,
            anomaly_score=anomaly_score,
        )

    def _determine_severity(self, anomaly_score: float) -> Severity:
        """Determine severity level from anomaly score."""
        if anomaly_score >= self.severity_thresholds[Severity.CRITICAL]:
            return Severity.CRITICAL
        elif anomaly_score >= self.severity_thresholds[Severity.HIGH]:
            return Severity.HIGH
        elif anomaly_score >= self.severity_thresholds[Severity.MEDIUM]:
            return Severity.MEDIUM
        else:
            return Severity.LOW


# Global instance
_anomaly_service: AnomalyDetectionService | None = None


def get_anomaly_service() -> AnomalyDetectionService:
    """Get the anomaly detection service instance."""
    global _anomaly_service
    if _anomaly_service is None:
        _anomaly_service = AnomalyDetectionService()
    return _anomaly_service
