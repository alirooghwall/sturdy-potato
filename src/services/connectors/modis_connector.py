"""MODIS Satellite Data Connector (NASA Terra/Aqua).

Connects to NASA's MODIS (Moderate Resolution Imaging Spectroradiometer)
satellite data for environmental monitoring and change detection.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from .base import BaseConnector, ConnectorConfig
from ..satellite_analysis import (
    SatelliteImage,
    SatelliteProvider,
    BoundingBox,
    get_satellite_service,
)


logger = logging.getLogger(__name__)


class MODISConnector(BaseConnector[list[dict[str, Any]]]):
    """MODIS satellite data connector.
    
    Features:
    - 250m-1km resolution
    - Daily global coverage
    - 36 spectral bands
    - Long-term data archive (2000-present)
    - Excellent for:
      - Vegetation monitoring
      - Fire detection
      - Land surface temperature
      - Snow/ice cover
      - Ocean color
    
    MODIS Products:
    - MOD09: Surface Reflectance
    - MOD11: Land Surface Temperature
    - MOD13: Vegetation Indices (NDVI/EVI)
    - MOD14: Thermal Anomalies/Fire
    - MOD15: LAI/FPAR
    - MCD43: BRDF/Albedo
    """

    def __init__(
        self,
        api_key: str | None = None,
        areas_of_interest: list[BoundingBox] | None = None,
        config: ConnectorConfig | None = None,
    ):
        """Initialize MODIS connector.
        
        Args:
            api_key: NASA EarthData API key (optional for some products)
            areas_of_interest: List of bounding boxes to monitor
            config: Connector configuration
        """
        if config is None:
            config = ConnectorConfig(
                name="MODIS",
                max_requests_per_minute=10,
                max_requests_per_hour=200,
                poll_interval_seconds=86400,  # Daily
            )
        
        super().__init__(config)
        
        self.api_key = api_key
        self.areas_of_interest = areas_of_interest or []
        
        # MODIS data endpoints
        self.modis_base_url = "https://modis.ornl.gov/rst/api/v1"
        self.earthdata_search_url = "https://cmr.earthdata.nasa.gov/search"
        
        # MODIS products to monitor
        self.products = [
            "MOD09A1",  # Surface Reflectance 8-Day L3 (500m)
            "MOD13Q1",  # Vegetation Indices 16-Day L3 (250m)
            "MOD14A1",  # Thermal Anomalies/Fire Daily L3 (1km)
            "MOD11A1",  # Land Surface Temperature Daily L3 (1km)
        ]
        
        self.satellite_service = get_satellite_service()
        
        logger.info("MODIS connector initialized")
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch MODIS data."""
        if not self._client:
            return None
        
        all_data = []
        
        for aoi in self.areas_of_interest:
            for product in self.products:
                try:
                    data = await self._fetch_product(product, aoi)
                    if data:
                        all_data.extend(data)
                except Exception as e:
                    logger.error(f"Error fetching MODIS {product}: {e}")
                    continue
        
        return all_data if all_data else None
    
    async def _fetch_product(
        self,
        product: str,
        bbox: BoundingBox,
        days_back: int = 30,
    ) -> list[dict[str, Any]]:
        """Fetch specific MODIS product.
        
        Args:
            product: MODIS product name
            bbox: Area of interest
            days_back: Days to look back
        """
        try:
            # Calculate center point of bbox
            lat = (bbox.min_lat + bbox.max_lat) / 2
            lon = (bbox.min_lon + bbox.max_lon) / 2
            
            # Date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Build request URL
            url = f"{self.modis_base_url}/{product}/subset"
            params = {
                "latitude": lat,
                "longitude": lon,
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "kmAboveBelow": 25,  # 50km x 50km area
                "kmLeftRight": 25,
            }
            
            # Make request
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            results = []
            if "subset" in data:
                for item in data["subset"]:
                    parsed = self._parse_modis_data(item, product, bbox)
                    if parsed:
                        results.append(parsed)
                        self._store_modis_metadata(parsed, bbox)
            
            logger.info(f"Fetched {len(results)} MODIS {product} records")
            return results
        
        except Exception as e:
            logger.error(f"Error fetching MODIS product {product}: {e}")
            return []
    
    def _parse_modis_data(
        self,
        item: dict[str, Any],
        product: str,
        bbox: BoundingBox,
    ) -> dict[str, Any] | None:
        """Parse MODIS data item."""
        try:
            # Extract date
            calendar_date = item.get("calendar_date", "")
            if calendar_date:
                acquisition_date = datetime.strptime(calendar_date, "%Y-%m-%d")
            else:
                acquisition_date = datetime.utcnow()
            
            # Get bands/data
            bands = item.get("band", [])
            if isinstance(bands, dict):
                bands = [bands]
            
            band_names = [b.get("band", "") for b in bands]
            band_values = {}
            
            for band in bands:
                band_name = band.get("band", "")
                band_data = band.get("data", [])
                if band_data:
                    # Calculate statistics
                    values = [float(v) for v in band_data if v != -3000]  # -3000 is fill value
                    if values:
                        band_values[band_name] = {
                            "mean": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "count": len(values),
                        }
            
            return {
                "product": product,
                "acquisition_date": acquisition_date.isoformat(),
                "bbox": bbox.to_dict(),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "bands": band_names,
                "band_values": band_values,
                "resolution_meters": self._get_product_resolution(product),
                "provider": "MODIS",
                "satellite": item.get("satellite", "Terra/Aqua"),
                "metadata": item,
            }
        
        except Exception as e:
            logger.error(f"Error parsing MODIS data: {e}")
            return None
    
    def _get_product_resolution(self, product: str) -> float:
        """Get resolution for MODIS product."""
        resolutions = {
            "MOD09A1": 500,   # 500m
            "MOD13Q1": 250,   # 250m
            "MOD14A1": 1000,  # 1km
            "MOD11A1": 1000,  # 1km
        }
        return resolutions.get(product, 500)
    
    def _store_modis_metadata(
        self,
        data: dict[str, Any],
        bbox: BoundingBox,
    ) -> None:
        """Store MODIS metadata in satellite service."""
        try:
            acquisition_date = data.get("acquisition_date")
            if isinstance(acquisition_date, str):
                acquisition_date = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))
            
            image = SatelliteImage(
                image_id=uuid4(),
                provider=SatelliteProvider.MODIS,
                acquisition_date=acquisition_date,
                cloud_coverage=0,  # MODIS data is pre-processed
                resolution_meters=float(data.get("resolution_meters", 500)),
                bbox=bbox,
                bands=data.get("bands", []),
                metadata=data,
            )
            
            self.satellite_service.images[image.image_id] = image
            
        except Exception as e:
            logger.error(f"Error storing MODIS metadata: {e}")
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest MODIS data into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for record in data:
            try:
                await kafka.publish_osint_data(
                    source_type="satellite",
                    source_id=f"modis_{record['product']}_{record['acquisition_date']}",
                    content=f"MODIS {record['product']}: {record.get('satellite', 'Terra/Aqua')}",
                    metadata=record,
                )
                
                logger.debug(f"Ingested MODIS record: {record['product']}")
            
            except Exception as e:
                logger.error(f"Error ingesting MODIS data: {e}")
                continue
    
    async def get_fire_detection(
        self,
        bbox: BoundingBox,
        days_back: int = 7,
    ) -> list[dict[str, Any]]:
        """Get fire detection data from MODIS.
        
        Uses MOD14 Thermal Anomalies/Fire product.
        """
        product = "MOD14A1"
        fire_data = await self._fetch_product(product, bbox, days_back)
        
        # Filter for actual fire detections
        fires = []
        for record in fire_data:
            band_values = record.get("band_values", {})
            
            # Check for fire detection (FireMask band)
            fire_mask = band_values.get("FireMask", {})
            if fire_mask.get("max", 0) >= 7:  # 7-9 indicates fire
                fires.append({
                    "detection_date": record["acquisition_date"],
                    "location": {
                        "lat": record["latitude"],
                        "lon": record["longitude"],
                    },
                    "confidence": self._get_fire_confidence(fire_mask.get("max", 0)),
                    "fire_mask_value": fire_mask.get("max", 0),
                    "metadata": record,
                })
        
        logger.info(f"Detected {len(fires)} fire events")
        return fires
    
    def _get_fire_confidence(self, fire_mask_value: float) -> str:
        """Get fire confidence from FireMask value."""
        if fire_mask_value >= 9:
            return "HIGH"
        elif fire_mask_value >= 8:
            return "MEDIUM"
        elif fire_mask_value >= 7:
            return "LOW"
        else:
            return "NONE"
    
    async def get_vegetation_indices(
        self,
        bbox: BoundingBox,
        days_back: int = 30,
    ) -> list[dict[str, Any]]:
        """Get NDVI and EVI from MODIS.
        
        Uses MOD13 Vegetation Indices product.
        """
        product = "MOD13Q1"
        vi_data = await self._fetch_product(product, bbox, days_back)
        
        vegetation_indices = []
        for record in vi_data:
            band_values = record.get("band_values", {})
            
            ndvi = band_values.get("250m_16_days_NDVI", {})
            evi = band_values.get("250m_16_days_EVI", {})
            
            if ndvi or evi:
                vegetation_indices.append({
                    "date": record["acquisition_date"],
                    "location": {
                        "lat": record["latitude"],
                        "lon": record["longitude"],
                    },
                    "ndvi": {
                        "mean": ndvi.get("mean", 0) * 0.0001,  # Scale factor
                        "min": ndvi.get("min", 0) * 0.0001,
                        "max": ndvi.get("max", 0) * 0.0001,
                    } if ndvi else None,
                    "evi": {
                        "mean": evi.get("mean", 0) * 0.0001,
                        "min": evi.get("min", 0) * 0.0001,
                        "max": evi.get("max", 0) * 0.0001,
                    } if evi else None,
                    "metadata": record,
                })
        
        return vegetation_indices
    
    async def get_land_surface_temperature(
        self,
        bbox: BoundingBox,
        days_back: int = 14,
    ) -> list[dict[str, Any]]:
        """Get land surface temperature from MODIS.
        
        Uses MOD11 LST product.
        """
        product = "MOD11A1"
        lst_data = await self._fetch_product(product, bbox, days_back)
        
        temperatures = []
        for record in lst_data:
            band_values = record.get("band_values", {})
            
            lst_day = band_values.get("LST_Day_1km", {})
            lst_night = band_values.get("LST_Night_1km", {})
            
            if lst_day or lst_night:
                temperatures.append({
                    "date": record["acquisition_date"],
                    "location": {
                        "lat": record["latitude"],
                        "lon": record["longitude"],
                    },
                    "temperature_day_kelvin": {
                        "mean": lst_day.get("mean", 0) * 0.02,  # Scale factor
                        "min": lst_day.get("min", 0) * 0.02,
                        "max": lst_day.get("max", 0) * 0.02,
                    } if lst_day else None,
                    "temperature_night_kelvin": {
                        "mean": lst_night.get("mean", 0) * 0.02,
                        "min": lst_night.get("min", 0) * 0.02,
                        "max": lst_night.get("max", 0) * 0.02,
                    } if lst_night else None,
                    "metadata": record,
                })
        
        return temperatures
