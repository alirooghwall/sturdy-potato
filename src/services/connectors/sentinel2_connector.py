"""Sentinel-2 Satellite Data Connector (ESA Copernicus).

Connects to ESA's Copernicus Open Access Hub (SciHub) to download
Sentinel-2 optical imagery for change detection and analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

from .base import BaseConnector, ConnectorConfig
from ..satellite_analysis import (
    SatelliteImage,
    SatelliteProvider,
    BoundingBox,
    get_satellite_service,
)


logger = logging.getLogger(__name__)


class Sentinel2Connector(BaseConnector[list[dict[str, Any]]]):
    """Sentinel-2 satellite data connector.
    
    Features:
    - 10m resolution multispectral imagery
    - 13 spectral bands
    - 5-day revisit time
    - Free and open data access
    - Global coverage
    
    Bands:
    - B02: Blue (490nm) - 10m
    - B03: Green (560nm) - 10m
    - B04: Red (665nm) - 10m
    - B08: NIR (842nm) - 10m
    - B05-B07, B8A, B11-B12: Various - 20m/60m
    """

    def __init__(
        self,
        username: str,
        password: str,
        areas_of_interest: list[BoundingBox] | None = None,
        config: ConnectorConfig | None = None,
    ):
        """Initialize Sentinel-2 connector.
        
        Args:
            username: Copernicus SciHub username
            password: Copernicus SciHub password
            areas_of_interest: List of bounding boxes to monitor
            config: Connector configuration
        """
        if config is None:
            config = ConnectorConfig(
                name="Sentinel-2",
                max_requests_per_minute=5,  # API rate limit
                max_requests_per_hour=100,
                poll_interval_seconds=86400,  # Daily checks
            )
        
        super().__init__(config)
        
        self.username = username
        self.password = password
        self.areas_of_interest = areas_of_interest or []
        
        # Initialize Sentinel API
        try:
            self.api = SentinelAPI(
                username,
                password,
                'https://scihub.copernicus.eu/dhus',
                show_progressbars=False,
            )
            logger.info("Sentinel-2 API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Sentinel-2 API: {e}")
            self.api = None
        
        # Sentinel-2 specific settings
        self.platform_name = "Sentinel-2"
        self.product_type = "S2MSI2A"  # Level-2A (atmospherically corrected)
        self.cloud_cover_max = 30  # Maximum cloud coverage percentage
        
        self.satellite_service = get_satellite_service()
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch Sentinel-2 imagery metadata."""
        if not self.api or not self._client:
            logger.warning("Sentinel-2 API not initialized")
            return None
        
        all_products = []
        
        # Query for each area of interest
        for aoi in self.areas_of_interest:
            try:
                products = await self._query_area(aoi)
                if products:
                    all_products.extend(products)
                    logger.info(f"Found {len(products)} Sentinel-2 products for AOI")
            except Exception as e:
                logger.error(f"Error querying Sentinel-2 for AOI: {e}")
                continue
        
        return all_products if all_products else None
    
    async def _query_area(
        self,
        bbox: BoundingBox,
        days_back: int = 7,
    ) -> list[dict[str, Any]]:
        """Query Sentinel-2 for a specific area.
        
        Args:
            bbox: Bounding box to query
            days_back: Number of days to look back
        """
        # Convert bbox to WKT format
        footprint = self._bbox_to_wkt(bbox)
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        date_range = (
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
        )
        
        # Query Sentinel Hub
        try:
            products = self.api.query(
                area=footprint,
                date=date_range,
                platformname=self.platform_name,
                producttype=self.product_type,
                cloudcoverpercentage=(0, self.cloud_cover_max),
            )
            
            logger.info(f"Found {len(products)} Sentinel-2 products")
            
            # Convert to our format
            product_list = []
            for product_id, product_info in products.items():
                product_data = self._parse_product(product_id, product_info, bbox)
                product_list.append(product_data)
                
                # Store in satellite service
                self._store_image_metadata(product_data, bbox)
            
            return product_list
        
        except Exception as e:
            logger.error(f"Error querying Sentinel-2: {e}")
            return []
    
    def _bbox_to_wkt(self, bbox: BoundingBox) -> str:
        """Convert bounding box to WKT polygon."""
        return (
            f"POLYGON(("
            f"{bbox.min_lon} {bbox.min_lat},"
            f"{bbox.max_lon} {bbox.min_lat},"
            f"{bbox.max_lon} {bbox.max_lat},"
            f"{bbox.min_lon} {bbox.max_lat},"
            f"{bbox.min_lon} {bbox.min_lat}"
            f"))"
        )
    
    def _parse_product(
        self,
        product_id: str,
        product_info: dict[str, Any],
        bbox: BoundingBox,
    ) -> dict[str, Any]:
        """Parse Sentinel-2 product information."""
        return {
            "product_id": product_id,
            "title": product_info.get("title", ""),
            "platform": "Sentinel-2",
            "instrument": product_info.get("instrumentshortname", "MSI"),
            "product_type": product_info.get("producttype", ""),
            "acquisition_date": product_info.get("beginposition"),
            "ingestion_date": product_info.get("ingestiondate"),
            "cloud_coverage": product_info.get("cloudcoverpercentage", 0),
            "size": product_info.get("size", ""),
            "footprint": product_info.get("footprint", ""),
            "download_url": product_info.get("link", ""),
            "thumbnail_url": product_info.get("link_icon", ""),
            "resolution_meters": 10,  # Best resolution for Sentinel-2
            "bands": [
                "B01", "B02", "B03", "B04", "B05", "B06", "B07",
                "B08", "B8A", "B09", "B10", "B11", "B12",
            ],
            "bbox": bbox.to_dict(),
        }
    
    def _store_image_metadata(
        self,
        product_data: dict[str, Any],
        bbox: BoundingBox,
    ) -> None:
        """Store image metadata in satellite service."""
        try:
            acquisition_date = product_data.get("acquisition_date")
            if isinstance(acquisition_date, str):
                acquisition_date = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))
            
            image = SatelliteImage(
                image_id=uuid4(),
                provider=SatelliteProvider.SENTINEL_2,
                acquisition_date=acquisition_date,
                cloud_coverage=float(product_data.get("cloud_coverage", 0)),
                resolution_meters=float(product_data.get("resolution_meters", 10)),
                bbox=bbox,
                bands=product_data.get("bands", []),
                thumbnail_url=product_data.get("thumbnail_url"),
                download_url=product_data.get("download_url"),
                metadata=product_data,
            )
            
            self.satellite_service.images[image.image_id] = image
            
        except Exception as e:
            logger.error(f"Error storing image metadata: {e}")
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest Sentinel-2 data into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for product in data:
            try:
                await kafka.publish_osint_data(
                    source_type="satellite",
                    source_id=f"sentinel2_{product['product_id']}",
                    content=f"Sentinel-2 imagery: {product['title']}",
                    metadata={
                        "provider": "Sentinel-2",
                        "product_id": product["product_id"],
                        "acquisition_date": product.get("acquisition_date"),
                        "cloud_coverage": product.get("cloud_coverage"),
                        "resolution_meters": product.get("resolution_meters"),
                        "bands": product.get("bands"),
                        "bbox": product.get("bbox"),
                        "download_url": product.get("download_url"),
                        "thumbnail_url": product.get("thumbnail_url"),
                    },
                )
                
                logger.debug(f"Ingested Sentinel-2 product: {product['product_id']}")
            
            except Exception as e:
                logger.error(f"Error ingesting Sentinel-2 data: {e}")
                continue
    
    def download_product(
        self,
        product_id: str,
        directory_path: str = "./data/sentinel2",
    ) -> str | None:
        """Download a Sentinel-2 product.
        
        Args:
            product_id: Product ID to download
            directory_path: Directory to save the product
        
        Returns:
            Path to downloaded file or None
        """
        if not self.api:
            logger.error("Sentinel-2 API not initialized")
            return None
        
        try:
            logger.info(f"Downloading Sentinel-2 product: {product_id}")
            result = self.api.download(product_id, directory_path=directory_path)
            
            if result:
                logger.info(f"Downloaded: {result}")
                return result.get("path")
            
            return None
        
        except Exception as e:
            logger.error(f"Error downloading product: {e}")
            return None
    
    def get_product_info(self, product_id: str) -> dict[str, Any] | None:
        """Get detailed product information.
        
        Args:
            product_id: Product ID
        
        Returns:
            Product information dictionary
        """
        if not self.api:
            return None
        
        try:
            return self.api.get_product_odata(product_id)
        except Exception as e:
            logger.error(f"Error getting product info: {e}")
            return None
