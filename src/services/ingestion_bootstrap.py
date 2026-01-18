"""Bootstrap module to initialize all ingestion connectors with configuration.

This module sets up all data connectors based on environment configuration.
"""

import logging

from src.config.ingestion_config import (
    get_ingestion_config,
    get_newsapi_config,
    get_guardian_config,
    get_nytimes_config,
    get_social_config,
    get_weather_config,
    get_satellite_config,
)
from src.services.connectors.base import ConnectorConfig
from src.services.connectors.news_api import NewsAPIConnector
from src.services.connectors.guardian_api import GuardianAPIConnector
from src.services.connectors.nytimes_api import NYTimesAPIConnector
from src.services.connectors.social_media import SocialMediaConnector
from src.services.connectors.twitter_connector import TwitterConnector
from src.services.connectors.telegram_connector import TelegramConnector
from src.services.connectors.weather import WeatherAPIConnector
from src.services.ingestion_manager import get_ingestion_manager

logger = logging.getLogger(__name__)


def bootstrap_ingestion_system() -> None:
    """Initialize and register all data ingestion connectors.
    
    This function:
    1. Loads configuration from environment
    2. Creates connector instances
    3. Registers them with the ingestion manager
    """
    logger.info("Bootstrapping data ingestion system...")
    
    manager = get_ingestion_manager()
    system_config = get_ingestion_config()
    
    if not system_config.enabled:
        logger.warning("Ingestion system is disabled in configuration")
        return
    
    # 1. NewsAPI Connector
    newsapi_cfg = get_newsapi_config()
    if newsapi_cfg.enabled:
        try:
            connector_config = ConnectorConfig(
                name="NewsAPI",
                enabled=newsapi_cfg.enabled,
                max_requests_per_minute=newsapi_cfg.max_requests_per_minute,
                max_requests_per_hour=newsapi_cfg.max_requests_per_hour,
                poll_interval_seconds=newsapi_cfg.poll_interval_seconds,
                max_retries=system_config.default_max_retries,
                retry_delay_seconds=system_config.default_retry_delay,
                retry_backoff_factor=system_config.default_retry_backoff,
                circuit_breaker_threshold=system_config.default_circuit_breaker_threshold,
                circuit_breaker_timeout=system_config.default_circuit_breaker_timeout,
                connection_timeout=system_config.default_connection_timeout,
                read_timeout=system_config.default_read_timeout,
            )
            
            news_connector = NewsAPIConnector(
                api_key=newsapi_cfg.api_key,
                config=connector_config,
            )
            
            manager.register_connector("newsapi", news_connector)
            logger.info("✓ NewsAPI connector registered")
        except Exception as e:
            logger.error(f"Failed to register NewsAPI connector: {e}")
    
    # 2. The Guardian Open Platform Connector
    guardian_cfg = get_guardian_config()
    if guardian_cfg.enabled:
        try:
            connector_config = ConnectorConfig(
                name="GuardianAPI",
                enabled=guardian_cfg.enabled,
                max_requests_per_minute=guardian_cfg.max_requests_per_minute,
                max_requests_per_hour=guardian_cfg.max_requests_per_hour,
                max_requests_per_day=guardian_cfg.max_requests_per_day,
                poll_interval_seconds=guardian_cfg.poll_interval_seconds,
                max_retries=system_config.default_max_retries,
                retry_delay_seconds=system_config.default_retry_delay,
                retry_backoff_factor=system_config.default_retry_backoff,
                circuit_breaker_threshold=system_config.default_circuit_breaker_threshold,
                circuit_breaker_timeout=system_config.default_circuit_breaker_timeout,
                connection_timeout=system_config.default_connection_timeout,
                read_timeout=system_config.default_read_timeout,
            )
            
            guardian_connector = GuardianAPIConnector(
                api_key=guardian_cfg.api_key,
                config=connector_config,
            )
            
            manager.register_connector("guardian", guardian_connector)
            logger.info("✓ Guardian API connector registered")
        except Exception as e:
            logger.error(f"Failed to register Guardian API connector: {e}")
    
    # 3. New York Times API Connector
    nytimes_cfg = get_nytimes_config()
    if nytimes_cfg.enabled:
        try:
            connector_config = ConnectorConfig(
                name="NYTimesAPI",
                enabled=nytimes_cfg.enabled,
                max_requests_per_minute=nytimes_cfg.max_requests_per_minute,
                max_requests_per_hour=nytimes_cfg.max_requests_per_hour,
                max_requests_per_day=nytimes_cfg.max_requests_per_day,
                poll_interval_seconds=nytimes_cfg.poll_interval_seconds,
                max_retries=system_config.default_max_retries,
                retry_delay_seconds=system_config.default_retry_delay,
                retry_backoff_factor=system_config.default_retry_backoff,
                circuit_breaker_threshold=system_config.default_circuit_breaker_threshold,
                circuit_breaker_timeout=system_config.default_circuit_breaker_timeout,
                connection_timeout=system_config.default_connection_timeout,
                read_timeout=system_config.default_read_timeout,
            )
            
            nytimes_connector = NYTimesAPIConnector(
                api_key=nytimes_cfg.api_key,
                config=connector_config,
            )
            
            manager.register_connector("nytimes", nytimes_connector)
            logger.info("✓ NY Times API connector registered")
        except Exception as e:
            logger.error(f"Failed to register NY Times API connector: {e}")
    
    # 4. Weather API Connector (OpenWeatherMap)
    weather_cfg = get_weather_config()
    if weather_cfg.enabled:
        try:
            connector_config = ConnectorConfig(
                name="WeatherAPI",
                enabled=weather_cfg.enabled,
                max_requests_per_minute=weather_cfg.max_requests_per_minute,
                max_requests_per_hour=weather_cfg.max_requests_per_hour,
                poll_interval_seconds=weather_cfg.poll_interval_seconds,
                max_retries=system_config.default_max_retries,
                retry_delay_seconds=system_config.default_retry_delay,
                retry_backoff_factor=system_config.default_retry_backoff,
                circuit_breaker_threshold=system_config.default_circuit_breaker_threshold,
                circuit_breaker_timeout=system_config.default_circuit_breaker_timeout,
                connection_timeout=system_config.default_connection_timeout,
                read_timeout=system_config.default_read_timeout,
            )
            
            weather_connector = WeatherAPIConnector(
                api_key=weather_cfg.api_key,
                config=connector_config,
            )
            
            manager.register_connector("weather", weather_connector)
            logger.info("✓ Weather API connector registered")
        except Exception as e:
            logger.error(f"Failed to register Weather API connector: {e}")
    
    # 5. Social Media Connectors
    social_cfg = get_social_config()
    if social_cfg.enabled:
        connector_config = ConnectorConfig(
            name="SocialMedia",
            enabled=social_cfg.enabled,
            max_requests_per_minute=social_cfg.max_requests_per_minute,
            max_requests_per_hour=social_cfg.max_requests_per_hour,
            poll_interval_seconds=social_cfg.poll_interval_seconds,
            max_retries=system_config.default_max_retries,
            retry_delay_seconds=system_config.default_retry_delay,
            retry_backoff_factor=system_config.default_retry_backoff,
            circuit_breaker_threshold=system_config.default_circuit_breaker_threshold,
            circuit_breaker_timeout=system_config.default_circuit_breaker_timeout,
            connection_timeout=system_config.default_connection_timeout,
            read_timeout=system_config.default_read_timeout,
        )
        
        # 5a. Twitter/X Connector (if credentials provided)
        if social_cfg.twitter_bearer_token:
            try:
                twitter_connector = TwitterConnector(
                    bearer_token=social_cfg.twitter_bearer_token,
                    config=connector_config,
                )
                
                manager.register_connector("twitter", twitter_connector)
                logger.info("✓ Twitter/X connector registered")
            except Exception as e:
                logger.error(f"Failed to register Twitter connector: {e}")
        else:
            logger.info("Twitter connector skipped (no bearer token configured)")
        
        # 5b. Telegram Connector (if credentials provided)
        if social_cfg.telegram_bot_token and social_cfg.telegram_channels:
            try:
                telegram_connector = TelegramConnector(
                    bot_token=social_cfg.telegram_bot_token,
                    channels=social_cfg.telegram_channels,
                    config=connector_config,
                )
                
                manager.register_connector("telegram", telegram_connector)
                logger.info(f"✓ Telegram connector registered (monitoring {len(social_cfg.telegram_channels)} channels)")
            except Exception as e:
                logger.error(f"Failed to register Telegram connector: {e}")
        else:
            logger.info("Telegram connector skipped (no bot token or channels configured)")
        
        # 5c. Fallback to mock social media connector if no real APIs configured
        if not social_cfg.twitter_bearer_token and not social_cfg.telegram_bot_token:
            if social_cfg.use_mock_data:
                try:
                    social_connector = SocialMediaConnector(config=connector_config)
                    manager.register_connector("social_media_mock", social_connector)
                    logger.info("✓ Mock Social Media connector registered (fallback)")
                except Exception as e:
                    logger.error(f"Failed to register mock Social Media connector: {e}")
    
    # 6. Satellite Connectors (if enabled and configured)
    satellite_cfg = get_satellite_config()
    if satellite_cfg.enabled:
        logger.info("Satellite connectors are configured but require API subscriptions")
        # Would register satellite connectors here if API keys are provided
    
    logger.info(f"✓ Ingestion system bootstrapped with {len(manager._connectors)} connectors")


async def start_ingestion_system() -> None:
    """Start the entire ingestion system."""
    manager = get_ingestion_manager()
    await manager.start_all()


async def stop_ingestion_system() -> None:
    """Stop the entire ingestion system."""
    manager = get_ingestion_manager()
    await manager.stop_all()
