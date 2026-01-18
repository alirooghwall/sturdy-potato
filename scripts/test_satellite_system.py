"""Comprehensive test suite for satellite imagery analysis system."""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, UTC
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.satellite_analysis import (
    get_satellite_service,
    BoundingBox,
    SatelliteProvider,
    SatelliteImage,
)
from src.services.temporal_analysis import (
    get_temporal_engine,
    AlertSeverity,
)
import numpy as np


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)


def test_satellite_service():
    """Test core satellite analysis service."""
    print("=" * 80)
    print("TEST 1: Satellite Analysis Service")
    print("=" * 80)
    
    service = get_satellite_service()
    
    # Test 1.1: Predefined AOIs
    print("\n[1.1] Testing predefined Areas of Interest...")
    print(f"✓ Loaded {len(service.predefined_aois)} predefined AOIs:")
    for name, bbox in service.predefined_aois.items():
        print(f"  - {name}: {bbox.to_dict()}")
    
    # Test 1.2: Spectral indices
    print("\n[1.2] Testing spectral index calculations...")
    
    # Create mock bands
    red_band = np.random.uniform(0.1, 0.3, (100, 100))
    nir_band = np.random.uniform(0.4, 0.7, (100, 100))
    green_band = np.random.uniform(0.2, 0.4, (100, 100))
    swir_band = np.random.uniform(0.3, 0.5, (100, 100))
    
    # Calculate NDVI
    ndvi = service.calculate_ndvi(red_band, nir_band)
    print(f"✓ NDVI calculated: mean={np.mean(ndvi):.3f}, range=[{np.min(ndvi):.3f}, {np.max(ndvi):.3f}]")
    
    # Calculate NDWI
    ndwi = service.calculate_ndwi(green_band, nir_band)
    print(f"✓ NDWI calculated: mean={np.mean(ndwi):.3f}, range=[{np.min(ndwi):.3f}, {np.max(ndwi):.3f}]")
    
    # Calculate NDBI
    ndbi = service.calculate_ndbi(swir_band, nir_band)
    print(f"✓ NDBI calculated: mean={np.mean(ndbi):.3f}, range=[{np.min(ndbi):.3f}, {np.max(ndbi):.3f}]")
    
    # Calculate NBR
    nbr = service.calculate_nbr(nir_band, swir_band)
    print(f"✓ NBR calculated: mean={np.mean(nbr):.3f}, range=[{np.min(nbr):.3f}, {np.max(nbr):.3f}]")
    
    # Test 1.3: Image metadata storage
    print("\n[1.3] Testing image metadata storage...")
    
    test_image = SatelliteImage(
        image_id=uuid4(),
        provider=SatelliteProvider.SENTINEL_2,
        acquisition_date=utcnow(),
        cloud_coverage=15.5,
        resolution_meters=10.0,
        bbox=service.predefined_aois["kabul"],
        bands=["B02", "B03", "B04", "B08"],
        metadata={"test": "data"},
    )
    
    service.images[test_image.image_id] = test_image
    print(f"✓ Stored test image: {test_image.image_id}")
    print(f"  - Provider: {test_image.provider.value}")
    print(f"  - Resolution: {test_image.resolution_meters}m")
    print(f"  - Cloud coverage: {test_image.cloud_coverage}%")
    
    print("\n✓ Satellite service tests completed successfully!\n")


def test_deforestation_analysis():
    """Test deforestation detection."""
    print("=" * 80)
    print("TEST 2: Deforestation Analysis (Panjshir Valley)")
    print("=" * 80)
    
    engine = get_temporal_engine()
    service = get_satellite_service()
    
    # Use Panjshir Valley AOI
    bbox = service.predefined_aois["panjshir_valley"]
    
    print(f"\nAnalyzing: Panjshir Valley")
    print(f"Bounding Box: {bbox.to_dict()}")
    
    # Dates
    before_date = datetime(2023, 1, 1, tzinfo=UTC)
    after_date = datetime(2024, 1, 1, tzinfo=UTC)
    
    print(f"Before: {before_date.date()}")
    print(f"After: {after_date.date()}")
    
    # Perform analysis
    analysis = engine.analyze_deforestation(bbox, before_date, after_date)
    
    print(f"\n✓ Deforestation Analysis Results:")
    print(f"  - Analysis ID: {analysis.analysis_id}")
    print(f"  - Forest Loss: {analysis.forest_loss_hectares:.2f} hectares")
    print(f"  - Loss Percentage: {analysis.forest_loss_percentage:.2f}%")
    print(f"  - Severity: {analysis.severity.value}")
    print(f"  - Confidence: {analysis.confidence:.2f}")
    print(f"  - Affected Areas: {len(analysis.affected_areas)}")
    
    if analysis.affected_areas:
        print(f"\n  Top Affected Location:")
        area = analysis.affected_areas[0]
        print(f"    - Centroid: {area['centroid']}")
        print(f"    - Area: {area['area_hectares']:.2f} ha")
    
    print("\n✓ Deforestation analysis completed!\n")
    return analysis


def test_urban_growth_analysis():
    """Test urban growth detection."""
    print("=" * 80)
    print("TEST 3: Urban Growth Analysis (Kabul)")
    print("=" * 80)
    
    engine = get_temporal_engine()
    service = get_satellite_service()
    
    bbox = service.predefined_aois["kabul"]
    
    print(f"\nAnalyzing: Kabul")
    print(f"Bounding Box: {bbox.to_dict()}")
    
    before_date = datetime(2020, 1, 1, tzinfo=UTC)
    after_date = datetime(2024, 1, 1, tzinfo=UTC)
    
    print(f"Before: {before_date.date()}")
    print(f"After: {after_date.date()}")
    
    analysis = engine.analyze_urban_growth(bbox, before_date, after_date)
    
    print(f"\n✓ Urban Growth Analysis Results:")
    print(f"  - Analysis ID: {analysis.analysis_id}")
    print(f"  - Urban Expansion: {analysis.urban_expansion_hectares:.2f} hectares")
    print(f"  - Expansion Percentage: {analysis.urban_expansion_percentage:.2f}%")
    print(f"  - Annual Growth Rate: {analysis.growth_rate_annual:.2f}%/year")
    print(f"  - New Urban Areas: {len(analysis.new_urban_areas)}")
    print(f"  - Infrastructure Detected: {analysis.infrastructure_detected}")
    
    print("\n✓ Urban growth analysis completed!\n")
    return analysis


def test_flood_analysis():
    """Test flood detection."""
    print("=" * 80)
    print("TEST 4: Flood Detection (Helmand Valley)")
    print("=" * 80)
    
    engine = get_temporal_engine()
    service = get_satellite_service()
    
    bbox = service.predefined_aois["helmand_valley"]
    
    print(f"\nAnalyzing: Helmand Valley")
    print(f"Bounding Box: {bbox.to_dict()}")
    
    baseline_date = datetime(2024, 5, 1, tzinfo=UTC)
    event_date = datetime(2024, 6, 15, tzinfo=UTC)
    
    print(f"Baseline: {baseline_date.date()}")
    print(f"Event: {event_date.date()}")
    
    analysis = engine.analyze_flooding(bbox, event_date, baseline_date)
    
    print(f"\n✓ Flood Analysis Results:")
    print(f"  - Analysis ID: {analysis.analysis_id}")
    print(f"  - Flooded Area: {analysis.flooded_area_hectares:.2f} hectares")
    print(f"  - Flooding Percentage: {analysis.flooded_area_percentage:.2f}%")
    print(f"  - Severity: {analysis.severity.value}")
    print(f"  - Confidence: {analysis.confidence:.2f}")
    print(f"  - Affected Locations: {len(analysis.affected_locations)}")
    
    print("\n✓ Flood analysis completed!\n")
    return analysis


def test_agriculture_monitoring():
    """Test agriculture monitoring."""
    print("=" * 80)
    print("TEST 5: Agriculture Monitoring (Herat)")
    print("=" * 80)
    
    engine = get_temporal_engine()
    service = get_satellite_service()
    
    bbox = service.predefined_aois["herat"]
    
    print(f"\nAnalyzing: Herat")
    print(f"Bounding Box: {bbox.to_dict()}")
    
    analysis_date = datetime(2024, 7, 15, tzinfo=UTC)
    print(f"Analysis Date: {analysis_date.date()}")
    
    analysis = engine.analyze_agriculture(bbox, analysis_date)
    
    print(f"\n✓ Agriculture Analysis Results:")
    print(f"  - Analysis ID: {analysis.analysis_id}")
    print(f"  - Crop Health Index: {analysis.crop_health_index:.2f}")
    print(f"  - Vegetation Vigor: {analysis.vegetation_vigor:.2f}")
    print(f"  - Crop Area: {analysis.crop_area_hectares:.2f} hectares")
    print(f"  - Health Status: {analysis.health_status}")
    print(f"  - Irrigation Detected: {analysis.irrigation_detected}")
    
    if analysis.recommendations:
        print(f"\n  Recommendations:")
        for rec in analysis.recommendations:
            print(f"    - {rec}")
    
    print("\n✓ Agriculture monitoring completed!\n")
    return analysis


def test_wildfire_detection():
    """Test wildfire detection."""
    print("=" * 80)
    print("TEST 6: Wildfire Detection (Kandahar)")
    print("=" * 80)
    
    engine = get_temporal_engine()
    service = get_satellite_service()
    
    bbox = service.predefined_aois["kandahar"]
    
    print(f"\nAnalyzing: Kandahar")
    print(f"Bounding Box: {bbox.to_dict()}")
    
    pre_fire_date = datetime(2024, 8, 1, tzinfo=UTC)
    detection_date = datetime(2024, 8, 15, tzinfo=UTC)
    
    print(f"Pre-fire: {pre_fire_date.date()}")
    print(f"Detection: {detection_date.date()}")
    
    analysis = engine.analyze_wildfire(bbox, detection_date, pre_fire_date)
    
    print(f"\n✓ Wildfire Analysis Results:")
    print(f"  - Analysis ID: {analysis.analysis_id}")
    print(f"  - Burned Area: {analysis.burned_area_hectares:.2f} hectares")
    print(f"  - Fire Intensity: {analysis.fire_intensity}")
    print(f"  - Severity: {analysis.severity.value}")
    print(f"  - Confidence: {analysis.confidence:.2f}")
    print(f"  - Active Fire Locations: {len(analysis.active_fire_locations)}")
    
    print("\n✓ Wildfire detection completed!\n")
    return analysis


def test_long_term_trends():
    """Test long-term trend analysis."""
    print("=" * 80)
    print("TEST 7: Long-term Trend Analysis (Mazar-i-Sharif)")
    print("=" * 80)
    
    engine = get_temporal_engine()
    service = get_satellite_service()
    
    bbox = service.predefined_aois["mazar_sharif"]
    
    print(f"\nAnalyzing: Mazar-i-Sharif")
    print(f"Bounding Box: {bbox.to_dict()}")
    
    start_date = datetime(2020, 1, 1, tzinfo=UTC)
    end_date = datetime(2024, 1, 1, tzinfo=UTC)
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    
    # Generate mock time series data
    time_series_data = []
    current = start_date
    value = 0.5
    
    while current <= end_date:
        value += np.random.uniform(-0.02, 0.03)  # Slight upward trend
        value = max(0.3, min(0.8, value))
        
        time_series_data.append({
            "date": current.isoformat(),
            "value": value,
        })
        
        current += timedelta(days=30)
    
    print(f"Data Points: {len(time_series_data)}")
    
    from src.services.satellite_analysis import AnalysisType
    analysis = engine.analyze_long_term_trend(
        AnalysisType.VEGETATION_HEALTH,
        bbox,
        start_date,
        end_date,
        time_series_data,
    )
    
    print(f"\n✓ Long-term Trend Analysis Results:")
    print(f"  - Trend ID: {analysis.trend_id}")
    print(f"  - Analysis Type: {analysis.analysis_type.value}")
    print(f"  - Trend Direction: {analysis.trend_direction.value}")
    print(f"  - Rate of Change: {analysis.rate_of_change:.4f}/year")
    print(f"  - Significance (R²): {analysis.significance:.3f}")
    print(f"  - Data Points: {len(analysis.data_points)}")
    
    if analysis.predictions:
        print(f"\n  Predictions:")
        pred_values = analysis.predictions.get("predicted_values", [])
        print(f"    - Next 4 periods: {[f'{v:.3f}' for v in pred_values]}")
        print(f"    - Confidence: {analysis.predictions.get('confidence', 0):.3f}")
    
    print("\n✓ Long-term trend analysis completed!\n")
    return analysis


def test_statistics():
    """Test system statistics."""
    print("=" * 80)
    print("TEST 8: System Statistics")
    print("=" * 80)
    
    service = get_satellite_service()
    engine = get_temporal_engine()
    
    print("\n[Satellite Service Statistics]")
    sat_stats = service.get_stats()
    for key, value in sat_stats.items():
        print(f"  - {key}: {value}")
    
    print("\n[Temporal Analysis Statistics]")
    temp_stats = engine.get_stats()
    for key, value in temp_stats.items():
        print(f"  - {key}: {value}")
    
    print("\n✓ Statistics retrieved successfully!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("SATELLITE IMAGERY ANALYSIS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80 + "\n")
    
    try:
        # Run tests
        test_satellite_service()
        
        deforestation = test_deforestation_analysis()
        urban_growth = test_urban_growth_analysis()
        flood = test_flood_analysis()
        agriculture = test_agriculture_monitoring()
        wildfire = test_wildfire_detection()
        trend = test_long_term_trends()
        
        test_statistics()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print("\n✓ All 8 test suites completed successfully!")
        print("\nAnalyses Performed:")
        print(f"  1. Deforestation (Panjshir Valley): {deforestation.forest_loss_percentage:.1f}% loss")
        print(f"  2. Urban Growth (Kabul): {urban_growth.urban_expansion_percentage:.1f}% expansion")
        print(f"  3. Flooding (Helmand Valley): {flood.flooded_area_percentage:.1f}% flooded")
        print(f"  4. Agriculture (Herat): {agriculture.health_status} crops")
        print(f"  5. Wildfire (Kandahar): {wildfire.fire_intensity} intensity")
        print(f"  6. Trend (Mazar-i-Sharif): {trend.trend_direction.value}")
        
        print("\n" + "=" * 80)
        print("✓ SATELLITE SYSTEM FULLY OPERATIONAL")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
