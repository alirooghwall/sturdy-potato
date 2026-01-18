"""New York Times API connector for news ingestion.

NYT provides comprehensive news coverage with their Developer API.
API Documentation: https://developer.nytimes.com/
"""

import logging
from typing import Any

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class NYTimesAPIConnector(BaseConnector[list[dict[str, Any]]]):
    """Connector for New York Times API.
    
    NYT provides multiple APIs:
    - Article Search API: Search 170+ years of articles
    - Top Stories API: Current top stories by section
    - Most Popular API: Most viewed/shared articles
    
    Rate Limits:
    - 500 requests per day (developer tier)
    - 5 requests per minute
    
    API: https://developer.nytimes.com/
    """

    def __init__(self, api_key: str, config: ConnectorConfig | None = None):
        """Initialize NYTimes API connector."""
        if config is None:
            config = ConnectorConfig(
                name="NYTimesAPI",
                max_requests_per_minute=5,  # API limit
                max_requests_per_hour=60,
                max_requests_per_day=500,  # Developer tier limit
                poll_interval_seconds=1800,  # 30 minutes
            )
        
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://api.nytimes.com/svc"
        
        # Search queries for Afghanistan coverage
        self.queries = [
            "Afghanistan",
            "Taliban",
            "Kabul",
            "Afghan",
            "Pakistan Afghanistan",
            "Central Asia",
        ]
        
        # Sections for top stories
        self.top_story_sections = [
            "world",
            "politics",
        ]
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch articles from NYTimes API."""
        if not self._client:
            return None
        
        all_articles = []
        
        # 1. Fetch from Article Search API
        for query in self.queries:
            try:
                response = await self._client.get(
                    f"{self.base_url}/search/v2/articlesearch.json",
                    params={
                        "q": query,
                        "api-key": self.api_key,
                        "sort": "newest",
                        "page": 0,
                        # Filter to recent articles (last 30 days)
                        "begin_date": self._get_date_filter(30),
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "OK":
                    docs = data.get("response", {}).get("docs", [])
                    for doc in docs:
                        doc["_source_api"] = "article_search"
                    all_articles.extend(docs)
                    logger.info(f"Fetched {len(docs)} articles from NYT Article Search for: {query}")
                else:
                    logger.warning(f"NYT API returned non-OK status: {data.get('message')}")
            
            except Exception as e:
                logger.error(f"Error fetching NYT articles for query '{query}': {e}")
                continue
        
        # 2. Fetch Top Stories (world and politics sections)
        for section in self.top_story_sections:
            try:
                response = await self._client.get(
                    f"{self.base_url}/topstories/v2/{section}.json",
                    params={
                        "api-key": self.api_key,
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "OK":
                    results = data.get("results", [])
                    # Filter for Afghanistan-related stories
                    filtered = [
                        r for r in results
                        if any(
                            keyword.lower() in (r.get("title", "") + r.get("abstract", "")).lower()
                            for keyword in ["afghanistan", "taliban", "kabul", "afghan"]
                        )
                    ]
                    for result in filtered:
                        result["_source_api"] = "top_stories"
                    all_articles.extend(filtered)
                    logger.info(f"Fetched {len(filtered)} relevant top stories from NYT section: {section}")
            
            except Exception as e:
                logger.error(f"Error fetching NYT top stories for section '{section}': {e}")
                continue
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("web_url") or article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"NYT API: {len(unique_articles)} unique articles (from {len(all_articles)} total)")
        
        return unique_articles if unique_articles else None
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest NYTimes articles into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for article in data:
            try:
                source_api = article.get("_source_api", "unknown")
                
                # Different field structures for different APIs
                if source_api == "article_search":
                    article_id = article.get("_id", "unknown")
                    headline = article.get("headline", {}).get("main", "")
                    abstract = article.get("abstract", "")
                    lead_paragraph = article.get("lead_paragraph", "")
                    snippet = article.get("snippet", "")
                    
                    content = f"{headline}\n\n{abstract or lead_paragraph or snippet}"
                    
                    metadata = {
                        "source": "New York Times",
                        "source_name": "The New York Times",
                        "section": article.get("section_name"),
                        "byline": article.get("byline", {}).get("original"),
                        "url": article.get("web_url"),
                        "published_at": article.get("pub_date"),
                        "document_type": article.get("document_type"),
                        "news_desk": article.get("news_desk"),
                        "type_of_material": article.get("type_of_material"),
                        "word_count": article.get("word_count"),
                        "keywords": [
                            kw.get("value")
                            for kw in article.get("keywords", [])
                            if kw.get("value")
                        ],
                    }
                
                elif source_api == "top_stories":
                    article_id = article.get("uri", article.get("url", "")).split("/")[-1]
                    headline = article.get("title", "")
                    abstract = article.get("abstract", "")
                    
                    content = f"{headline}\n\n{abstract}"
                    
                    multimedia = article.get("multimedia", [])
                    image_url = None
                    if multimedia:
                        # Get largest image
                        large_images = [m for m in multimedia if m.get("format") == "superJumbo"]
                        if large_images:
                            image_url = large_images[0].get("url")
                    
                    metadata = {
                        "source": "New York Times",
                        "source_name": "The New York Times",
                        "section": article.get("section"),
                        "subsection": article.get("subsection"),
                        "byline": article.get("byline"),
                        "url": article.get("url"),
                        "short_url": article.get("short_url"),
                        "published_at": article.get("published_date"),
                        "updated_at": article.get("updated_date"),
                        "image_url": image_url,
                        "item_type": article.get("item_type"),
                        "des_facet": article.get("des_facet", []),
                        "org_facet": article.get("org_facet", []),
                        "per_facet": article.get("per_facet", []),
                        "geo_facet": article.get("geo_facet", []),
                    }
                
                else:
                    logger.warning(f"Unknown NYT source API: {source_api}")
                    continue
                
                await kafka.publish_osint_data(
                    source_type="news",
                    source_id=f"nytimes_{article_id}",
                    content=content,
                    metadata=metadata,
                )
                
                logger.debug(f"Ingested NYT article: {headline[:60]}...")
            
            except Exception as e:
                logger.error(f"Error ingesting NYT article: {e}")
                continue
    
    def _get_date_filter(self, days_ago: int) -> str:
        """Get date filter in YYYYMMDD format for N days ago."""
        from datetime import datetime, timedelta
        
        date = datetime.utcnow() - timedelta(days=days_ago)
        return date.strftime("%Y%m%d")
