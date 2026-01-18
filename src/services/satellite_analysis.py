"""Satellite Imagery Analysis System.

Multi-source satellite data analysis with temporal comparison capabilities.
Supports Sentinel-2, Google Earth Engine, MODIS, and other providers.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import logging

import numpy as np


logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class SatelliteProvider(str, Enum):
    """Satellite data providers."""
    SENTINEL_2 = "SENTINEL_2"  # ESA Copernicus
    SENTINEL_1 = "SENTINEL_1"  # SAR
    MODIS = "MODIS"  # NASA Terra/Aqua
    LANDSAT_8 = "LANDSAT_8"  # NASA/USGS
    LANDSAT_9 = "LANDSAT_9"
    GOOGLE_EARTH = "GOOGLE_EARTH"
    PLANET_LABS = "PLANET_LABS"


class AnalysisType(str, Enum):
    """Types of satellite analysis."""
    DEFORESTATION = "DEFORESTATION"
    URBAN_GROWTH = "URBAN_GROWTH"
    FLOODING = "FLOODING"
    AGRICULTURE = "AGRICULTURE"
    WILDFIRE = "WILDFIRE"
    DROUGHT = "DROUGHT"
    LAND_COVER_CHANGE = "LAND_COVER_CHANGE"
    VEGETATION_HEALTH = "VEGETATION_HEALTH"
    WATER_BODIES = "WATER_BODIES"
    INFRASTRUCTURE = "INFRASTRUCTURE"


class ChangeDetectionMethod(str, Enum):
    """Change detection algorithms."""
    NDVI_DIFFERENCE = "NDVI_DIFFERENCE"  # Vegetation
    NDWI_DIFFERENCE = "NDWI_DIFFERENCE"  # Water
    NDBI_DIFFERENCE = "NDBI_DIFFERENCE"  # Built-up areas
    NBR_DIFFERENCE = "NBR_DIFFERENCE"  # Burn ratio for fires
    IMAGE_DIFFERENCING = "IMAGE_DIFFERENCING"
    RATIO_CHANGE = "RATIO_CHANGE"
    CHANGE_VECTOR_ANALYSIS = "CHANGE_VECTOR_ANALYSIS"
    MACHINE_LEARNING = "MACHINE_LEARNING"


@dataclass
class BoundingBox:
    """Geographic bounding box."""
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    
    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "min_lon": self.min_lon,
            "min_lat": self.min_lat,
            "max_lon": self.max_lon,
            "max_lat": self.max_lat,
        }
    
    def to_geojson_polygon(self) -> list[list[float]]:
        """Convert to GeoJSON polygon coordinates."""
        return [
            [
                [self.min_lon, self.min_lat],
                [self.max_lon, self.min_lat],
                [self.max_lon, self.max_lat],
                [self.min_lon, self.max_lat],
                [self.min_lon, self.min_lat],
            ]
        ]


@dataclass
class SatelliteImage:
    """Satellite image metadata."""
    image_id: UUID
    provider: SatelliteProvider
    acquisition_date: datetime
    cloud_coverage: float  # 0-100%
    resolution_meters: float
    bbox: BoundingBox
    bands: list[str]  # Available spectral bands
    file_path: str | None = None
    thumbnail_url: str | None = None
    download_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpectralIndex:
    """Calculated spectral index."""
    index_name: str  # NDVI, NDWI, etc.
    value: float
    timestamp: datetime
    bbox: BoundingBox
    description: str = ""


@dataclass
class ChangeDetection:
    """Change detection result."""
    detection_id: UUID
    analysis_type: AnalysisType
    method: ChangeDetectionMethod
    before_date: datetime
    after_date: datetime
    bbox: BoundingBox
    change_percentage: float  # Percentage of area changed
    change_magnitude: float  # Average magnitude of change
    confidence: float  # 0-1
    changed_pixels: int
    total_pixels: int
    details: dict[str, Any] = field(default_factory=dict)
    visualization_url: str | None = None


@dataclass
class TimeSeriesAnalysis:
    """Time series analysis result."""
    analysis_id: UUID
    analysis_type: AnalysisType
    bbox: BoundingBox
    start_date: datetime
    end_date: datetime
    data_points: list[dict[str, Any]] = field(default_factory=list)
    trend: str = "STABLE"  # INCREASING, DECREASING, STABLE, FLUCTUATING
    trend_confidence: float = 0.0
    statistics: dict[str, Any] = field(default_factory=dict)


class SatelliteAnalysisService:
    """Service for satellite imagery analysis."""

    def __init__(self):
        """Initialize satellite analysis service."""
        self.images: dict[UUID, SatelliteImage] = {}
        self.change_detections: dict[UUID, ChangeDetection] = {}
        self.time_series: dict[UUID, TimeSeriesAnalysis] = {}
        
        # Areas of interest in Afghanistan
        self.predefined_aois = {
            "kabul": BoundingBox(69.11, 34.47, 69.26, 34.62),
            "kandahar": BoundingBox(65.65, 31.55, 65.83, 31.70),
            "herat": BoundingBox(62.14, 34.28, 62.26, 34.40),
            "mazar_sharif": BoundingBox(66.99, 36.66, 67.14, 36.76),
            "jalalabad": BoundingBox(70.41, 34.40, 70.52, 34.47),
            "helmand_valley": BoundingBox(64.0, 31.0, 65.0, 32.5),
            "panjshir_valley": BoundingBox(69.5, 35.2, 70.0, 35.6),
        }
        
        logger.info("Satellite analysis service initialized")
    
    def calculate_ndvi(
        self,
        red_band: np.ndarray,
        nir_band: np.ndarray,
    ) -> np.ndarray:
        """Calculate Normalized Difference Vegetation Index (NDVI).
        
        NDVI = (NIR - Red) / (NIR + Red)
        Range: -1 to 1 (higher = more vegetation)
        """
        # Avoid division by zero
        denominator = nir_band + red_band
        denominator = np.where(denominator == 0, 0.0001, denominator)
        
        ndvi = (nir_band - red_band) / denominator
        return np.clip(ndvi, -1, 1)
    
    def calculate_ndwi(
        self,
        green_band: np.ndarray,
        nir_band: np.ndarray,
    ) -> np.ndarray:
        """Calculate Normalized Difference Water Index (NDWI).
        
        NDWI = (Green - NIR) / (Green + NIR)
        Range: -1 to 1 (higher = more water)
        """
        denominator = green_band + nir_band
        denominator = np.where(denominator == 0, 0.0001, denominator)
        
        ndwi = (green_band - nir_band) / denominator
        return np.clip(ndwi, -1, 1)
    
    def calculate_ndbi(
        self,
        swir_band: np.ndarray,
        nir_band: np.ndarray,
    ) -> np.ndarray:
        """Calculate Normalized Difference Built-up Index (NDBI).
        
        NDBI = (SWIR - NIR) / (SWIR + NIR)
        Range: -1 to 1 (higher = more built-up area)
        """
        denominator = swir_band + nir_band
        denominator = np.where(denominator == 0, 0.0001, denominator)
        
        ndbi = (swir_band - nir_band) / denominator
        return np.clip(ndbi, -1, 1)
    
    def calculate_nbr(
        self,
        nir_band: np.ndarray,
        swir_band: np.ndarray,
    ) -> np.ndarray:
        """Calculate Normalized Burn Ratio (NBR).
        
        NBR = (NIR - SWIR) / (NIR + SWIR)
        Range: -1 to 1 (used for fire/burn detection)
        """
        denominator = nir_band + swir_band
        denominator = np.where(denominator == 0, 0.0001, denominator)
        
        nbr = (nir_band - swir_band) / denominator
        return np.clip(nbr, -1, 1)
    
    def detect_deforestation(
        self,
        before_ndvi: np.ndarray,
        after_ndvi: np.ndarray,
        bbox: BoundingBox,
        before_date: datetime,
        after_date: datetime,
        threshold: float = 0.2,
    ) -> ChangeDetection:
        """Detect deforestation by comparing NDVI values.
        
        Args:
            before_ndvi: NDVI array from earlier date
            after_ndvi: NDVI array from later date
            bbox: Geographic bounding box
            before_date: Date of before image
            after_date: Date of after image
            threshold: NDVI decrease threshold for detection
        """
        # Calculate NDVI difference
        ndvi_diff = before_ndvi - after_ndvi
        
        # Identify deforested areas (significant NDVI decrease)
        deforested = ndvi_diff > threshold
        
        changed_pixels = np.sum(deforested)
        total_pixels = deforested.size
        change_percentage = (changed_pixels / total_pixels) * 100
        
        # Calculate average magnitude of change
        change_magnitude = float(np.mean(ndvi_diff[deforested])) if changed_pixels > 0 else 0.0
        
        # Calculate confidence based on magnitude
        confidence = min(1.0, change_magnitude / 0.5)
        
        detection = ChangeDetection(
            detection_id=uuid4(),
            analysis_type=AnalysisType.DEFORESTATION,
            method=ChangeDetectionMethod.NDVI_DIFFERENCE,
            before_date=before_date,
            after_date=after_date,
            bbox=bbox,
            change_percentage=change_percentage,
            change_magnitude=change_magnitude,
            confidence=confidence,
            changed_pixels=int(changed_pixels),
            total_pixels=int(total_pixels),
            details={
                "threshold": threshold,
                "avg_ndvi_before": float(np.mean(before_ndvi)),
                "avg_ndvi_after": float(np.mean(after_ndvi)),
                "max_change": float(np.max(ndvi_diff)),
            },
        )
        
        self.change_detections[detection.detection_id] = detection
        return detection
    
    def detect_urban_growth(
        self,
        before_ndbi: np.ndarray,
        after_ndbi: np.ndarray,
        bbox: BoundingBox,
        before_date: datetime,
        after_date: datetime,
        threshold: float = 0.15,
    ) -> ChangeDetection:
        """Detect urban growth using NDBI."""
        ndbi_diff = after_ndbi - before_ndbi
        
        # Urban growth = increase in built-up index
        urban_growth = ndbi_diff > threshold
        
        changed_pixels = np.sum(urban_growth)
        total_pixels = urban_growth.size
        change_percentage = (changed_pixels / total_pixels) * 100
        change_magnitude = float(np.mean(ndbi_diff[urban_growth])) if changed_pixels > 0 else 0.0
        
        confidence = min(1.0, change_magnitude / 0.4)
        
        detection = ChangeDetection(
            detection_id=uuid4(),
            analysis_type=AnalysisType.URBAN_GROWTH,
            method=ChangeDetectionMethod.NDBI_DIFFERENCE,
            before_date=before_date,
            after_date=after_date,
            bbox=bbox,
            change_percentage=change_percentage,
            change_magnitude=change_magnitude,
            confidence=confidence,
            changed_pixels=int(changed_pixels),
            total_pixels=int(total_pixels),
            details={
                "threshold": threshold,
                "avg_ndbi_before": float(np.mean(before_ndbi)),
                "avg_ndbi_after": float(np.mean(after_ndbi)),
            },
        )
        
        self.change_detections[detection.detection_id] = detection
        return detection
    
    def detect_flooding(
        self,
        before_ndwi: np.ndarray,
        after_ndwi: np.ndarray,
        bbox: BoundingBox,
        before_date: datetime,
        after_date: datetime,
        threshold: float = 0.2,
    ) -> ChangeDetection:
        """Detect flooding using NDWI."""
        ndwi_diff = after_ndwi - before_ndwi
        
        # Flooding = increase in water index
        flooded = ndwi_diff > threshold
        
        changed_pixels = np.sum(flooded)
        total_pixels = flooded.size
        change_percentage = (changed_pixels / total_pixels) * 100
        change_magnitude = float(np.mean(ndwi_diff[flooded])) if changed_pixels > 0 else 0.0
        
        confidence = min(1.0, change_magnitude / 0.5)
        
        detection = ChangeDetection(
            detection_id=uuid4(),
            analysis_type=AnalysisType.FLOODING,
            method=ChangeDetectionMethod.NDWI_DIFFERENCE,
            before_date=before_date,
            after_date=after_date,
            bbox=bbox,
            change_percentage=change_percentage,
            change_magnitude=change_magnitude,
            confidence=confidence,
            changed_pixels=int(changed_pixels),
            total_pixels=int(total_pixels),
            details={
                "threshold": threshold,
                "avg_ndwi_before": float(np.mean(before_ndwi)),
                "avg_ndwi_after": float(np.mean(after_ndwi)),
            },
        )
        
        self.change_detections[detection.detection_id] = detection
        return detection
    
    def get_stats(self) -> dict[str, Any]:
        """Get analysis statistics."""
        return {
            "total_images": len(self.images),
            "total_change_detections": len(self.change_detections),
            "total_time_series": len(self.time_series),
            "analysis_types": {
                atype.value: sum(
                    1 for d in self.change_detections.values()
                    if d.analysis_type == atype
                )
                for atype in AnalysisType
            },
        }


# Global instance
_satellite_service: SatelliteAnalysisService | None = None


def get_satellite_service() -> SatelliteAnalysisService:
    """Get the satellite analysis service instance."""
    global _satellite_service
    if _satellite_service is None:
        _satellite_service = SatelliteAnalysisService()
    return _satellite_service
