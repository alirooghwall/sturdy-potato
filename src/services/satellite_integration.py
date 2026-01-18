"""Integration service connecting satellite analysis with other platform features.

Connects satellite imagery analysis with:
- Narrative tracking and analysis
- Credibility scoring
- Threat detection
- Alert generation
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from .temporal_analysis import (
    AlertSeverity,
    DeforestationAnalysis,
    UrbanGrowthAnalysis,
    FloodAnalysis,
    AgricultureAnalysis,
    WildfireAnalysis,
    get_temporal_engine,
)
from .narrative_tracker import get_narrative_tracker
from .credibility_scoring import get_credibility_scorer, SourceType
from src.models.enums import ThreatCategory as ThreatLevel


logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class SatelliteEventType(str, Enum):
    """Types of satellite-detected events."""
    DEFORESTATION = "DEFORESTATION"
    URBAN_EXPANSION = "URBAN_EXPANSION"
    FLOODING = "FLOODING"
    AGRICULTURAL_STRESS = "AGRICULTURAL_STRESS"
    WILDFIRE = "WILDFIRE"
    INFRASTRUCTURE_CHANGE = "INFRASTRUCTURE_CHANGE"
    ENVIRONMENTAL_DEGRADATION = "ENVIRONMENTAL_DEGRADATION"


@dataclass
class SatelliteAlert:
    """Alert generated from satellite analysis."""
    alert_id: UUID
    event_type: SatelliteEventType
    severity: AlertSeverity
    location: dict[str, Any]  # Lat/lon coordinates
    area_affected_hectares: float
    detection_date: datetime
    confidence: float
    description: str
    analysis_id: UUID
    metadata: dict[str, Any] = field(default_factory=dict)
    narrative_ids: list[UUID] = field(default_factory=list)
    threat_level: ThreatLevel | None = None
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class SatelliteNarrativeLink:
    """Link between satellite event and narrative."""
    link_id: UUID
    alert_id: UUID
    narrative_id: UUID
    correlation_score: float  # 0-1
    evidence: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)


class SatelliteIntegrationService:
    """Service for integrating satellite analysis with platform features."""

    def __init__(self):
        """Initialize integration service."""
        self.temporal_engine = get_temporal_engine()
        self.narrative_tracker = get_narrative_tracker()
        self.credibility_scorer = get_credibility_scorer()
        
        self.alerts: dict[UUID, SatelliteAlert] = {}
        self.narrative_links: dict[UUID, SatelliteNarrativeLink] = {}
        
        logger.info("Satellite integration service initialized")
    
    def process_deforestation_alert(
        self,
        analysis: DeforestationAnalysis,
    ) -> SatelliteAlert:
        """Process deforestation analysis and generate alert."""
        alert_id = uuid4()
        
        # Extract location from affected areas
        location = {}
        if analysis.affected_areas:
            location = analysis.affected_areas[0]["centroid"]
        else:
            # Use bbox center
            location = {
                "lat": (analysis.bbox.min_lat + analysis.bbox.max_lat) / 2,
                "lon": (analysis.bbox.min_lon + analysis.bbox.max_lon) / 2,
            }
        
        # Generate description
        description = (
            f"Deforestation detected: {analysis.forest_loss_hectares:.1f} hectares "
            f"({analysis.forest_loss_percentage:.1f}%) of forest lost between "
            f"{analysis.before_date.date()} and {analysis.after_date.date()}"
        )
        
        # Determine threat level
        threat_level = self._assess_deforestation_threat(analysis)
        
        # Generate recommendations
        recommendations = self._generate_deforestation_recommendations(analysis)
        
        alert = SatelliteAlert(
            alert_id=alert_id,
            event_type=SatelliteEventType.DEFORESTATION,
            severity=analysis.severity,
            location=location,
            area_affected_hectares=analysis.forest_loss_hectares,
            detection_date=analysis.after_date,
            confidence=analysis.confidence,
            description=description,
            analysis_id=analysis.analysis_id,
            metadata={
                "forest_loss_percentage": analysis.forest_loss_percentage,
                "affected_areas_count": len(analysis.affected_areas),
                "bbox": analysis.bbox.to_dict(),
            },
            threat_level=threat_level,
            recommended_actions=recommendations,
        )
        
        self.alerts[alert_id] = alert
        
        # Try to link with narratives
        self._link_to_narratives(alert, ["deforestation", "environment", "forest", "logging"])
        
        # Create credibility entry for satellite source
        self._register_satellite_source(alert)
        
        logger.info(f"Deforestation alert generated: {alert_id}")
        return alert
    
    def process_flood_alert(
        self,
        analysis: FloodAnalysis,
    ) -> SatelliteAlert:
        """Process flood analysis and generate alert."""
        alert_id = uuid4()
        
        location = {}
        if analysis.affected_locations:
            location = analysis.affected_locations[0]["centroid"]
        else:
            location = {
                "lat": (analysis.bbox.min_lat + analysis.bbox.max_lat) / 2,
                "lon": (analysis.bbox.min_lon + analysis.bbox.max_lon) / 2,
            }
        
        description = (
            f"Flooding detected: {analysis.flooded_area_hectares:.1f} hectares "
            f"({analysis.flooded_area_percentage:.1f}%) inundated on "
            f"{analysis.event_date.date()}"
        )
        
        threat_level = self._assess_flood_threat(analysis)
        recommendations = self._generate_flood_recommendations(analysis)
        
        alert = SatelliteAlert(
            alert_id=alert_id,
            event_type=SatelliteEventType.FLOODING,
            severity=analysis.severity,
            location=location,
            area_affected_hectares=analysis.flooded_area_hectares,
            detection_date=analysis.event_date,
            confidence=analysis.confidence,
            description=description,
            analysis_id=analysis.analysis_id,
            metadata={
                "flooding_percentage": analysis.flooded_area_percentage,
                "affected_locations_count": len(analysis.affected_locations),
                "bbox": analysis.bbox.to_dict(),
            },
            threat_level=threat_level,
            recommended_actions=recommendations,
        )
        
        self.alerts[alert_id] = alert
        self._link_to_narratives(alert, ["flood", "water", "disaster", "emergency"])
        self._register_satellite_source(alert)
        
        logger.info(f"Flood alert generated: {alert_id}")
        return alert
    
    def process_wildfire_alert(
        self,
        analysis: WildfireAnalysis,
    ) -> SatelliteAlert:
        """Process wildfire analysis and generate alert."""
        alert_id = uuid4()
        
        location = {}
        if analysis.active_fire_locations:
            location = analysis.active_fire_locations[0]["centroid"]
        else:
            location = {
                "lat": (analysis.bbox.min_lat + analysis.bbox.max_lat) / 2,
                "lon": (analysis.bbox.min_lon + analysis.bbox.max_lon) / 2,
            }
        
        description = (
            f"Wildfire detected: {analysis.burned_area_hectares:.1f} hectares burned "
            f"with {analysis.fire_intensity} intensity on {analysis.detection_date.date()}"
        )
        
        threat_level = self._assess_wildfire_threat(analysis)
        recommendations = self._generate_wildfire_recommendations(analysis)
        
        alert = SatelliteAlert(
            alert_id=alert_id,
            event_type=SatelliteEventType.WILDFIRE,
            severity=analysis.severity,
            location=location,
            area_affected_hectares=analysis.burned_area_hectares,
            detection_date=analysis.detection_date,
            confidence=analysis.confidence,
            description=description,
            analysis_id=analysis.analysis_id,
            metadata={
                "fire_intensity": analysis.fire_intensity,
                "active_fire_count": len(analysis.active_fire_locations),
                "smoke_detected": analysis.smoke_detected,
                "bbox": analysis.bbox.to_dict(),
            },
            threat_level=threat_level,
            recommended_actions=recommendations,
        )
        
        self.alerts[alert_id] = alert
        self._link_to_narratives(alert, ["fire", "wildfire", "burn", "smoke"])
        self._register_satellite_source(alert)
        
        logger.info(f"Wildfire alert generated: {alert_id}")
        return alert
    
    def process_urban_growth_alert(
        self,
        analysis: UrbanGrowthAnalysis,
    ) -> SatelliteAlert:
        """Process urban growth analysis and generate alert."""
        alert_id = uuid4()
        
        location = {}
        if analysis.new_urban_areas:
            location = analysis.new_urban_areas[0]["centroid"]
        else:
            location = {
                "lat": (analysis.bbox.min_lat + analysis.bbox.max_lat) / 2,
                "lon": (analysis.bbox.min_lon + analysis.bbox.max_lon) / 2,
            }
        
        description = (
            f"Urban expansion detected: {analysis.urban_expansion_hectares:.1f} hectares "
            f"({analysis.urban_expansion_percentage:.1f}%) new development at "
            f"{analysis.growth_rate_annual:.1f}%/year"
        )
        
        # Urban growth is usually informational
        severity = AlertSeverity.INFO
        if analysis.urban_expansion_percentage > 20:
            severity = AlertSeverity.MEDIUM
        if analysis.urban_expansion_percentage > 40:
            severity = AlertSeverity.HIGH
        
        threat_level = ThreatLevel.LOW  # Usually not a threat
        recommendations = [
            "Monitor for infrastructure development",
            "Assess environmental impact",
            "Track population movement patterns",
        ]
        
        alert = SatelliteAlert(
            alert_id=alert_id,
            event_type=SatelliteEventType.URBAN_EXPANSION,
            severity=severity,
            location=location,
            area_affected_hectares=analysis.urban_expansion_hectares,
            detection_date=analysis.after_date,
            confidence=0.8,
            description=description,
            analysis_id=analysis.analysis_id,
            metadata={
                "expansion_percentage": analysis.urban_expansion_percentage,
                "growth_rate_annual": analysis.growth_rate_annual,
                "infrastructure_detected": analysis.infrastructure_detected,
                "bbox": analysis.bbox.to_dict(),
            },
            threat_level=threat_level,
            recommended_actions=recommendations,
        )
        
        self.alerts[alert_id] = alert
        self._link_to_narratives(alert, ["urban", "development", "construction", "infrastructure"])
        self._register_satellite_source(alert)
        
        logger.info(f"Urban growth alert generated: {alert_id}")
        return alert
    
    def process_agriculture_alert(
        self,
        analysis: AgricultureAnalysis,
    ) -> SatelliteAlert:
        """Process agriculture analysis and generate alert."""
        alert_id = uuid4()
        
        location = {
            "lat": (analysis.bbox.min_lat + analysis.bbox.max_lat) / 2,
            "lon": (analysis.bbox.min_lon + analysis.bbox.max_lon) / 2,
        }
        
        description = (
            f"Agricultural monitoring: {analysis.crop_area_hectares:.1f} hectares "
            f"of crops in {analysis.health_status} condition "
            f"(health index: {analysis.crop_health_index:.2f})"
        )
        
        # Determine severity based on health status
        if analysis.health_status == "POOR":
            severity = AlertSeverity.HIGH
        elif analysis.health_status == "STRESSED":
            severity = AlertSeverity.MEDIUM
        elif analysis.health_status == "FAIR":
            severity = AlertSeverity.LOW
        else:
            severity = AlertSeverity.INFO
        
        threat_level = ThreatLevel.LOW
        if analysis.health_status in ["POOR", "STRESSED"]:
            threat_level = ThreatLevel.MEDIUM
        
        alert = SatelliteAlert(
            alert_id=alert_id,
            event_type=SatelliteEventType.AGRICULTURAL_STRESS,
            severity=severity,
            location=location,
            area_affected_hectares=analysis.crop_area_hectares,
            detection_date=analysis.analysis_date,
            confidence=0.75,
            description=description,
            analysis_id=analysis.analysis_id,
            metadata={
                "crop_health_index": analysis.crop_health_index,
                "health_status": analysis.health_status,
                "vegetation_vigor": analysis.vegetation_vigor,
                "irrigation_detected": analysis.irrigation_detected,
                "bbox": analysis.bbox.to_dict(),
            },
            threat_level=threat_level,
            recommended_actions=analysis.recommendations,
        )
        
        self.alerts[alert_id] = alert
        self._link_to_narratives(alert, ["agriculture", "crop", "farming", "drought"])
        self._register_satellite_source(alert)
        
        logger.info(f"Agriculture alert generated: {alert_id}")
        return alert
    
    def _link_to_narratives(
        self,
        alert: SatelliteAlert,
        keywords: list[str],
    ) -> None:
        """Link satellite alert to relevant narratives."""
        # Get active narratives
        active_narratives = self.narrative_tracker.get_active_narratives(min_volume=5)
        
        for narrative in active_narratives:
            # Check if narrative keywords match
            narrative_keywords = []
            if narrative.snapshots:
                latest = narrative.snapshots[-1]
                narrative_keywords = latest.top_keywords[:10]
            
            # Calculate correlation
            matches = sum(1 for kw in keywords if any(nkw.lower() in kw.lower() for nkw in narrative_keywords))
            correlation_score = matches / len(keywords) if keywords else 0
            
            if correlation_score > 0.3:  # Threshold for correlation
                link_id = uuid4()
                link = SatelliteNarrativeLink(
                    link_id=link_id,
                    alert_id=alert.alert_id,
                    narrative_id=narrative.narrative_id,
                    correlation_score=correlation_score,
                    evidence=[
                        f"Satellite event: {alert.event_type.value}",
                        f"Location: {alert.location}",
                        f"Matching keywords: {matches}/{len(keywords)}",
                    ],
                )
                
                self.narrative_links[link_id] = link
                alert.narrative_ids.append(narrative.narrative_id)
                
                logger.info(f"Linked alert {alert.alert_id} to narrative {narrative.narrative_id}")
    
    def _register_satellite_source(self, alert: SatelliteAlert) -> None:
        """Register satellite as credible source."""
        source_id = f"satellite_{alert.event_type.value.lower()}"
        
        # Score the satellite source
        self.credibility_scorer.score_source(
            source_id=source_id,
            source_type=SourceType.UNKNOWN,  # Could add SATELLITE type
            metadata={
                "source_type": "satellite_imagery",
                "provider": "multi-source",
                "verified": True,
                "confidence": alert.confidence,
                "analysis_type": alert.event_type.value,
            },
        )
        
        # Update source accuracy (satellite data is typically accurate)
        self.credibility_scorer.update_source_accuracy(source_id, accurate=True)
    
    def _assess_deforestation_threat(self, analysis: DeforestationAnalysis) -> ThreatLevel:
        """Assess threat level from deforestation."""
        if analysis.forest_loss_percentage > 30:
            return ThreatLevel.HIGH
        elif analysis.forest_loss_percentage > 15:
            return ThreatLevel.MEDIUM
        elif analysis.forest_loss_percentage > 5:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.NEGLIGIBLE
    
    def _assess_flood_threat(self, analysis: FloodAnalysis) -> ThreatLevel:
        """Assess threat level from flooding."""
        if analysis.severity == AlertSeverity.CRITICAL:
            return ThreatLevel.CRITICAL
        elif analysis.severity == AlertSeverity.HIGH:
            return ThreatLevel.HIGH
        elif analysis.severity == AlertSeverity.MEDIUM:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _assess_wildfire_threat(self, analysis: WildfireAnalysis) -> ThreatLevel:
        """Assess threat level from wildfire."""
        if analysis.fire_intensity == "EXTREME":
            return ThreatLevel.CRITICAL
        elif analysis.fire_intensity == "HIGH":
            return ThreatLevel.HIGH
        elif analysis.fire_intensity == "MEDIUM":
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _generate_deforestation_recommendations(
        self,
        analysis: DeforestationAnalysis,
    ) -> list[str]:
        """Generate recommendations for deforestation."""
        recommendations = []
        
        if analysis.severity == AlertSeverity.CRITICAL:
            recommendations.append("URGENT: Deploy ground verification team")
            recommendations.append("Contact environmental authorities immediately")
        
        recommendations.append("Monitor area with high-frequency satellite passes")
        recommendations.append("Cross-reference with land use permits")
        recommendations.append("Investigate potential illegal logging")
        
        if analysis.forest_loss_percentage > 20:
            recommendations.append("Assess biodiversity impact")
            recommendations.append("Evaluate ecosystem service losses")
        
        return recommendations
    
    def _generate_flood_recommendations(
        self,
        analysis: FloodAnalysis,
    ) -> list[str]:
        """Generate recommendations for flooding."""
        recommendations = []
        
        if analysis.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            recommendations.append("URGENT: Activate emergency response protocols")
            recommendations.append("Coordinate with disaster relief agencies")
            recommendations.append("Assess population displacement needs")
        
        recommendations.append("Monitor water levels with daily imagery")
        recommendations.append("Map evacuation routes and safe zones")
        recommendations.append("Assess infrastructure damage")
        recommendations.append("Track flood recession for recovery planning")
        
        return recommendations
    
    def _generate_wildfire_recommendations(
        self,
        analysis: WildfireAnalysis,
    ) -> list[str]:
        """Generate recommendations for wildfire."""
        recommendations = []
        
        if analysis.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            recommendations.append("URGENT: Alert fire suppression teams")
            recommendations.append("Establish containment perimeters")
            recommendations.append("Evacuate affected populations if needed")
        
        recommendations.append("Monitor fire progression with hourly updates")
        recommendations.append("Assess wind patterns for spread prediction")
        recommendations.append("Track smoke plumes for air quality alerts")
        recommendations.append("Plan post-fire recovery and reforestation")
        
        return recommendations
    
    def get_alerts_by_severity(
        self,
        severity: AlertSeverity,
    ) -> list[SatelliteAlert]:
        """Get alerts filtered by severity."""
        return [
            alert for alert in self.alerts.values()
            if alert.severity == severity
        ]
    
    def get_alerts_by_location(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50,
    ) -> list[SatelliteAlert]:
        """Get alerts near a location."""
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1, lon1, lat2, lon2):
            """Calculate distance between two points in km."""
            R = 6371  # Earth radius in km
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        
        nearby_alerts = []
        for alert in self.alerts.values():
            alert_lat = alert.location.get("lat", 0)
            alert_lon = alert.location.get("lon", 0)
            
            distance = haversine(lat, lon, alert_lat, alert_lon)
            if distance <= radius_km:
                nearby_alerts.append(alert)
        
        return nearby_alerts
    
    def get_narrative_links(self, alert_id: UUID) -> list[SatelliteNarrativeLink]:
        """Get narrative links for an alert."""
        return [
            link for link in self.narrative_links.values()
            if link.alert_id == alert_id
        ]
    
    def get_stats(self) -> dict[str, Any]:
        """Get integration statistics."""
        return {
            "total_alerts": len(self.alerts),
            "narrative_links": len(self.narrative_links),
            "alerts_by_type": {
                event_type.value: sum(
                    1 for a in self.alerts.values()
                    if a.event_type == event_type
                )
                for event_type in SatelliteEventType
            },
            "alerts_by_severity": {
                severity.value: sum(
                    1 for a in self.alerts.values()
                    if a.severity == severity
                )
                for severity in AlertSeverity
            },
        }


# Global instance
_integration_service: SatelliteIntegrationService | None = None


def get_satellite_integration() -> SatelliteIntegrationService:
    """Get the satellite integration service instance."""
    global _integration_service
    if _integration_service is None:
        _integration_service = SatelliteIntegrationService()
    return _integration_service
