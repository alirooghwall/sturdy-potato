"""Configuration management for data ingestion connectors.

Provides centralized configuration for all data sources with environment variable support.
"""

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NewsAPIConfig(BaseSettings):
    """NewsAPI connector configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="NEWSAPI_",
        env_file=".env",
        case_sensitive=False,
    )
    
    enabled: bool = True
    api_key: str = Field(default="demo_key", description="NewsAPI.org API key")
    max_requests_per_minute: int = 5
    max_requests_per_hour: int = 100
    poll_interval_seconds: int = 900  # 15 minutes


class GuardianAPIConfig(BaseSettings):
    """The Guardian Open Platform connector configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="GUARDIAN_",
        env_file=".env",
        case_sensitive=False,
    )
    
    enabled: bool = True
    api_key: str = Field(default="demo_key", description="Guardian Open Platform API key")
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 720
    max_requests_per_day: int = 5000  # Developer tier
    poll_interval_seconds: int = 900  # 15 minutes


class NYTimesAPIConfig(BaseSettings):
    """New York Times API connector configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="NYTIMES_",
        env_file=".env",
        case_sensitive=False,
    )
    
    enabled: bool = True
    api_key: str = Field(default="demo_key", description="NYTimes Developer API key")
    max_requests_per_minute: int = 5  # API limit
    max_requests_per_hour: int = 60
    max_requests_per_day: int = 500  # Developer tier
    poll_interval_seconds: int = 1800  # 30 minutes


class WeatherAPIConfig(BaseSettings):
    """Weather API connector configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="WEATHER_",
        env_file=".env",
        case_sensitive=False,
    )
    
    enabled: bool = True
    api_key: str = Field(default="demo_key", description="OpenWeatherMap API key")
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    poll_interval_seconds: int = 1800  # 30 minutes


class SocialMediaConfig(BaseSettings):
    """Social media connector configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="SOCIAL_",
        env_file=".env",
        case_sensitive=False,
    )
    
    enabled: bool = True
    
    # Twitter/X API (if available)
    twitter_api_key: str = Field(default="", description="Twitter API key")
    twitter_api_secret: str = Field(default="", description="Twitter API secret")
    twitter_bearer_token: str = Field(default="", description="Twitter Bearer token")
    
    # Telegram Bot API (if available)
    telegram_bot_token: str = Field(default="", description="Telegram bot token")
    telegram_channels: list[str] = Field(
        default_factory=list,
        description="List of Telegram channels to monitor"
    )
    
    # Configuration
    max_requests_per_minute: int = 15
    max_requests_per_hour: int = 500
    poll_interval_seconds: int = 600  # 10 minutes
    use_mock_data: bool = True  # Use mock data if no API keys


class SatelliteConfig(BaseSettings):
    """Satellite data connector configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="SATELLITE_",
        env_file=".env",
        case_sensitive=False,
    )
    
    enabled: bool = False  # Disabled by default (requires subscriptions)
    
    # Planet Labs
    planet_api_key: str = Field(default="", description="Planet Labs API key")
    
    # Sentinel Hub
    sentinel_client_id: str = Field(default="", description="Sentinel Hub client ID")
    sentinel_client_secret: str = Field(default="", description="Sentinel Hub client secret")
    
    # Maxar
    maxar_api_key: str = Field(default="", description="Maxar API key")
    
    # Configuration
    max_requests_per_minute: int = 10
    max_requests_per_hour: int = 100
    poll_interval_seconds: int = 3600  # 1 hour


class IngestionSystemConfig(BaseSettings):
    """Overall ingestion system configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="INGESTION_",
        env_file=".env",
        case_sensitive=False,
    )
    
    # System-wide settings
    enabled: bool = True
    auto_start: bool = False  # Don't auto-start by default
    health_check_interval: int = 60  # seconds
    
    # Retry settings (default for all connectors)
    default_max_retries: int = 3
    default_retry_delay: int = 1
    default_retry_backoff: float = 2.0
    
    # Circuit breaker settings
    default_circuit_breaker_threshold: int = 5
    default_circuit_breaker_timeout: int = 60
    
    # Timeouts
    default_connection_timeout: int = 10
    default_read_timeout: int = 30


@lru_cache
def get_newsapi_config() -> NewsAPIConfig:
    """Get NewsAPI configuration."""
    return NewsAPIConfig()


@lru_cache
def get_guardian_config() -> GuardianAPIConfig:
    """Get Guardian API configuration."""
    return GuardianAPIConfig()


@lru_cache
def get_nytimes_config() -> NYTimesAPIConfig:
    """Get NY Times API configuration."""
    return NYTimesAPIConfig()


@lru_cache
def get_weather_config() -> WeatherAPIConfig:
    """Get Weather API configuration."""
    return WeatherAPIConfig()


@lru_cache
def get_social_config() -> SocialMediaConfig:
    """Get Social Media configuration."""
    return SocialMediaConfig()


@lru_cache
def get_satellite_config() -> SatelliteConfig:
    """Get Satellite configuration."""
    return SatelliteConfig()


@lru_cache
def get_ingestion_config() -> IngestionSystemConfig:
    """Get overall ingestion system configuration."""
    return IngestionSystemConfig()


def get_all_configs() -> dict[str, Any]:
    """Get all ingestion configurations."""
    return {
        "system": get_ingestion_config().model_dump(),
        "newsapi": get_newsapi_config().model_dump(exclude={"api_key"}),
        "guardian": get_guardian_config().model_dump(exclude={"api_key"}),
        "nytimes": get_nytimes_config().model_dump(exclude={"api_key"}),
        "weather": get_weather_config().model_dump(exclude={"api_key"}),
        "social": get_social_config().model_dump(
            exclude={"twitter_api_key", "twitter_api_secret", "twitter_bearer_token", "telegram_bot_token"}
        ),
        "satellite": get_satellite_config().model_dump(
            exclude={"planet_api_key", "sentinel_client_id", "sentinel_client_secret", "maxar_api_key"}
        ),
    }
