"""Twitter/X API v2 Integration for real-time social media monitoring.

Requires Twitter API v2 credentials:
- API Key
- API Secret
- Bearer Token
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class TwitterConnector(BaseConnector[List[Dict[str, Any]]]):
    """Twitter API v2 connector for ISR platform."""

    def __init__(self, bearer_token: str, config: ConnectorConfig | None = None):
        if config is None:
            config = ConnectorConfig(
                name="Twitter",
                max_requests_per_minute=15,
                max_requests_per_hour=300,
                poll_interval_seconds=600,  # 10 minutes
            )
        
        super().__init__(config)
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        
        # Search queries for Afghanistan
        self.search_queries = [
            "Afghanistan -is:retweet lang:en",
            "Taliban -is:retweet lang:en",
            "Kabul -is:retweet lang:en",
        ]
        
        logger.info("Twitter connector initialized")
    
    async def fetch_data(self) -> List[Dict[str, Any]] | None:
        """Fetch tweets from Twitter API."""
        if not self._client:
            return None
        
        all_tweets = []
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        
        for query in self.search_queries:
            try:
                response = await self._client.get(
                    f"{self.base_url}/tweets/search/recent",
                    headers=headers,
                    params={
                        "query": query,
                        "max_results": 10,
                        "tweet.fields": "created_at,author_id,public_metrics,entities,context_annotations",
                        "user.fields": "username,verified,public_metrics",
                        "expansions": "author_id",
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                tweets = data.get("data", [])
                users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
                
                # Enhance tweets with user data
                for tweet in tweets:
                    tweet["user"] = users.get(tweet["author_id"], {})
                    all_tweets.append(tweet)
                
                logger.info(f"Fetched {len(tweets)} tweets for query: {query}")
            
            except Exception as e:
                logger.error(f"Error fetching tweets for '{query}': {e}")
                continue
        
        return all_tweets if all_tweets else None
    
    async def ingest_data(self, data: List[Dict[str, Any]]) -> None:
        """Ingest tweets into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for tweet in data:
            try:
                await kafka.publish_osint_data(
                    source_type="social",
                    source_id=f"twitter_{tweet['id']}",
                    content=tweet.get("text", ""),
                    metadata={
                        "platform": "twitter",
                        "tweet_id": tweet["id"],
                        "author_id": tweet.get("author_id"),
                        "username": tweet.get("user", {}).get("username"),
                        "verified": tweet.get("user", {}).get("verified"),
                        "created_at": tweet.get("created_at"),
                        "metrics": tweet.get("public_metrics", {}),
                        "entities": tweet.get("entities", {}),
                    },
                )
                
                logger.debug(f"Ingested tweet: {tweet['id']}")
            
            except Exception as e:
                logger.error(f"Error ingesting tweet: {e}")
                continue
