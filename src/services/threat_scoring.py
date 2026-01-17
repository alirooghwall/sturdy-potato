"""Threat scoring service for ISR Platform."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from src.models.domain import Entity, ThreatScore
from src.models.enums import ThreatCategory


class ThreatScoringService:
    """Service for calculating threat scores."""

    def __init__(self) -> None:
        """Initialize the threat scoring service."""
        self.model_id = "threat-scorer-ensemble-v1"
        self.model_version = "1.0.0"

        # Factor weights
        self.weights = {
            "credibility": 0.20,
            "tactical_impact": 0.25,
            "capability": 0.20,
            "vulnerability": 0.20,
            "time_sensitivity": 0.15,
        }

    def calculate_score(
        self,
        entity: Entity,
        context: dict[str, Any] | None = None,
    ) -> ThreatScore:
        """Calculate threat score for an entity."""
        context = context or {}

        # Calculate individual factor scores
        factor_scores = self._calculate_factor_scores(entity, context)

        # Calculate overall score
        overall_score = self._calculate_overall_score(factor_scores)

        # Determine category
        category = self._determine_category(overall_score)

        # Generate explanation
        explanation = self._generate_explanation(entity, factor_scores, overall_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(entity, factor_scores)

        # Determine trend (would need historical data in production)
        trend_direction = "STABLE"

        return ThreatScore(
            entity_id=entity.entity_id,
            overall_score=overall_score,
            category=category,
            factor_scores=factor_scores,
            explanation_summary=explanation,
            key_indicators=self._extract_key_indicators(context),
            recommendations=recommendations,
            model_id=self.model_id,
            model_version=self.model_version,
            context_window_start=context.get(
                "window_start", datetime.utcnow() - timedelta(days=7)
            ),
            context_window_end=context.get("window_end", datetime.utcnow()),
            trend_direction=trend_direction,
        )

    def _calculate_factor_scores(
        self,
        entity: Entity,
        context: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """Calculate individual factor scores."""
        factors = {}

        # Credibility score
        credibility_score = self._calculate_credibility(entity, context)
        factors["credibility"] = {
            "score": credibility_score,
            "weight": self.weights["credibility"],
            "contribution": credibility_score * self.weights["credibility"],
            "details": self._get_credibility_details(entity, context),
        }

        # Tactical impact score
        tactical_score = self._calculate_tactical_impact(entity, context)
        factors["tactical_impact"] = {
            "score": tactical_score,
            "weight": self.weights["tactical_impact"],
            "contribution": tactical_score * self.weights["tactical_impact"],
            "details": self._get_tactical_details(entity, context),
        }

        # Capability score
        capability_score = self._calculate_capability(entity, context)
        factors["capability"] = {
            "score": capability_score,
            "weight": self.weights["capability"],
            "contribution": capability_score * self.weights["capability"],
            "details": self._get_capability_details(entity, context),
        }

        # Vulnerability score
        vulnerability_score = self._calculate_vulnerability(entity, context)
        factors["vulnerability"] = {
            "score": vulnerability_score,
            "weight": self.weights["vulnerability"],
            "contribution": vulnerability_score * self.weights["vulnerability"],
            "details": self._get_vulnerability_details(entity, context),
        }

        # Time sensitivity score
        time_score = self._calculate_time_sensitivity(entity, context)
        factors["time_sensitivity"] = {
            "score": time_score,
            "weight": self.weights["time_sensitivity"],
            "contribution": time_score * self.weights["time_sensitivity"],
            "details": self._get_time_details(entity, context),
        }

        return factors

    def _calculate_credibility(
        self, entity: Entity, context: dict[str, Any]
    ) -> int:
        """Calculate credibility factor score."""
        base_score = 50

        # Adjust based on confidence score
        base_score += int(entity.confidence_score * 30)

        # Adjust based on number of sources
        num_sources = context.get("num_corroborating_sources", 0)
        base_score += min(num_sources * 5, 20)

        return min(max(base_score, 0), 100)

    def _calculate_tactical_impact(
        self, entity: Entity, context: dict[str, Any]
    ) -> int:
        """Calculate tactical impact factor score."""
        base_score = 50

        # Adjust based on proximity to population centers
        distance_km = context.get("distance_to_population_center_km", 100)
        if distance_km < 10:
            base_score += 30
        elif distance_km < 25:
            base_score += 20
        elif distance_km < 50:
            base_score += 10

        # Adjust based on proximity to critical infrastructure
        near_infrastructure = context.get("near_critical_infrastructure", False)
        if near_infrastructure:
            base_score += 15

        return min(max(base_score, 0), 100)

    def _calculate_capability(
        self, entity: Entity, context: dict[str, Any]
    ) -> int:
        """Calculate capability factor score."""
        base_score = 50

        # Adjust based on entity attributes
        attributes = entity.attributes

        # Group size
        group_size = attributes.get("estimated_size", 0)
        if group_size > 50:
            base_score += 25
        elif group_size > 20:
            base_score += 15
        elif group_size > 10:
            base_score += 10

        # Weapons capability
        if attributes.get("heavy_weapons", False):
            base_score += 20
        elif attributes.get("light_weapons", False):
            base_score += 10

        return min(max(base_score, 0), 100)

    def _calculate_vulnerability(
        self, entity: Entity, context: dict[str, Any]
    ) -> int:
        """Calculate vulnerability factor score."""
        base_score = 50

        # Adjust based on target vulnerability
        security_presence = context.get("security_presence_level", "MEDIUM")
        if security_presence == "LOW":
            base_score += 25
        elif security_presence == "MEDIUM":
            base_score += 10
        elif security_presence == "HIGH":
            base_score -= 10

        # Adjust for civilian exposure
        civilian_density = context.get("civilian_density", "MEDIUM")
        if civilian_density == "HIGH":
            base_score += 20
        elif civilian_density == "MEDIUM":
            base_score += 10

        return min(max(base_score, 0), 100)

    def _calculate_time_sensitivity(
        self, entity: Entity, context: dict[str, Any]
    ) -> int:
        """Calculate time sensitivity factor score."""
        base_score = 50

        # Adjust based on intelligence age
        intel_age_hours = context.get("intelligence_age_hours", 24)
        if intel_age_hours < 6:
            base_score += 30
        elif intel_age_hours < 24:
            base_score += 20
        elif intel_age_hours < 72:
            base_score += 10

        # Adjust for imminent threat indicators
        if context.get("imminent_threat_indicators", False):
            base_score += 20

        return min(max(base_score, 0), 100)

    def _calculate_overall_score(
        self, factor_scores: dict[str, dict[str, Any]]
    ) -> int:
        """Calculate overall threat score from factors."""
        total = sum(f["contribution"] for f in factor_scores.values())
        return min(max(int(total), 0), 100)

    def _determine_category(self, score: int) -> ThreatCategory:
        """Determine threat category from score."""
        if score >= 86:
            return ThreatCategory.CRITICAL
        elif score >= 61:
            return ThreatCategory.HIGH
        elif score >= 31:
            return ThreatCategory.MEDIUM
        else:
            return ThreatCategory.LOW

    def _generate_explanation(
        self,
        entity: Entity,
        factor_scores: dict[str, dict[str, Any]],
        overall_score: int,
    ) -> str:
        """Generate natural language explanation of the threat score."""
        category = self._determine_category(overall_score)

        # Find top contributing factors
        sorted_factors = sorted(
            factor_scores.items(),
            key=lambda x: x[1]["contribution"],
            reverse=True,
        )
        top_factors = sorted_factors[:3]

        explanation_parts = [
            f"The threat score of {overall_score} ({category.value}) "
            f"for entity {entity.display_name or entity.entity_id} "
            "was primarily driven by: "
        ]

        for i, (factor_name, factor_data) in enumerate(top_factors):
            explanation_parts.append(
                f"({i+1}) {factor_name.replace('_', ' ').title()} "
                f"(score: {factor_data['score']}, contribution: {factor_data['contribution']:.1f})"
            )
            if factor_data.get("details"):
                explanation_parts.append(f" - {factor_data['details']}")
            if i < len(top_factors) - 1:
                explanation_parts.append("; ")

        return "".join(explanation_parts)

    def _generate_recommendations(
        self,
        entity: Entity,
        factor_scores: dict[str, dict[str, Any]],
    ) -> list[str]:
        """Generate recommendations based on threat assessment."""
        recommendations = []

        # High credibility suggests action needed
        if factor_scores["credibility"]["score"] > 70:
            recommendations.append(
                "High credibility intelligence - consider immediate response planning"
            )

        # High tactical impact
        if factor_scores["tactical_impact"]["score"] > 70:
            recommendations.append(
                "High tactical impact - increase ISR coverage in affected area"
            )

        # High vulnerability
        if factor_scores["vulnerability"]["score"] > 70:
            recommendations.append(
                "Target area shows high vulnerability - consider security reinforcement"
            )

        # Time sensitive
        if factor_scores["time_sensitivity"]["score"] > 70:
            recommendations.append(
                "Time-sensitive intelligence - expedite analysis and decision-making"
            )

        if not recommendations:
            recommendations.append("Continue monitoring - no immediate action required")

        return recommendations

    def _extract_key_indicators(self, context: dict[str, Any]) -> list[str]:
        """Extract key indicators from context."""
        indicators = []

        if context.get("num_corroborating_sources", 0) > 0:
            indicators.append(
                f"{context['num_corroborating_sources']} corroborating intelligence reports"
            )

        if context.get("recent_activity_detected", False):
            indicators.append("Recent activity detected in area of interest")

        if context.get("sigint_intercepts", 0) > 0:
            indicators.append(
                f"SIGINT intercepts: {context['sigint_intercepts']} relevant communications"
            )

        return indicators

    def _get_credibility_details(
        self, entity: Entity, context: dict[str, Any]
    ) -> str:
        """Get details for credibility factor."""
        num_sources = context.get("num_corroborating_sources", 0)
        return f"Based on {num_sources} corroborating sources, confidence: {entity.confidence_score:.0%}"

    def _get_tactical_details(
        self, entity: Entity, context: dict[str, Any]
    ) -> str:
        """Get details for tactical impact factor."""
        distance = context.get("distance_to_population_center_km", "unknown")
        return f"Distance to nearest population center: {distance}km"

    def _get_capability_details(
        self, entity: Entity, context: dict[str, Any]
    ) -> str:
        """Get details for capability factor."""
        size = entity.attributes.get("estimated_size", "unknown")
        return f"Estimated group size: {size}"

    def _get_vulnerability_details(
        self, entity: Entity, context: dict[str, Any]
    ) -> str:
        """Get details for vulnerability factor."""
        security = context.get("security_presence_level", "unknown")
        return f"Security presence level: {security}"

    def _get_time_details(
        self, entity: Entity, context: dict[str, Any]
    ) -> str:
        """Get details for time sensitivity factor."""
        age = context.get("intelligence_age_hours", "unknown")
        return f"Intelligence age: {age} hours"


# Global instance
_threat_service: ThreatScoringService | None = None


def get_threat_service() -> ThreatScoringService:
    """Get the threat scoring service instance."""
    global _threat_service
    if _threat_service is None:
        _threat_service = ThreatScoringService()
    return _threat_service
