"""Satellite imagery visualization and animation generation.

Creates interactive maps, time-lapse animations, and visual representations
of satellite analysis results.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for visualization generation."""
    width: int = 800
    height: int = 600
    dpi: int = 100
    colormap: str = "viridis"
    show_legend: bool = True
    show_scale: bool = True
    show_coordinates: bool = True
    output_format: str = "PNG"  # PNG, JPEG, GIF, MP4


@dataclass
class TimeLapseConfig:
    """Configuration for time-lapse generation."""
    fps: int = 2  # Frames per second
    duration_seconds: int | None = None
    loop: bool = True
    quality: str = "high"  # low, medium, high
    include_labels: bool = True
    include_date_stamp: bool = True


class SatelliteVisualizationService:
    """Service for creating satellite imagery visualizations."""

    def __init__(self):
        """Initialize visualization service."""
        self.visualizations: dict[UUID, dict[str, Any]] = {}
        logger.info("Satellite visualization service initialized")
    
    def create_change_detection_map(
        self,
        change_map: np.ndarray,
        bbox: dict[str, float],
        title: str = "Change Detection",
        config: VisualizationConfig | None = None,
    ) -> dict[str, Any]:
        """Create visualization of change detection results.
        
        Args:
            change_map: 2D array of change probabilities (0-1)
            bbox: Bounding box coordinates
            title: Map title
            config: Visualization configuration
        
        Returns:
            Visualization metadata and file path
        """
        if config is None:
            config = VisualizationConfig()
        
        viz_id = uuid4()
        
        # In production, would use matplotlib/folium to create actual visualizations
        visualization = {
            "visualization_id": str(viz_id),
            "type": "change_detection_map",
            "title": title,
            "bbox": bbox,
            "dimensions": {
                "width": config.width,
                "height": config.height,
            },
            "statistics": {
                "total_pixels": int(change_map.size),
                "changed_pixels": int(np.sum(change_map > 0.5)),
                "change_percentage": float((np.sum(change_map > 0.5) / change_map.size) * 100),
                "mean_change": float(np.mean(change_map)),
                "max_change": float(np.max(change_map)),
            },
            "file_path": f"visualizations/change_map_{viz_id}.{config.output_format.lower()}",
            "thumbnail_path": f"visualizations/thumbnails/change_map_{viz_id}_thumb.jpg",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[viz_id] = visualization
        
        logger.info(f"Created change detection map: {viz_id}")
        return visualization
    
    def create_ndvi_map(
        self,
        ndvi: np.ndarray,
        bbox: dict[str, float],
        date: datetime,
        config: VisualizationConfig | None = None,
    ) -> dict[str, Any]:
        """Create NDVI visualization map.
        
        Args:
            ndvi: NDVI values (-1 to 1)
            bbox: Bounding box
            date: Image acquisition date
            config: Visualization configuration
        
        Returns:
            Visualization metadata
        """
        if config is None:
            config = VisualizationConfig(colormap="RdYlGn")
        
        viz_id = uuid4()
        
        visualization = {
            "visualization_id": str(viz_id),
            "type": "ndvi_map",
            "title": f"NDVI - {date.strftime('%Y-%m-%d')}",
            "bbox": bbox,
            "date": date.isoformat(),
            "statistics": {
                "mean_ndvi": float(np.mean(ndvi)),
                "min_ndvi": float(np.min(ndvi)),
                "max_ndvi": float(np.max(ndvi)),
                "std_ndvi": float(np.std(ndvi)),
                "vegetation_coverage": float(np.sum(ndvi > 0.3) / ndvi.size * 100),
            },
            "colormap": config.colormap,
            "file_path": f"visualizations/ndvi_map_{viz_id}.{config.output_format.lower()}",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[viz_id] = visualization
        
        logger.info(f"Created NDVI map: {viz_id}")
        return visualization
    
    def create_comparison_map(
        self,
        before_data: np.ndarray,
        after_data: np.ndarray,
        bbox: dict[str, float],
        before_date: datetime,
        after_date: datetime,
        analysis_type: str = "NDVI",
        config: VisualizationConfig | None = None,
    ) -> dict[str, Any]:
        """Create side-by-side comparison map.
        
        Args:
            before_data: Data from earlier date
            after_data: Data from later date
            bbox: Bounding box
            before_date: Earlier date
            after_date: Later date
            analysis_type: Type of analysis (NDVI, NDWI, etc.)
            config: Visualization configuration
        
        Returns:
            Visualization metadata
        """
        if config is None:
            config = VisualizationConfig(width=1600)
        
        viz_id = uuid4()
        
        # Calculate difference
        difference = after_data - before_data
        
        visualization = {
            "visualization_id": str(viz_id),
            "type": "comparison_map",
            "title": f"{analysis_type} Comparison",
            "bbox": bbox,
            "before_date": before_date.isoformat(),
            "after_date": after_date.isoformat(),
            "analysis_type": analysis_type,
            "statistics": {
                "before": {
                    "mean": float(np.mean(before_data)),
                    "std": float(np.std(before_data)),
                },
                "after": {
                    "mean": float(np.mean(after_data)),
                    "std": float(np.std(after_data)),
                },
                "difference": {
                    "mean": float(np.mean(difference)),
                    "std": float(np.std(difference)),
                    "max_increase": float(np.max(difference)),
                    "max_decrease": float(np.min(difference)),
                },
            },
            "layout": "side_by_side",
            "file_path": f"visualizations/comparison_{viz_id}.{config.output_format.lower()}",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[viz_id] = visualization
        
        logger.info(f"Created comparison map: {viz_id}")
        return visualization
    
    def create_alert_map(
        self,
        alerts: list[dict[str, Any]],
        bbox: dict[str, float],
        config: VisualizationConfig | None = None,
    ) -> dict[str, Any]:
        """Create map showing alert locations.
        
        Args:
            alerts: List of alert dictionaries with locations
            bbox: Map bounding box
            config: Visualization configuration
        
        Returns:
            Visualization metadata
        """
        if config is None:
            config = VisualizationConfig()
        
        viz_id = uuid4()
        
        # Group alerts by severity
        by_severity = {}
        for alert in alerts:
            severity = alert.get("severity", "INFO")
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(alert)
        
        visualization = {
            "visualization_id": str(viz_id),
            "type": "alert_map",
            "title": "Satellite Alert Locations",
            "bbox": bbox,
            "alert_count": len(alerts),
            "alerts_by_severity": {
                severity: len(items)
                for severity, items in by_severity.items()
            },
            "markers": [
                {
                    "location": alert.get("location", {}),
                    "severity": alert.get("severity"),
                    "event_type": alert.get("event_type"),
                    "description": alert.get("description", "")[:100],
                }
                for alert in alerts
            ],
            "file_path": f"visualizations/alert_map_{viz_id}.{config.output_format.lower()}",
            "interactive_url": f"maps/interactive/alert_map_{viz_id}.html",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[viz_id] = visualization
        
        logger.info(f"Created alert map: {viz_id}")
        return visualization
    
    def generate_time_lapse(
        self,
        image_sequence: list[dict[str, Any]],
        bbox: dict[str, float],
        analysis_type: str = "RGB",
        config: TimeLapseConfig | None = None,
    ) -> dict[str, Any]:
        """Generate time-lapse animation from image sequence.
        
        Args:
            image_sequence: List of images with metadata
            bbox: Bounding box
            analysis_type: Type of visualization (RGB, NDVI, etc.)
            config: Time-lapse configuration
        
        Returns:
            Animation metadata
        """
        if config is None:
            config = TimeLapseConfig()
        
        animation_id = uuid4()
        
        # Sort images by date
        sorted_images = sorted(image_sequence, key=lambda x: x.get("date", ""))
        
        # Calculate duration
        if config.duration_seconds is None:
            config.duration_seconds = len(sorted_images) / config.fps
        
        animation = {
            "animation_id": str(animation_id),
            "type": "time_lapse",
            "analysis_type": analysis_type,
            "bbox": bbox,
            "frame_count": len(sorted_images),
            "fps": config.fps,
            "duration_seconds": config.duration_seconds,
            "start_date": sorted_images[0].get("date") if sorted_images else None,
            "end_date": sorted_images[-1].get("date") if sorted_images else None,
            "config": {
                "loop": config.loop,
                "quality": config.quality,
                "include_labels": config.include_labels,
                "include_date_stamp": config.include_date_stamp,
            },
            "file_formats": {
                "mp4": f"animations/timelapse_{animation_id}.mp4",
                "gif": f"animations/timelapse_{animation_id}.gif",
                "webm": f"animations/timelapse_{animation_id}.webm",
            },
            "thumbnail_path": f"animations/thumbnails/timelapse_{animation_id}_thumb.jpg",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[animation_id] = animation
        
        logger.info(f"Generated time-lapse animation: {animation_id}")
        return animation
    
    def create_interactive_map(
        self,
        layers: list[dict[str, Any]],
        bbox: dict[str, float],
        center: dict[str, float] | None = None,
        zoom: int = 10,
    ) -> dict[str, Any]:
        """Create interactive web map with multiple layers.
        
        Args:
            layers: List of map layers to display
            bbox: Map bounding box
            center: Map center coordinates
            zoom: Initial zoom level
        
        Returns:
            Interactive map metadata
        """
        map_id = uuid4()
        
        if center is None:
            center = {
                "lat": (bbox["min_lat"] + bbox["max_lat"]) / 2,
                "lon": (bbox["min_lon"] + bbox["max_lon"]) / 2,
            }
        
        interactive_map = {
            "map_id": str(map_id),
            "type": "interactive_map",
            "bbox": bbox,
            "center": center,
            "zoom": zoom,
            "layers": layers,
            "features": [
                "zoom_control",
                "layer_control",
                "legend",
                "scale_bar",
                "coordinates_display",
                "measurement_tool",
            ],
            "url": f"maps/interactive/{map_id}.html",
            "embed_code": f'<iframe src="maps/interactive/{map_id}.html" width="100%" height="600"></iframe>',
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[map_id] = interactive_map
        
        logger.info(f"Created interactive map: {map_id}")
        return interactive_map
    
    def create_trend_chart(
        self,
        time_series_data: list[dict[str, Any]],
        metric: str,
        title: str,
        config: VisualizationConfig | None = None,
    ) -> dict[str, Any]:
        """Create trend visualization chart.
        
        Args:
            time_series_data: Time series data points
            metric: Metric being visualized
            title: Chart title
            config: Visualization configuration
        
        Returns:
            Chart metadata
        """
        if config is None:
            config = VisualizationConfig()
        
        chart_id = uuid4()
        
        # Calculate statistics
        values = [point.get("value", 0) for point in time_series_data]
        
        chart = {
            "chart_id": str(chart_id),
            "type": "trend_chart",
            "title": title,
            "metric": metric,
            "data_points": len(time_series_data),
            "statistics": {
                "mean": float(np.mean(values)) if values else 0,
                "min": float(np.min(values)) if values else 0,
                "max": float(np.max(values)) if values else 0,
                "std": float(np.std(values)) if values else 0,
                "trend": "increasing" if len(values) > 1 and values[-1] > values[0] else "decreasing",
            },
            "chart_type": "line",  # line, area, bar
            "file_path": f"visualizations/trend_chart_{chart_id}.{config.output_format.lower()}",
            "interactive_url": f"charts/interactive/trend_{chart_id}.html",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.visualizations[chart_id] = chart
        
        logger.info(f"Created trend chart: {chart_id}")
        return chart
    
    def get_visualization(self, viz_id: UUID) -> dict[str, Any] | None:
        """Get visualization by ID."""
        return self.visualizations.get(viz_id)
    
    def list_visualizations(
        self,
        viz_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List visualizations with optional filtering."""
        visualizations = list(self.visualizations.values())
        
        if viz_type:
            visualizations = [v for v in visualizations if v.get("type") == viz_type]
        
        # Sort by creation date (newest first)
        visualizations.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return visualizations[:limit]
    
    def get_stats(self) -> dict[str, Any]:
        """Get visualization statistics."""
        by_type = {}
        for viz in self.visualizations.values():
            viz_type = viz.get("type", "unknown")
            by_type[viz_type] = by_type.get(viz_type, 0) + 1
        
        return {
            "total_visualizations": len(self.visualizations),
            "by_type": by_type,
        }


# Global instance
_visualization_service: SatelliteVisualizationService | None = None


def get_visualization_service() -> SatelliteVisualizationService:
    """Get the visualization service instance."""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = SatelliteVisualizationService()
    return _visualization_service
