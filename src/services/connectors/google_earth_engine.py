"""Google Earth Engine Connector.

Provides access to Google Earth Engine's massive catalog of satellite imagery
and geospatial datasets for analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Google Earth Engine library not available. Install with: pip install earthengine-api")

from .base import BaseConnector, ConnectorConfig
from ..satellite_analysis import (
    SatelliteImage,
    SatelliteProvider,
    BoundingBox,
    get_satellite_service,
)


logger = logging.getLogger(__name__)


class GoogleEarthEngineConnector(BaseConnector[list[dict[str, Any]]]):
    """Google Earth Engine data connector.
    
    Features:
    - Access to petabytes of satellite imagery
    - Sentinel-2, Landsat, MODIS datasets
    - Cloud-based processing
    - Time series analysis
    - Climate and weather data
    
    Requires:
    - Google Cloud Project
    - Earth Engine API access
    - Service account credentials
    """

    def __init__(
        self,
        service_account: str | None = None,
        key_file: str | None = None,
        areas_of_interest: list[BoundingBox] | None = None,
        config: ConnectorConfig | None = None,
    ):
        """Initialize Google Earth Engine connector.
        
        Args:
            service_account: Service account email
            key_file: Path to service account key JSON file
            areas_of_interest: List of bounding boxes to monitor
            config: Connector configuration
        """
        if config is None:
            config = ConnectorConfig(
                name="GoogleEarthEngine",
                max_requests_per_minute=10,
                max_requests_per_hour=500,
                poll_interval_seconds=86400,
            )
        
        super().__init__(config)
        
        self.service_account = service_account
        self.key_file = key_file
        self.areas_of_interest = areas_of_interest or []
        self.authenticated = False
        
        if not EE_AVAILABLE:
            logger.error("Google Earth Engine library not installed")
            return
        
        # Initialize Earth Engine
        try:
            if service_account and key_file:
                credentials = ee.ServiceAccountCredentials(service_account, key_file)
                ee.Initialize(credentials)
            else:
                # Try default authentication
                ee.Initialize()
            
            self.authenticated = True
            logger.info("Google Earth Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Earth Engine: {e}")
            self.authenticated = False
        
        self.satellite_service = get_satellite_service()
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch imagery from Google Earth Engine."""
        if not self.authenticated or not EE_AVAILABLE:
            logger.warning("Google Earth Engine not authenticated")
            return None
        
        all_images = []
        
        for aoi in self.areas_of_interest:
            try:
                # Fetch from multiple datasets
                sentinel2_images = await self._fetch_sentinel2_gee(aoi)
                landsat_images = await self._fetch_landsat_gee(aoi)
                modis_images = await self._fetch_modis_gee(aoi)
                
                all_images.extend(sentinel2_images)
                all_images.extend(landsat_images)
                all_images.extend(modis_images)
                
            except Exception as e:
                logger.error(f"Error fetching GEE data for AOI: {e}")
                continue
        
        return all_images if all_images else None
    
    async def _fetch_sentinel2_gee(
        self,
        bbox: BoundingBox,
        days_back: int = 30,
        cloud_cover_max: float = 30,
    ) -> list[dict[str, Any]]:
        """Fetch Sentinel-2 data via Google Earth Engine."""
        if not self.authenticated:
            return []
        
        try:
            # Define area of interest
            geometry = ee.Geometry.Rectangle([
                bbox.min_lon, bbox.min_lat,
                bbox.max_lon, bbox.max_lat
            ])
            
            # Date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Query Sentinel-2 collection
            collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(geometry) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max))
            
            # Get collection info
            size = collection.size().getInfo()
            logger.info(f"Found {size} Sentinel-2 images in GEE")
            
            if size == 0:
                return []
            
            # Get image list (limit to 10 most recent)
            images = collection.sort('system:time_start', False).limit(10).getInfo()
            
            results = []
            for img_info in images.get('features', []):
                properties = img_info.get('properties', {})
                img_id = img_info.get('id', '')
                
                image_data = {
                    "image_id": img_id,
                    "provider": "Sentinel-2 (GEE)",
                    "acquisition_date": datetime.fromtimestamp(
                        properties.get('system:time_start', 0) / 1000
                    ).isoformat(),
                    "cloud_coverage": properties.get('CLOUDY_PIXEL_PERCENTAGE', 0),
                    "resolution_meters": 10,
                    "bbox": bbox.to_dict(),
                    "bands": ["B2", "B3", "B4", "B8", "B11", "B12"],
                    "gee_asset_id": img_id,
                    "metadata": properties,
                }
                
                results.append(image_data)
                self._store_gee_image(image_data, bbox)
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching Sentinel-2 from GEE: {e}")
            return []
    
    async def _fetch_landsat_gee(
        self,
        bbox: BoundingBox,
        days_back: int = 30,
        cloud_cover_max: float = 30,
    ) -> list[dict[str, Any]]:
        """Fetch Landsat data via Google Earth Engine."""
        if not self.authenticated:
            return []
        
        try:
            geometry = ee.Geometry.Rectangle([
                bbox.min_lon, bbox.min_lat,
                bbox.max_lon, bbox.max_lat
            ])
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Query Landsat 8/9 collection
            collection = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
                .filterBounds(geometry) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover_max))
            
            size = collection.size().getInfo()
            logger.info(f"Found {size} Landsat images in GEE")
            
            if size == 0:
                return []
            
            images = collection.sort('system:time_start', False).limit(10).getInfo()
            
            results = []
            for img_info in images.get('features', []):
                properties = img_info.get('properties', {})
                img_id = img_info.get('id', '')
                
                image_data = {
                    "image_id": img_id,
                    "provider": "Landsat-9 (GEE)",
                    "acquisition_date": datetime.fromtimestamp(
                        properties.get('system:time_start', 0) / 1000
                    ).isoformat(),
                    "cloud_coverage": properties.get('CLOUD_COVER', 0),
                    "resolution_meters": 30,
                    "bbox": bbox.to_dict(),
                    "bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
                    "gee_asset_id": img_id,
                    "metadata": properties,
                }
                
                results.append(image_data)
                self._store_gee_image(image_data, bbox, provider=SatelliteProvider.LANDSAT_9)
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching Landsat from GEE: {e}")
            return []
    
    async def _fetch_modis_gee(
        self,
        bbox: BoundingBox,
        days_back: int = 30,
    ) -> list[dict[str, Any]]:
        """Fetch MODIS data via Google Earth Engine."""
        if not self.authenticated:
            return []
        
        try:
            geometry = ee.Geometry.Rectangle([
                bbox.min_lon, bbox.min_lat,
                bbox.max_lon, bbox.max_lat
            ])
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Query MODIS Terra collection
            collection = ee.ImageCollection('MODIS/061/MOD09A1') \
                .filterBounds(geometry) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            size = collection.size().getInfo()
            logger.info(f"Found {size} MODIS images in GEE")
            
            if size == 0:
                return []
            
            images = collection.sort('system:time_start', False).limit(10).getInfo()
            
            results = []
            for img_info in images.get('features', []):
                properties = img_info.get('properties', {})
                img_id = img_info.get('id', '')
                
                image_data = {
                    "image_id": img_id,
                    "provider": "MODIS (GEE)",
                    "acquisition_date": datetime.fromtimestamp(
                        properties.get('system:time_start', 0) / 1000
                    ).isoformat(),
                    "cloud_coverage": 0,  # MODIS doesn't have cloud cover in metadata
                    "resolution_meters": 500,
                    "bbox": bbox.to_dict(),
                    "bands": ["sur_refl_b01", "sur_refl_b02", "sur_refl_b03", "sur_refl_b04"],
                    "gee_asset_id": img_id,
                    "metadata": properties,
                }
                
                results.append(image_data)
                self._store_gee_image(image_data, bbox, provider=SatelliteProvider.MODIS)
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching MODIS from GEE: {e}")
            return []
    
    def _store_gee_image(
        self,
        image_data: dict[str, Any],
        bbox: BoundingBox,
        provider: SatelliteProvider = SatelliteProvider.SENTINEL_2,
    ) -> None:
        """Store GEE image metadata."""
        try:
            acquisition_date = image_data.get("acquisition_date")
            if isinstance(acquisition_date, str):
                acquisition_date = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))
            
            image = SatelliteImage(
                image_id=uuid4(),
                provider=provider,
                acquisition_date=acquisition_date,
                cloud_coverage=float(image_data.get("cloud_coverage", 0)),
                resolution_meters=float(image_data.get("resolution_meters", 10)),
                bbox=bbox,
                bands=image_data.get("bands", []),
                metadata=image_data,
            )
            
            self.satellite_service.images[image.image_id] = image
            
        except Exception as e:
            logger.error(f"Error storing GEE image metadata: {e}")
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest GEE data into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for image in data:
            try:
                await kafka.publish_osint_data(
                    source_type="satellite",
                    source_id=f"gee_{image['image_id']}",
                    content=f"Google Earth Engine imagery: {image['provider']}",
                    metadata=image,
                )
                
                logger.debug(f"Ingested GEE image: {image['image_id']}")
            
            except Exception as e:
                logger.error(f"Error ingesting GEE data: {e}")
                continue
    
    def calculate_ndvi_gee(
        self,
        image_id: str,
        bbox: BoundingBox,
    ) -> dict[str, Any] | None:
        """Calculate NDVI using Google Earth Engine processing.
        
        Args:
            image_id: GEE asset ID
            bbox: Area of interest
        
        Returns:
            NDVI statistics
        """
        if not self.authenticated:
            return None
        
        try:
            # Load image
            image = ee.Image(image_id)
            
            # Define geometry
            geometry = ee.Geometry.Rectangle([
                bbox.min_lon, bbox.min_lat,
                bbox.max_lon, bbox.max_lat
            ])
            
            # Calculate NDVI
            # For Sentinel-2: (B8 - B4) / (B8 + B4)
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            # Get statistics
            stats = ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), '', True
                ).combine(
                    ee.Reducer.stdDev(), '', True
                ),
                geometry=geometry,
                scale=10,
                maxPixels=1e9,
            ).getInfo()
            
            return {
                "mean": stats.get('NDVI_mean'),
                "min": stats.get('NDVI_min'),
                "max": stats.get('NDVI_max'),
                "std": stats.get('NDVI_stdDev'),
                "bbox": bbox.to_dict(),
            }
        
        except Exception as e:
            logger.error(f"Error calculating NDVI in GEE: {e}")
            return None
    
    def export_image(
        self,
        image_id: str,
        bbox: BoundingBox,
        scale: int = 10,
        format: str = "GeoTIFF",
    ) -> str | None:
        """Export image from Google Earth Engine.
        
        Args:
            image_id: GEE asset ID
            bbox: Area to export
            scale: Resolution in meters
            format: Export format
        
        Returns:
            Export task ID
        """
        if not self.authenticated:
            return None
        
        try:
            image = ee.Image(image_id)
            
            geometry = ee.Geometry.Rectangle([
                bbox.min_lon, bbox.min_lat,
                bbox.max_lon, bbox.max_lat
            ])
            
            task = ee.batch.Export.image.toDrive(
                image=image,
                description=f'export_{image_id.replace("/", "_")}',
                folder='EarthEngineExports',
                region=geometry,
                scale=scale,
                fileFormat=format,
            )
            
            task.start()
            
            logger.info(f"Started export task: {task.id}")
            return task.id
        
        except Exception as e:
            logger.error(f"Error exporting image: {e}")
            return None
