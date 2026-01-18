"""Satellite imagery analysis API endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.services.satellite_analysis import (
    AnalysisType,
    BoundingBox,
    SatelliteProvider,
    get_satellite_service,
)
from src.services.temporal_analysis import (
    AlertSeverity,
    TrendDirection,
    get_temporal_engine,
)
from src.services.satellite_integration import (
    SatelliteEventType,
    get_satellite_integration,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class BoundingBoxRequest(BaseModel):
    """Bounding box request."""
    min_lon: float = Field(ge=-180, le=180)
    min_lat: float = Field(ge=-90, le=90)
    max_lon: float = Field(ge=-180, le=180)
    max_lat: float = Field(ge=-90, le=90)


class DeforestationAnalysisRequest(BaseModel):
    """Request for deforestation analysis."""
    bbox: BoundingBoxRequest
    before_date: str  # ISO format
    after_date: str  # ISO format


class UrbanGrowthAnalysisRequest(BaseModel):
    """Request for urban growth analysis."""
    bbox: BoundingBoxRequest
    before_date: str
    after_date: str


class FloodAnalysisRequest(BaseModel):
    """Request for flood analysis."""
    bbox: BoundingBoxRequest
    event_date: str
    baseline_date: str


class AgricultureAnalysisRequest(BaseModel):
    """Request for agriculture monitoring."""
    bbox: BoundingBoxRequest
    analysis_date: str


class WildfireAnalysisRequest(BaseModel):
    """Request for wildfire analysis."""
    bbox: BoundingBoxRequest
    detection_date: str
    pre_fire_date: str


class LongTermTrendRequest(BaseModel):
    """Request for long-term trend analysis."""
    analysis_type: AnalysisType
    bbox: BoundingBoxRequest
    start_date: str
    end_date: str


# API Endpoints

@router.get("/providers")
async def get_satellite_providers(
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
) -> dict[str, Any]:
    """Get available satellite data providers."""
    return {
        "providers": [
            {
                "name": provider.value,
                "description": _get_provider_description(provider),
                "resolution_meters": _get_provider_resolution(provider),
            }
            for provider in SatelliteProvider
        ]
    }


@router.get("/images")
async def list_satellite_images(
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
    provider: SatelliteProvider | None = Query(default=None),
    min_date: str | None = Query(default=None),
    max_date: str | None = Query(default=None),
    max_cloud_cover: float = Query(default=30, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """List available satellite images."""
    service = get_satellite_service()
    
    images = list(service.images.values())
    
    # Filter by provider
    if provider:
        images = [img for img in images if img.provider == provider]
    
    # Filter by date range
    if min_date:
        min_dt = datetime.fromisoformat(min_date.replace('Z', '+00:00'))
        images = [img for img in images if img.acquisition_date >= min_dt]
    
    if max_date:
        max_dt = datetime.fromisoformat(max_date.replace('Z', '+00:00'))
        images = [img for img in images if img.acquisition_date <= max_dt]
    
    # Filter by cloud coverage
    images = [img for img in images if img.cloud_coverage <= max_cloud_cover]
    
    # Sort by date (most recent first)
    images.sort(key=lambda x: x.acquisition_date, reverse=True)
    
    return {
        "total": len(images),
        "images": [
            {
                "image_id": str(img.image_id),
                "provider": img.provider.value,
                "acquisition_date": img.acquisition_date.isoformat(),
                "cloud_coverage": img.cloud_coverage,
                "resolution_meters": img.resolution_meters,
                "bbox": img.bbox.to_dict(),
                "bands": img.bands,
                "thumbnail_url": img.thumbnail_url,
            }
            for img in images[:limit]
        ],
    }


@router.get("/images/{image_id}")
async def get_satellite_image(
    image_id: UUID,
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
) -> dict[str, Any]:
    """Get satellite image details."""
    service = get_satellite_service()
    
    image = service.images.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found",
        )
    
    return {
        "image_id": str(image.image_id),
        "provider": image.provider.value,
        "acquisition_date": image.acquisition_date.isoformat(),
        "cloud_coverage": image.cloud_coverage,
        "resolution_meters": image.resolution_meters,
        "bbox": image.bbox.to_dict(),
        "bands": image.bands,
        "file_path": image.file_path,
        "thumbnail_url": image.thumbnail_url,
        "download_url": image.download_url,
        "metadata": image.metadata,
    }


@router.post("/analysis/deforestation")
async def analyze_deforestation(
    request: DeforestationAnalysisRequest,
    user: Annotated[dict, Depends(require_permission("satellite:analyze"))],
) -> dict[str, Any]:
    """Analyze deforestation between two dates."""
    engine = get_temporal_engine()
    
    # Parse dates
    before_date = datetime.fromisoformat(request.before_date.replace('Z', '+00:00'))
    after_date = datetime.fromisoformat(request.after_date.replace('Z', '+00:00'))
    
    # Create bounding box
    bbox = BoundingBox(
        min_lon=request.bbox.min_lon,
        min_lat=request.bbox.min_lat,
        max_lon=request.bbox.max_lon,
        max_lat=request.bbox.max_lat,
    )
    
    # Perform analysis
    analysis = engine.analyze_deforestation(bbox, before_date, after_date)
    
    return {
        "analysis_id": str(analysis.analysis_id),
        "analysis_type": "DEFORESTATION",
        "bbox": bbox.to_dict(),
        "before_date": before_date.isoformat(),
        "after_date": after_date.isoformat(),
        "forest_loss_hectares": analysis.forest_loss_hectares,
        "forest_loss_percentage": analysis.forest_loss_percentage,
        "affected_areas": analysis.affected_areas,
        "severity": analysis.severity.value,
        "confidence": analysis.confidence,
        "details": analysis.details,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/analysis/urban-growth")
async def analyze_urban_growth(
    request: UrbanGrowthAnalysisRequest,
    user: Annotated[dict, Depends(require_permission("satellite:analyze"))],
) -> dict[str, Any]:
    """Analyze urban growth and expansion."""
    engine = get_temporal_engine()
    
    before_date = datetime.fromisoformat(request.before_date.replace('Z', '+00:00'))
    after_date = datetime.fromisoformat(request.after_date.replace('Z', '+00:00'))
    
    bbox = BoundingBox(
        min_lon=request.bbox.min_lon,
        min_lat=request.bbox.min_lat,
        max_lon=request.bbox.max_lon,
        max_lat=request.bbox.max_lat,
    )
    
    analysis = engine.analyze_urban_growth(bbox, before_date, after_date)
    
    return {
        "analysis_id": str(analysis.analysis_id),
        "analysis_type": "URBAN_GROWTH",
        "bbox": bbox.to_dict(),
        "before_date": before_date.isoformat(),
        "after_date": after_date.isoformat(),
        "urban_expansion_hectares": analysis.urban_expansion_hectares,
        "urban_expansion_percentage": analysis.urban_expansion_percentage,
        "growth_rate_annual": analysis.growth_rate_annual,
        "new_urban_areas": analysis.new_urban_areas,
        "infrastructure_detected": analysis.infrastructure_detected,
        "details": analysis.details,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/analysis/flooding")
async def analyze_flooding(
    request: FloodAnalysisRequest,
    user: Annotated[dict, Depends(require_permission("satellite:analyze"))],
) -> dict[str, Any]:
    """Analyze flood extent and impacts."""
    engine = get_temporal_engine()
    
    event_date = datetime.fromisoformat(request.event_date.replace('Z', '+00:00'))
    baseline_date = datetime.fromisoformat(request.baseline_date.replace('Z', '+00:00'))
    
    bbox = BoundingBox(
        min_lon=request.bbox.min_lon,
        min_lat=request.bbox.min_lat,
        max_lon=request.bbox.max_lon,
        max_lat=request.bbox.max_lat,
    )
    
    analysis = engine.analyze_flooding(bbox, event_date, baseline_date)
    
    return {
        "analysis_id": str(analysis.analysis_id),
        "analysis_type": "FLOODING",
        "bbox": bbox.to_dict(),
        "event_date": event_date.isoformat(),
        "baseline_date": baseline_date.isoformat(),
        "flooded_area_hectares": analysis.flooded_area_hectares,
        "flooded_area_percentage": analysis.flooded_area_percentage,
        "water_level_change_meters": analysis.water_level_change_meters,
        "affected_locations": analysis.affected_locations,
        "severity": analysis.severity.value,
        "confidence": analysis.confidence,
        "details": analysis.details,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/analysis/agriculture")
async def analyze_agriculture(
    request: AgricultureAnalysisRequest,
    user: Annotated[dict, Depends(require_permission("satellite:analyze"))],
) -> dict[str, Any]:
    """Monitor agricultural health and conditions."""
    engine = get_temporal_engine()
    
    analysis_date = datetime.fromisoformat(request.analysis_date.replace('Z', '+00:00'))
    
    bbox = BoundingBox(
        min_lon=request.bbox.min_lon,
        min_lat=request.bbox.min_lat,
        max_lon=request.bbox.max_lon,
        max_lat=request.bbox.max_lat,
    )
    
    analysis = engine.analyze_agriculture(bbox, analysis_date)
    
    return {
        "analysis_id": str(analysis.analysis_id),
        "analysis_type": "AGRICULTURE",
        "bbox": bbox.to_dict(),
        "analysis_date": analysis_date.isoformat(),
        "crop_health_index": analysis.crop_health_index,
        "vegetation_vigor": analysis.vegetation_vigor,
        "crop_area_hectares": analysis.crop_area_hectares,
        "health_status": analysis.health_status,
        "irrigation_detected": analysis.irrigation_detected,
        "crop_stage": analysis.crop_stage,
        "recommendations": analysis.recommendations,
        "details": analysis.details,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/analysis/wildfire")
async def analyze_wildfire(
    request: WildfireAnalysisRequest,
    user: Annotated[dict, Depends(require_permission("satellite:analyze"))],
) -> dict[str, Any]:
    """Detect and analyze wildfires."""
    engine = get_temporal_engine()
    
    detection_date = datetime.fromisoformat(request.detection_date.replace('Z', '+00:00'))
    pre_fire_date = datetime.fromisoformat(request.pre_fire_date.replace('Z', '+00:00'))
    
    bbox = BoundingBox(
        min_lon=request.bbox.min_lon,
        min_lat=request.bbox.min_lat,
        max_lon=request.bbox.max_lon,
        max_lat=request.bbox.max_lat,
    )
    
    analysis = engine.analyze_wildfire(bbox, detection_date, pre_fire_date)
    
    return {
        "analysis_id": str(analysis.analysis_id),
        "analysis_type": "WILDFIRE",
        "bbox": bbox.to_dict(),
        "detection_date": detection_date.isoformat(),
        "pre_fire_date": pre_fire_date.isoformat(),
        "burned_area_hectares": analysis.burned_area_hectares,
        "fire_intensity": analysis.fire_intensity,
        "active_fire_locations": analysis.active_fire_locations,
        "smoke_detected": analysis.smoke_detected,
        "wind_direction": analysis.wind_direction,
        "severity": analysis.severity.value,
        "confidence": analysis.confidence,
        "recovery_analysis": analysis.recovery_analysis,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/analysis/long-term-trend")
async def analyze_long_term_trend(
    request: LongTermTrendRequest,
    user: Annotated[dict, Depends(require_permission("satellite:analyze"))],
) -> dict[str, Any]:
    """Analyze long-term environmental trends."""
    engine = get_temporal_engine()
    
    start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    
    bbox = BoundingBox(
        min_lon=request.bbox.min_lon,
        min_lat=request.bbox.min_lat,
        max_lon=request.bbox.max_lon,
        max_lat=request.bbox.max_lat,
    )
    
    # Generate mock time series data for demonstration
    # In production, this would come from actual historical satellite data
    time_series_data = []
    current = start_date
    while current <= end_date:
        time_series_data.append({
            "date": current.isoformat(),
            "value": 0.5 + (len(time_series_data) * 0.01),  # Mock trend
        })
        current += timedelta(days=30)
    
    trend = engine.analyze_long_term_trend(
        request.analysis_type,
        bbox,
        start_date,
        end_date,
        time_series_data,
    )
    
    return {
        "trend_id": str(trend.trend_id),
        "analysis_type": trend.analysis_type.value,
        "bbox": bbox.to_dict(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trend_direction": trend.trend_direction.value,
        "rate_of_change": trend.rate_of_change,
        "significance": trend.significance,
        "data_points": trend.data_points,
        "predictions": trend.predictions,
        "details": trend.details,
        "timestamp": utcnow().isoformat(),
    }


@router.get("/areas-of-interest")
async def get_predefined_areas(
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
) -> dict[str, Any]:
    """Get predefined areas of interest."""
    service = get_satellite_service()
    
    return {
        "areas": {
            name: bbox.to_dict()
            for name, bbox in service.predefined_aois.items()
        }
    }


@router.get("/stats")
async def get_satellite_stats(
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
) -> dict[str, Any]:
    """Get satellite analysis statistics."""
    satellite_service = get_satellite_service()
    temporal_engine = get_temporal_engine()
    integration_service = get_satellite_integration()
    
    return {
        "satellite_service": satellite_service.get_stats(),
        "temporal_analysis": temporal_engine.get_stats(),
        "integration": integration_service.get_stats(),
        "timestamp": utcnow().isoformat(),
    }


# ============================================================================
# Alert and Integration Endpoints
# ============================================================================

@router.get("/alerts")
async def list_satellite_alerts(
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
    severity: AlertSeverity | None = Query(default=None),
    event_type: SatelliteEventType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """List satellite-generated alerts."""
    integration = get_satellite_integration()
    
    alerts = list(integration.alerts.values())
    
    # Filter by severity
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    # Filter by event type
    if event_type:
        alerts = [a for a in alerts if a.event_type == event_type]
    
    # Sort by detection date (most recent first)
    alerts.sort(key=lambda x: x.detection_date, reverse=True)
    
    return {
        "total": len(alerts),
        "alerts": [
            {
                "alert_id": str(a.alert_id),
                "event_type": a.event_type.value,
                "severity": a.severity.value,
                "location": a.location,
                "area_affected_hectares": a.area_affected_hectares,
                "detection_date": a.detection_date.isoformat(),
                "confidence": a.confidence,
                "description": a.description,
                "threat_level": a.threat_level.value if a.threat_level else None,
                "narrative_ids": [str(nid) for nid in a.narrative_ids],
                "recommended_actions": a.recommended_actions[:3],  # Top 3
            }
            for a in alerts[:limit]
        ],
        "timestamp": utcnow().isoformat(),
    }


@router.get("/alerts/{alert_id}")
async def get_satellite_alert(
    alert_id: UUID,
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
) -> dict[str, Any]:
    """Get detailed information about a satellite alert."""
    integration = get_satellite_integration()
    
    alert = integration.alerts.get(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    
    # Get narrative links
    narrative_links = integration.get_narrative_links(alert_id)
    
    return {
        "alert_id": str(alert.alert_id),
        "event_type": alert.event_type.value,
        "severity": alert.severity.value,
        "location": alert.location,
        "area_affected_hectares": alert.area_affected_hectares,
        "detection_date": alert.detection_date.isoformat(),
        "confidence": alert.confidence,
        "description": alert.description,
        "analysis_id": str(alert.analysis_id),
        "metadata": alert.metadata,
        "threat_level": alert.threat_level.value if alert.threat_level else None,
        "recommended_actions": alert.recommended_actions,
        "narrative_links": [
            {
                "link_id": str(link.link_id),
                "narrative_id": str(link.narrative_id),
                "correlation_score": link.correlation_score,
                "evidence": link.evidence,
            }
            for link in narrative_links
        ],
        "timestamp": utcnow().isoformat(),
    }


@router.get("/alerts/nearby")
async def get_nearby_alerts(
    user: Annotated[dict, Depends(require_permission("satellite:read"))],
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """Get alerts near a location."""
    integration = get_satellite_integration()
    
    alerts = integration.get_alerts_by_location(lat, lon, radius_km)
    
    # Sort by distance (approximation by checking location)
    return {
        "query_location": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "total": len(alerts),
        "alerts": [
            {
                "alert_id": str(a.alert_id),
                "event_type": a.event_type.value,
                "severity": a.severity.value,
                "location": a.location,
                "area_affected_hectares": a.area_affected_hectares,
                "detection_date": a.detection_date.isoformat(),
                "description": a.description,
            }
            for a in alerts
        ],
        "timestamp": utcnow().isoformat(),
    }


@router.post("/alerts/generate-from-analysis")
async def generate_alert_from_analysis(
    user: Annotated[dict, Depends(require_permission("satellite:write"))],
    analysis_type: str = Query(...),
    analysis_id: UUID = Query(...),
) -> dict[str, Any]:
    """Generate alert from existing analysis."""
    integration = get_satellite_integration()
    temporal_engine = get_temporal_engine()
    
    alert = None
    
    if analysis_type == "deforestation":
        analysis = temporal_engine.deforestation_analyses.get(analysis_id)
        if analysis:
            alert = integration.process_deforestation_alert(analysis)
    
    elif analysis_type == "flooding":
        analysis = temporal_engine.flood_analyses.get(analysis_id)
        if analysis:
            alert = integration.process_flood_alert(analysis)
    
    elif analysis_type == "wildfire":
        analysis = temporal_engine.wildfire_analyses.get(analysis_id)
        if analysis:
            alert = integration.process_wildfire_alert(analysis)
    
    elif analysis_type == "urban_growth":
        analysis = temporal_engine.urban_growth_analyses.get(analysis_id)
        if analysis:
            alert = integration.process_urban_growth_alert(analysis)
    
    elif analysis_type == "agriculture":
        analysis = temporal_engine.agriculture_analyses.get(analysis_id)
        if analysis:
            alert = integration.process_agriculture_alert(analysis)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid analysis type: {analysis_type}",
        )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )
    
    return {
        "alert_id": str(alert.alert_id),
        "event_type": alert.event_type.value,
        "severity": alert.severity.value,
        "description": alert.description,
        "narrative_ids": [str(nid) for nid in alert.narrative_ids],
        "timestamp": utcnow().isoformat(),
    }


def _get_provider_description(provider: SatelliteProvider) -> str:
    """Get description for satellite provider."""
    descriptions = {
        SatelliteProvider.SENTINEL_2: "ESA Copernicus optical imagery, 10m resolution",
        SatelliteProvider.SENTINEL_1: "ESA Copernicus SAR imagery",
        SatelliteProvider.MODIS: "NASA Terra/Aqua, daily global coverage",
        SatelliteProvider.LANDSAT_8: "NASA/USGS Landsat 8, 30m resolution",
        SatelliteProvider.LANDSAT_9: "NASA/USGS Landsat 9, 30m resolution",
        SatelliteProvider.GOOGLE_EARTH: "Google Earth Engine multi-source",
        SatelliteProvider.PLANET_LABS: "Planet Labs high-resolution imagery",
    }
    return descriptions.get(provider, "Satellite imagery provider")


def _get_provider_resolution(provider: SatelliteProvider) -> float:
    """Get typical resolution for provider."""
    resolutions = {
        SatelliteProvider.SENTINEL_2: 10.0,
        SatelliteProvider.SENTINEL_1: 10.0,
        SatelliteProvider.MODIS: 250.0,
        SatelliteProvider.LANDSAT_8: 30.0,
        SatelliteProvider.LANDSAT_9: 30.0,
        SatelliteProvider.GOOGLE_EARTH: 10.0,
        SatelliteProvider.PLANET_LABS: 3.0,
    }
    return resolutions.get(provider, 10.0)
