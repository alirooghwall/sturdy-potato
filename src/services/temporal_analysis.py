"""Multi-Temporal Satellite Image Analysis Engine.

Comprehensive system for analyzing satellite imagery across time periods
to detect changes in deforestation, urban growth, flooding, agriculture,
wildfires, and long-term environmental trends.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import numpy as np

from .satellite_analysis import (
    AnalysisType,
    BoundingBox,
    ChangeDetection,
    ChangeDetectionMethod,
    SatelliteImage,
    TimeSeriesAnalysis,
    get_satellite_service,
)


logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class TrendDirection(str, Enum):
    """Trend direction for time series."""
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    FLUCTUATING = "FLUCTUATING"
    SEASONAL = "SEASONAL"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class DeforestationAnalysis:
    """Deforestation analysis result."""
    analysis_id: UUID
    bbox: BoundingBox
    before_date: datetime
    after_date: datetime
    forest_loss_hectares: float
    forest_loss_percentage: float
    affected_areas: list[dict[str, Any]] = field(default_factory=list)
    severity: AlertSeverity = AlertSeverity.INFO
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class UrbanGrowthAnalysis:
    """Urban growth analysis result."""
    analysis_id: UUID
    bbox: BoundingBox
    before_date: datetime
    after_date: datetime
    urban_expansion_hectares: float
    urban_expansion_percentage: float
    growth_rate_annual: float
    new_urban_areas: list[dict[str, Any]] = field(default_factory=list)
    infrastructure_detected: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FloodAnalysis:
    """Flood detection and analysis result."""
    analysis_id: UUID
    bbox: BoundingBox
    event_date: datetime
    baseline_date: datetime
    flooded_area_hectares: float
    flooded_area_percentage: float
    water_level_change_meters: float | None
    affected_locations: list[dict[str, Any]] = field(default_factory=list)
    severity: AlertSeverity = AlertSeverity.INFO
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgricultureAnalysis:
    """Agriculture monitoring analysis result."""
    analysis_id: UUID
    bbox: BoundingBox
    analysis_date: datetime
    crop_health_index: float  # 0-1
    vegetation_vigor: float  # NDVI average
    crop_area_hectares: float
    health_status: str  # HEALTHY, STRESSED, POOR, CRITICAL
    irrigation_detected: bool
    crop_stage: str | None
    recommendations: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class WildfireAnalysis:
    """Wildfire detection and tracking result."""
    analysis_id: UUID
    bbox: BoundingBox
    detection_date: datetime
    burned_area_hectares: float
    fire_intensity: str  # LOW, MEDIUM, HIGH, EXTREME
    smoke_detected: bool
    wind_direction: str | None
    severity: AlertSeverity = AlertSeverity.HIGH
    confidence: float = 0.0
    active_fire_locations: list[dict[str, Any]] = field(default_factory=list)
    recovery_analysis: dict[str, Any] = field(default_factory=dict)


@dataclass
class LongTermTrend:
    """Long-term environmental trend analysis."""
    trend_id: UUID
    analysis_type: AnalysisType
    bbox: BoundingBox
    start_date: datetime
    end_date: datetime
    trend_direction: TrendDirection
    rate_of_change: float  # Units depend on analysis type
    significance: float  # Statistical significance 0-1
    data_points: list[dict[str, Any]] = field(default_factory=list)
    predictions: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


class TemporalAnalysisEngine:
    """Multi-temporal satellite image analysis engine."""

    def __init__(self):
        """Initialize temporal analysis engine."""
        self.satellite_service = get_satellite_service()
        
        self.deforestation_analyses: dict[UUID, DeforestationAnalysis] = {}
        self.urban_growth_analyses: dict[UUID, UrbanGrowthAnalysis] = {}
        self.flood_analyses: dict[UUID, FloodAnalysis] = {}
        self.agriculture_analyses: dict[UUID, AgricultureAnalysis] = {}
        self.wildfire_analyses: dict[UUID, WildfireAnalysis] = {}
        self.long_term_trends: dict[UUID, LongTermTrend] = {}
        
        # Analysis thresholds
        self.deforestation_threshold = 0.2  # NDVI decrease
        self.urban_growth_threshold = 0.15  # NDBI increase
        self.flood_threshold = 0.25  # NDWI increase
        self.fire_threshold = 0.3  # NBR decrease
        
        # Resolution for area calculations (meters per pixel)
        self.pixel_resolution = 10  # Sentinel-2 default
        
        logger.info("Temporal analysis engine initialized")
    
    def analyze_deforestation(
        self,
        bbox: BoundingBox,
        before_date: datetime,
        after_date: datetime,
        before_ndvi: np.ndarray | None = None,
        after_ndvi: np.ndarray | None = None,
    ) -> DeforestationAnalysis:
        """Comprehensive deforestation analysis.
        
        Args:
            bbox: Area of interest
            before_date: Earlier date for comparison
            after_date: Later date for comparison
            before_ndvi: Pre-calculated NDVI (optional)
            after_ndvi: Pre-calculated NDVI (optional)
        """
        analysis_id = uuid4()
        
        # If NDVI not provided, calculate from available imagery
        if before_ndvi is None or after_ndvi is None:
            # This would fetch and process actual imagery
            # For now, create mock data for demonstration
            logger.warning("Using mock NDVI data - implement actual image processing")
            before_ndvi = np.random.uniform(0.4, 0.8, (100, 100))
            after_ndvi = before_ndvi - np.random.uniform(0, 0.3, (100, 100))
            after_ndvi = np.clip(after_ndvi, 0, 1)
        
        # Detect forest loss
        ndvi_diff = before_ndvi - after_ndvi
        forest_loss_mask = ndvi_diff > self.deforestation_threshold
        
        # Calculate areas
        pixels_lost = np.sum(forest_loss_mask)
        total_pixels = forest_loss_mask.size
        
        # Convert pixels to hectares (1 hectare = 10,000 m²)
        pixel_area_m2 = self.pixel_resolution ** 2
        forest_loss_hectares = (pixels_lost * pixel_area_m2) / 10000
        forest_loss_percentage = (pixels_lost / total_pixels) * 100
        
        # Identify affected areas (cluster detection)
        affected_areas = self._identify_clusters(forest_loss_mask, bbox)
        
        # Determine severity
        if forest_loss_percentage > 20:
            severity = AlertSeverity.CRITICAL
        elif forest_loss_percentage > 10:
            severity = AlertSeverity.HIGH
        elif forest_loss_percentage > 5:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW
        
        # Calculate confidence
        avg_change = float(np.mean(ndvi_diff[forest_loss_mask])) if pixels_lost > 0 else 0
        confidence = min(1.0, avg_change / 0.5)
        
        analysis = DeforestationAnalysis(
            analysis_id=analysis_id,
            bbox=bbox,
            before_date=before_date,
            after_date=after_date,
            forest_loss_hectares=forest_loss_hectares,
            forest_loss_percentage=forest_loss_percentage,
            affected_areas=affected_areas,
            severity=severity,
            confidence=confidence,
            details={
                "avg_ndvi_before": float(np.mean(before_ndvi)),
                "avg_ndvi_after": float(np.mean(after_ndvi)),
                "max_change": float(np.max(ndvi_diff)),
                "pixels_affected": int(pixels_lost),
                "analysis_resolution_m": self.pixel_resolution,
            },
        )
        
        self.deforestation_analyses[analysis_id] = analysis
        logger.info(f"Deforestation analysis complete: {forest_loss_percentage:.2f}% loss")
        
        return analysis
    
    def analyze_urban_growth(
        self,
        bbox: BoundingBox,
        before_date: datetime,
        after_date: datetime,
        before_ndbi: np.ndarray | None = None,
        after_ndbi: np.ndarray | None = None,
    ) -> UrbanGrowthAnalysis:
        """Comprehensive urban growth analysis."""
        analysis_id = uuid4()
        
        # Mock data if not provided
        if before_ndbi is None or after_ndbi is None:
            logger.warning("Using mock NDBI data - implement actual image processing")
            before_ndbi = np.random.uniform(-0.2, 0.2, (100, 100))
            after_ndbi = before_ndbi + np.random.uniform(0, 0.25, (100, 100))
            after_ndbi = np.clip(after_ndbi, -1, 1)
        
        # Detect urban expansion
        ndbi_diff = after_ndbi - before_ndbi
        urban_growth_mask = ndbi_diff > self.urban_growth_threshold
        
        # Calculate areas
        pixels_expanded = np.sum(urban_growth_mask)
        total_pixels = urban_growth_mask.size
        
        pixel_area_m2 = self.pixel_resolution ** 2
        urban_expansion_hectares = (pixels_expanded * pixel_area_m2) / 10000
        urban_expansion_percentage = (pixels_expanded / total_pixels) * 100
        
        # Calculate annual growth rate
        days_diff = (after_date - before_date).days
        years_diff = days_diff / 365.25
        growth_rate_annual = urban_expansion_percentage / years_diff if years_diff > 0 else 0
        
        # Identify new urban areas
        new_urban_areas = self._identify_clusters(urban_growth_mask, bbox)
        
        # Detect infrastructure types (simplified)
        infrastructure_detected = []
        if urban_expansion_hectares > 10:
            infrastructure_detected.append("Major development")
        if urban_expansion_percentage > 5:
            infrastructure_detected.append("Urban sprawl")
        
        analysis = UrbanGrowthAnalysis(
            analysis_id=analysis_id,
            bbox=bbox,
            before_date=before_date,
            after_date=after_date,
            urban_expansion_hectares=urban_expansion_hectares,
            urban_expansion_percentage=urban_expansion_percentage,
            growth_rate_annual=growth_rate_annual,
            new_urban_areas=new_urban_areas,
            infrastructure_detected=infrastructure_detected,
            details={
                "avg_ndbi_before": float(np.mean(before_ndbi)),
                "avg_ndbi_after": float(np.mean(after_ndbi)),
                "pixels_expanded": int(pixels_expanded),
                "days_analyzed": days_diff,
            },
        )
        
        self.urban_growth_analyses[analysis_id] = analysis
        logger.info(f"Urban growth analysis complete: {urban_expansion_percentage:.2f}% expansion")
        
        return analysis
    
    def analyze_flooding(
        self,
        bbox: BoundingBox,
        event_date: datetime,
        baseline_date: datetime,
        event_ndwi: np.ndarray | None = None,
        baseline_ndwi: np.ndarray | None = None,
    ) -> FloodAnalysis:
        """Comprehensive flood detection and analysis."""
        analysis_id = uuid4()
        
        # Mock data if not provided
        if event_ndwi is None or baseline_ndwi is None:
            logger.warning("Using mock NDWI data - implement actual image processing")
            baseline_ndwi = np.random.uniform(-0.3, 0.1, (100, 100))
            event_ndwi = baseline_ndwi + np.random.uniform(0, 0.4, (100, 100))
            event_ndwi = np.clip(event_ndwi, -1, 1)
        
        # Detect flooded areas
        ndwi_diff = event_ndwi - baseline_ndwi
        flood_mask = ndwi_diff > self.flood_threshold
        
        # Calculate areas
        pixels_flooded = np.sum(flood_mask)
        total_pixels = flood_mask.size
        
        pixel_area_m2 = self.pixel_resolution ** 2
        flooded_area_hectares = (pixels_flooded * pixel_area_m2) / 10000
        flooded_area_percentage = (pixels_flooded / total_pixels) * 100
        
        # Identify affected locations
        affected_locations = self._identify_clusters(flood_mask, bbox)
        
        # Determine severity
        if flooded_area_percentage > 30:
            severity = AlertSeverity.CRITICAL
        elif flooded_area_percentage > 15:
            severity = AlertSeverity.HIGH
        elif flooded_area_percentage > 5:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW
        
        # Calculate confidence
        avg_change = float(np.mean(ndwi_diff[flood_mask])) if pixels_flooded > 0 else 0
        confidence = min(1.0, avg_change / 0.5)
        
        analysis = FloodAnalysis(
            analysis_id=analysis_id,
            bbox=bbox,
            event_date=event_date,
            baseline_date=baseline_date,
            flooded_area_hectares=flooded_area_hectares,
            flooded_area_percentage=flooded_area_percentage,
            water_level_change_meters=None,  # Would require elevation data
            affected_locations=affected_locations,
            severity=severity,
            confidence=confidence,
            details={
                "avg_ndwi_baseline": float(np.mean(baseline_ndwi)),
                "avg_ndwi_event": float(np.mean(event_ndwi)),
                "max_water_increase": float(np.max(ndwi_diff)),
                "pixels_flooded": int(pixels_flooded),
            },
        )
        
        self.flood_analyses[analysis_id] = analysis
        logger.info(f"Flood analysis complete: {flooded_area_percentage:.2f}% flooded")
        
        return analysis
    
    def analyze_agriculture(
        self,
        bbox: BoundingBox,
        analysis_date: datetime,
        ndvi: np.ndarray | None = None,
        ndwi: np.ndarray | None = None,
    ) -> AgricultureAnalysis:
        """Comprehensive agriculture monitoring."""
        analysis_id = uuid4()
        
        # Mock data if not provided
        if ndvi is None:
            logger.warning("Using mock NDVI data for agriculture analysis")
            ndvi = np.random.uniform(0.3, 0.8, (100, 100))
        
        if ndwi is None:
            ndwi = np.random.uniform(-0.2, 0.2, (100, 100))
        
        # Calculate vegetation vigor
        vegetation_vigor = float(np.mean(ndvi))
        
        # Identify crop areas (NDVI > 0.3 typically indicates vegetation)
        crop_mask = ndvi > 0.3
        crop_pixels = np.sum(crop_mask)
        
        pixel_area_m2 = self.pixel_resolution ** 2
        crop_area_hectares = (crop_pixels * pixel_area_m2) / 10000
        
        # Calculate crop health index (0-1 scale)
        crop_health_index = float(np.mean(ndvi[crop_mask])) if crop_pixels > 0 else 0
        
        # Determine health status
        if crop_health_index > 0.7:
            health_status = "HEALTHY"
        elif crop_health_index > 0.5:
            health_status = "FAIR"
        elif crop_health_index > 0.3:
            health_status = "STRESSED"
        else:
            health_status = "POOR"
        
        # Detect irrigation (high NDWI in crop areas)
        if ndwi is not None:
            avg_ndwi_crops = float(np.mean(ndwi[crop_mask])) if crop_pixels > 0 else 0
            irrigation_detected = avg_ndwi_crops > 0.1
        else:
            irrigation_detected = False
        
        # Generate recommendations
        recommendations = []
        if health_status in ["STRESSED", "POOR"]:
            recommendations.append("Investigate potential drought stress")
            recommendations.append("Consider irrigation if available")
        if not irrigation_detected and health_status != "HEALTHY":
            recommendations.append("Low water availability detected")
        if crop_health_index > 0.6:
            recommendations.append("Crops showing good vigor")
        
        analysis = AgricultureAnalysis(
            analysis_id=analysis_id,
            bbox=bbox,
            analysis_date=analysis_date,
            crop_health_index=crop_health_index,
            vegetation_vigor=vegetation_vigor,
            crop_area_hectares=crop_area_hectares,
            health_status=health_status,
            irrigation_detected=irrigation_detected,
            crop_stage=None,  # Would require time series analysis
            recommendations=recommendations,
            details={
                "avg_ndvi": vegetation_vigor,
                "avg_ndwi": float(np.mean(ndwi)) if ndwi is not None else None,
                "crop_pixels": int(crop_pixels),
            },
        )
        
        self.agriculture_analyses[analysis_id] = analysis
        logger.info(f"Agriculture analysis complete: {health_status} ({crop_health_index:.2f})")
        
        return analysis
    
    def analyze_wildfire(
        self,
        bbox: BoundingBox,
        detection_date: datetime,
        pre_fire_date: datetime,
        pre_fire_nbr: np.ndarray | None = None,
        post_fire_nbr: np.ndarray | None = None,
    ) -> WildfireAnalysis:
        """Comprehensive wildfire detection and analysis."""
        analysis_id = uuid4()
        
        # Mock data if not provided
        if pre_fire_nbr is None or post_fire_nbr is None:
            logger.warning("Using mock NBR data for wildfire analysis")
            pre_fire_nbr = np.random.uniform(0.3, 0.6, (100, 100))
            post_fire_nbr = pre_fire_nbr - np.random.uniform(0, 0.5, (100, 100))
            post_fire_nbr = np.clip(post_fire_nbr, -1, 1)
        
        # Calculate dNBR (difference NBR)
        dnbr = pre_fire_nbr - post_fire_nbr
        
        # Detect burned areas
        burn_mask = dnbr > self.fire_threshold
        
        # Calculate areas
        pixels_burned = np.sum(burn_mask)
        total_pixels = burn_mask.size
        
        pixel_area_m2 = self.pixel_resolution ** 2
        burned_area_hectares = (pixels_burned * pixel_area_m2) / 10000
        
        # Determine fire intensity from dNBR
        avg_dnbr = float(np.mean(dnbr[burn_mask])) if pixels_burned > 0 else 0
        
        if avg_dnbr > 0.66:
            fire_intensity = "EXTREME"
            severity = AlertSeverity.CRITICAL
        elif avg_dnbr > 0.44:
            fire_intensity = "HIGH"
            severity = AlertSeverity.HIGH
        elif avg_dnbr > 0.27:
            fire_intensity = "MEDIUM"
            severity = AlertSeverity.MEDIUM
        else:
            fire_intensity = "LOW"
            severity = AlertSeverity.LOW
        
        # Identify active fire locations
        active_fire_locations = self._identify_clusters(burn_mask, bbox)
        
        # Confidence based on intensity
        confidence = min(1.0, avg_dnbr / 0.7)
        
        analysis = WildfireAnalysis(
            analysis_id=analysis_id,
            bbox=bbox,
            detection_date=detection_date,
            burned_area_hectares=burned_area_hectares,
            fire_intensity=fire_intensity,
            active_fire_locations=active_fire_locations,
            smoke_detected=False,  # Would require additional bands
            wind_direction=None,  # Would require weather data
            severity=severity,
            confidence=confidence,
            recovery_analysis={},  # Would require long-term monitoring
        )
        
        self.wildfire_analyses[analysis_id] = analysis
        logger.info(f"Wildfire analysis complete: {burned_area_hectares:.2f} ha, {fire_intensity} intensity")
        
        return analysis
    
    def analyze_long_term_trend(
        self,
        analysis_type: AnalysisType,
        bbox: BoundingBox,
        start_date: datetime,
        end_date: datetime,
        time_series_data: list[dict[str, Any]],
    ) -> LongTermTrend:
        """Analyze long-term environmental trends."""
        trend_id = uuid4()
        
        if not time_series_data or len(time_series_data) < 3:
            logger.warning("Insufficient data for trend analysis")
            return LongTermTrend(
                trend_id=trend_id,
                analysis_type=analysis_type,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                trend_direction=TrendDirection.STABLE,
                rate_of_change=0.0,
                significance=0.0,
                data_points=time_series_data,
            )
        
        # Extract values
        values = [point.get("value", 0) for point in time_series_data]
        values_array = np.array(values)
        
        # Calculate linear trend
        x = np.arange(len(values))
        z = np.polyfit(x, values_array, 1)
        slope = z[0]
        
        # Determine trend direction
        if abs(slope) < 0.001:
            trend_direction = TrendDirection.STABLE
        elif slope > 0.005:
            trend_direction = TrendDirection.INCREASING
        elif slope < -0.005:
            trend_direction = TrendDirection.DECREASING
        else:
            # Check for fluctuations
            std_dev = np.std(values_array)
            mean_val = np.mean(values_array)
            cv = std_dev / mean_val if mean_val != 0 else 0
            
            if cv > 0.2:
                trend_direction = TrendDirection.FLUCTUATING
            else:
                trend_direction = TrendDirection.STABLE
        
        # Calculate rate of change (per year)
        days_total = (end_date - start_date).days
        years = days_total / 365.25
        rate_of_change = slope * (len(values) / years) if years > 0 else 0
        
        # Calculate significance (R² value)
        p = np.poly1d(z)
        y_pred = p(x)
        ss_res = np.sum((values_array - y_pred) ** 2)
        ss_tot = np.sum((values_array - np.mean(values_array)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        significance = max(0, r_squared)
        
        # Make predictions
        future_points = 4  # Predict 4 time periods ahead
        future_x = np.arange(len(values), len(values) + future_points)
        future_values = p(future_x)
        
        predictions = {
            "method": "linear_regression",
            "predicted_values": future_values.tolist(),
            "confidence": float(significance),
        }
        
        trend = LongTermTrend(
            trend_id=trend_id,
            analysis_type=analysis_type,
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            trend_direction=trend_direction,
            rate_of_change=float(rate_of_change),
            significance=float(significance),
            data_points=time_series_data,
            predictions=predictions,
            details={
                "slope": float(slope),
                "r_squared": float(r_squared),
                "mean_value": float(np.mean(values_array)),
                "std_dev": float(np.std(values_array)),
                "num_observations": len(values),
            },
        )
        
        self.long_term_trends[trend_id] = trend
        logger.info(f"Long-term trend analysis complete: {trend_direction.value}")
        
        return trend
    
    def _identify_clusters(
        self,
        mask: np.ndarray,
        bbox: BoundingBox,
        min_size: int = 10,
    ) -> list[dict[str, Any]]:
        """Identify spatial clusters in a binary mask."""
        # Simplified cluster detection
        # In production, would use proper connected component analysis
        
        clusters = []
        
        # Find all positive pixels
        positive_pixels = np.argwhere(mask)
        
        if len(positive_pixels) > min_size:
            # Calculate centroid
            centroid_y, centroid_x = np.mean(positive_pixels, axis=0)
            
            # Convert pixel coordinates to lat/lon (simplified)
            lat = bbox.min_lat + (centroid_y / mask.shape[0]) * (bbox.max_lat - bbox.min_lat)
            lon = bbox.min_lon + (centroid_x / mask.shape[1]) * (bbox.max_lon - bbox.min_lon)
            
            pixel_area_m2 = self.pixel_resolution ** 2
            cluster_area_hectares = (len(positive_pixels) * pixel_area_m2) / 10000
            
            clusters.append({
                "centroid": {"lat": float(lat), "lon": float(lon)},
                "area_hectares": float(cluster_area_hectares),
                "pixel_count": len(positive_pixels),
            })
        
        return clusters
    
    def get_stats(self) -> dict[str, Any]:
        """Get analysis statistics."""
        return {
            "total_analyses": sum([
                len(self.deforestation_analyses),
                len(self.urban_growth_analyses),
                len(self.flood_analyses),
                len(self.agriculture_analyses),
                len(self.wildfire_analyses),
                len(self.long_term_trends),
            ]),
            "deforestation_analyses": len(self.deforestation_analyses),
            "urban_growth_analyses": len(self.urban_growth_analyses),
            "flood_analyses": len(self.flood_analyses),
            "agriculture_analyses": len(self.agriculture_analyses),
            "wildfire_analyses": len(self.wildfire_analyses),
            "long_term_trends": len(self.long_term_trends),
        }


# Global instance
_temporal_engine: TemporalAnalysisEngine | None = None


def get_temporal_engine() -> TemporalAnalysisEngine:
    """Get the temporal analysis engine instance."""
    global _temporal_engine
    if _temporal_engine is None:
        _temporal_engine = TemporalAnalysisEngine()
    return _temporal_engine
