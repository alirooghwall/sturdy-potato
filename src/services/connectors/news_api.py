"""NewsAPI connector for real-time news ingestion.

Ingests news articles from NewsAPI.org related to Afghanistan and regional conflicts.
"""

import logging
from typing import Any

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class NewsAPIConnector(BaseConnector[list[dict[str, Any]]]):
    """Connector for NewsAPI.org.
    
    Fetches news articles about Afghanistan, terrorism, and regional conflicts.
    """

    def __init__(self, api_key: str, config: ConnectorConfig | None = None):
        """Initialize NewsAPI connector."""
        if config is None:
            config = ConnectorConfig(
                name="NewsAPI",
                max_requests_per_minute=5,  # Free tier limit
                max_requests_per_hour=100,
                poll_interval_seconds=900,  # 15 minutes
            )
        
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        
        # Search queries for Afghanistan-related news
        self.queries = [
            "Afghanistan",
            "Taliban",
            "Kabul",
            "Kandahar",
            "Pakistan border",
            "Central Asia conflict",
        ]
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch news articles from NewsAPI."""
        if not self._client:
            return None
        
        all_articles = []
        
        for query in self.queries:
            try:
                response = await self._client.get(
                    f"{self.base_url}/everything",
                    params={
                        "q": query,
                        "apiKey": self.api_key,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 10,
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "ok":
                    articles = data.get("articles", [])
                    all_articles.extend(articles)
                    logger.info(f"Fetched {len(articles)} articles for query: {query}")
                else:
                    logger.warning(f"NewsAPI returned error: {data.get('message')}")
            
            except Exception as e:
                logger.error(f"Error fetching news for query '{query}': {e}")
                continue
        
        return all_articles if all_articles else None
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest news articles into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus, MessageTopic
        
        kafka = get_kafka_bus()
        
        for article in data:
            try:
                # Extract relevant fields
                source_id = article.get("source", {}).get("id", "unknown")
                source_name = article.get("source", {}).get("name", "Unknown")
                
                await kafka.publish_osint_data(
                    source_type="news",
                    source_id=f"newsapi_{source_id}",
                    content=article.get("title", "") + "\n\n" + article.get("description", ""),
                    metadata={
                        "source_name": source_name,
                        "author": article.get("author"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "content": article.get("content"),
                        "url_to_image": article.get("urlToImage"),
                    },
                )
                
                logger.debug(f"Ingested news article: {article.get('title')}")
            
            except Exception as e:
                logger.error(f"Error ingesting article: {e}")
                continue
