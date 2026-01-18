"""Data ingestion connectors for external sources.

This module provides a framework for ingesting data from:
- News sources (NewsAPI, The Guardian, NY Times)
- Weather services (OpenWeatherMap)
- Social media (Twitter, Telegram, Reddit)
- Satellite providers (Planet Labs, Sentinel Hub, Maxar)
"""

from .base import BaseConnector, ConnectorStatus, ConnectorConfig
from .news_api import NewsAPIConnector
from .guardian_api import GuardianAPIConnector
from .nytimes_api import NYTimesAPIConnector
from .weather import WeatherAPIConnector
from .social_media import SocialMediaConnector

__all__ = [
    "BaseConnector",
    "ConnectorStatus",
    "ConnectorConfig",
    "NewsAPIConnector",
    "GuardianAPIConnector",
    "NYTimesAPIConnector",
    "WeatherAPIConnector",
    "SocialMediaConnector",
]
