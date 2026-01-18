"""The Guardian Open Platform connector for news ingestion.

The Guardian offers free access to their content API with generous rate limits.
API Documentation: https://open-platform.theguardian.com/documentation/
"""

import logging
from typing import Any

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class GuardianAPIConnector(BaseConnector[list[dict[str, Any]]]):
    """Connector for The Guardian Open Platform.
    
    The Guardian provides free API access with:
    - 5,000 calls per day (developer tier)
    - 12 calls per second
    - Access to over 2.7 million pieces of content
    
    API: https://open-platform.theguardian.com/
    """

    def __init__(self, api_key: str, config: ConnectorConfig | None = None):
        """Initialize Guardian API connector."""
        if config is None:
            config = ConnectorConfig(
                name="GuardianAPI",
                max_requests_per_minute=60,  # Well under 12/sec limit
                max_requests_per_hour=720,
                max_requests_per_day=5000,  # Developer tier limit
                poll_interval_seconds=900,  # 15 minutes
            )
        
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://content.guardianapis.com"
        
        # Search queries for Afghanistan and regional security
        self.queries = [
            "Afghanistan",
            "Taliban",
            "Kabul",
            "Pakistan border",
            "Central Asia security",
            "Afghanistan humanitarian",
            "Kandahar",
            "Afghan refugees",
        ]
        
        # Sections to focus on
        self.sections = [
            "world/afghanistan",
            "world/asia",
            "world/middleeast",
        ]
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch articles from The Guardian."""
        if not self._client:
            return None
        
        all_articles = []
        
        # Search by queries
        for query in self.queries:
            try:
                response = await self._client.get(
                    f"{self.base_url}/search",
                    params={
                        "q": query,
                        "api-key": self.api_key,
                        "page-size": 10,  # Max per request
                        "order-by": "newest",
                        "show-fields": "headline,trailText,bodyText,byline,thumbnail,shortUrl",
                        "show-tags": "keyword",
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("response", {}).get("status") == "ok":
                    results = data.get("response", {}).get("results", [])
                    all_articles.extend(results)
                    logger.info(f"Fetched {len(results)} articles from Guardian for query: {query}")
                else:
                    logger.warning(f"Guardian API returned non-ok status: {data.get('response', {}).get('message')}")
            
            except Exception as e:
                logger.error(f"Error fetching Guardian articles for query '{query}': {e}")
                continue
        
        # Also fetch from specific sections
        for section in self.sections:
            try:
                response = await self._client.get(
                    f"{self.base_url}/search",
                    params={
                        "section": section,
                        "api-key": self.api_key,
                        "page-size": 10,
                        "order-by": "newest",
                        "show-fields": "headline,trailText,bodyText,byline,thumbnail,shortUrl",
                        "show-tags": "keyword",
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("response", {}).get("status") == "ok":
                    results = data.get("response", {}).get("results", [])
                    all_articles.extend(results)
                    logger.info(f"Fetched {len(results)} articles from Guardian section: {section}")
            
            except Exception as e:
                logger.error(f"Error fetching Guardian section '{section}': {e}")
                continue
        
        # Remove duplicates by web URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("webUrl", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"Guardian API: {len(unique_articles)} unique articles (from {len(all_articles)} total)")
        
        return unique_articles if unique_articles else None
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest Guardian articles into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for article in data:
            try:
                # Extract fields
                article_id = article.get("id", "unknown")
                fields = article.get("fields", {})
                tags = article.get("tags", [])
                
                # Build content
                headline = fields.get("headline", article.get("webTitle", ""))
                trail_text = fields.get("trailText", "")
                body_text = fields.get("bodyText", "")
                
                content_parts = [headline]
                if trail_text:
                    content_parts.append(trail_text)
                if body_text:
                    # Limit body text to first 1000 chars to avoid huge payloads
                    content_parts.append(body_text[:1000])
                
                content = "\n\n".join(content_parts)
                
                # Extract keywords from tags
                keywords = [tag.get("webTitle", "") for tag in tags if tag.get("type") == "keyword"]
                
                await kafka.publish_osint_data(
                    source_type="news",
                    source_id=f"guardian_{article_id}",
                    content=content,
                    metadata={
                        "source": "The Guardian",
                        "source_name": "The Guardian",
                        "section": article.get("sectionName"),
                        "section_id": article.get("sectionId"),
                        "byline": fields.get("byline"),
                        "url": article.get("webUrl"),
                        "short_url": fields.get("shortUrl"),
                        "thumbnail": fields.get("thumbnail"),
                        "published_at": article.get("webPublicationDate"),
                        "keywords": keywords,
                        "article_type": article.get("type"),
                        "pillar_name": article.get("pillarName"),
                    },
                )
                
                logger.debug(f"Ingested Guardian article: {headline[:60]}...")
            
            except Exception as e:
                logger.error(f"Error ingesting Guardian article: {e}")
                continue
