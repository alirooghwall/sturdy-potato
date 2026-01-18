"""Weather API connector for meteorological data.

Ingests weather data for key Afghanistan locations to support operational planning.
"""

import logging
from typing import Any

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class WeatherAPIConnector(BaseConnector[dict[str, Any]]):
    """Connector for OpenWeatherMap API.
    
    Fetches current weather and forecasts for major Afghanistan cities and strategic locations.
    
    OpenWeatherMap provides:
    - Current weather data
    - 5-day / 3-hour forecast
    - Air quality data
    - Weather alerts
    
    Rate Limits (Free Tier):
    - 60 calls per minute
    - 1,000,000 calls per month
    
    API: https://openweathermap.org/api
    """

    def __init__(self, api_key: str, config: ConnectorConfig | None = None):
        """Initialize Weather API connector."""
        if config is None:
            config = ConnectorConfig(
                name="OpenWeatherMap",
                max_requests_per_minute=60,
                max_requests_per_hour=1000,
                max_requests_per_day=10000,
                poll_interval_seconds=1800,  # 30 minutes
            )
        
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Key Afghanistan locations with strategic importance
        self.locations = [
            {"name": "Kabul", "lat": 34.5553, "lon": 69.2075, "importance": "capital"},
            {"name": "Kandahar", "lat": 31.6289, "lon": 65.7372, "importance": "major_city"},
            {"name": "Herat", "lat": 34.3482, "lon": 62.2046, "importance": "major_city"},
            {"name": "Mazar-i-Sharif", "lat": 36.7099, "lon": 67.1101, "importance": "major_city"},
            {"name": "Jalalabad", "lat": 34.4287, "lon": 70.4531, "importance": "border_region"},
            {"name": "Kunduz", "lat": 36.7286, "lon": 68.8578, "importance": "strategic"},
            {"name": "Lashkar Gah", "lat": 31.5830, "lon": 64.3610, "importance": "regional"},
            {"name": "Ghazni", "lat": 33.5497, "lon": 68.4173, "importance": "strategic"},
            {"name": "Torkham Border", "lat": 34.0742, "lon": 71.1533, "importance": "border_crossing"},
            {"name": "Spin Boldak", "lat": 31.0090, "lon": 66.3904, "importance": "border_crossing"},
        ]
    
    async def fetch_data(self) -> dict[str, Any] | None:
        """Fetch weather data for all locations.
        
        Fetches both current weather and 5-day forecast for comprehensive coverage.
        """
        if not self._client:
            return None
        
        weather_data = {}
        
        for location in self.locations:
            try:
                # 1. Fetch current weather
                current_response = await self._client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "appid": self.api_key,
                        "units": "metric",
                    },
                )
                current_response.raise_for_status()
                current_data = current_response.json()
                
                # 2. Fetch 5-day forecast (optional, can be disabled to save API calls)
                try:
                    forecast_response = await self._client.get(
                        f"{self.base_url}/forecast",
                        params={
                            "lat": location["lat"],
                            "lon": location["lon"],
                            "appid": self.api_key,
                            "units": "metric",
                            "cnt": 8,  # Next 24 hours (3-hour intervals)
                        },
                    )
                    forecast_response.raise_for_status()
                    forecast_data = forecast_response.json()
                except Exception as e:
                    logger.warning(f"Could not fetch forecast for {location['name']}: {e}")
                    forecast_data = None
                
                # 3. Fetch air quality data (if available)
                try:
                    air_quality_response = await self._client.get(
                        f"{self.base_url}/air_pollution",
                        params={
                            "lat": location["lat"],
                            "lon": location["lon"],
                            "appid": self.api_key,
                        },
                    )
                    air_quality_response.raise_for_status()
                    air_quality_data = air_quality_response.json()
                except Exception as e:
                    logger.debug(f"Air quality data not available for {location['name']}: {e}")
                    air_quality_data = None
                
                # Combine all data
                weather_data[location["name"]] = {
                    "location": location,
                    "current": current_data,
                    "forecast": forecast_data,
                    "air_quality": air_quality_data,
                }
                
                logger.debug(
                    f"Fetched weather for {location['name']}: "
                    f"{current_data['main']['temp']}°C, {current_data['weather'][0]['description']}"
                )
            
            except Exception as e:
                logger.error(f"Error fetching weather for {location['name']}: {e}")
                continue
        
        return weather_data if weather_data else None
    
    async def ingest_data(self, data: dict[str, Any]) -> None:
        """Ingest weather data into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for location_name, weather_package in data.items():
            try:
                location_info = weather_package["location"]
                current = weather_package["current"]
                forecast = weather_package.get("forecast")
                air_quality = weather_package.get("air_quality")
                
                # Prepare comprehensive weather data
                sensor_data = {
                    "location": location_name,
                    "importance": location_info.get("importance", "unknown"),
                    "coordinates": {
                        "lat": current["coord"]["lat"],
                        "lon": current["coord"]["lon"],
                    },
                    # Current conditions
                    "current": {
                        "temperature": current["main"]["temp"],
                        "feels_like": current["main"]["feels_like"],
                        "temp_min": current["main"]["temp_min"],
                        "temp_max": current["main"]["temp_max"],
                        "humidity": current["main"]["humidity"],
                        "pressure": current["main"]["pressure"],
                        "wind_speed": current["wind"]["speed"],
                        "wind_direction": current["wind"].get("deg"),
                        "wind_gust": current["wind"].get("gust"),
                        "clouds": current["clouds"]["all"],
                        "visibility": current.get("visibility"),
                        "conditions": current["weather"][0]["main"],
                        "description": current["weather"][0]["description"],
                        "icon": current["weather"][0]["icon"],
                        "timestamp": current.get("dt"),
                        "sunrise": current["sys"].get("sunrise"),
                        "sunset": current["sys"].get("sunset"),
                    },
                }
                
                # Add forecast data if available
                if forecast:
                    forecast_list = forecast.get("list", [])
                    sensor_data["forecast"] = [
                        {
                            "timestamp": item["dt"],
                            "temperature": item["main"]["temp"],
                            "conditions": item["weather"][0]["main"],
                            "description": item["weather"][0]["description"],
                            "wind_speed": item["wind"]["speed"],
                            "precipitation_probability": item.get("pop", 0),
                            "rain_3h": item.get("rain", {}).get("3h", 0),
                            "snow_3h": item.get("snow", {}).get("3h", 0),
                        }
                        for item in forecast_list[:8]  # Next 24 hours
                    ]
                
                # Add air quality data if available
                if air_quality and "list" in air_quality and air_quality["list"]:
                    aqi_data = air_quality["list"][0]
                    sensor_data["air_quality"] = {
                        "aqi": aqi_data["main"]["aqi"],  # 1-5 scale
                        "components": aqi_data.get("components", {}),
                    }
                
                await kafka.publish_sensor_data(
                    sensor_type="ground",
                    sensor_id=f"openweathermap_{location_name.lower().replace(' ', '_')}",
                    data=sensor_data,
                )
                
                logger.debug(
                    f"Ingested comprehensive weather data for {location_name} "
                    f"(current + {len(sensor_data.get('forecast', []))} forecast points)"
                )
            
            except Exception as e:
                logger.error(f"Error ingesting weather for {location_name}: {e}")
                continue
