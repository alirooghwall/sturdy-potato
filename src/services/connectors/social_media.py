"""Social media connector for OSINT data collection.

Mock implementation for social media monitoring.
In production, this would integrate with Twitter API, Telegram, etc.
"""

import logging
import random
from typing import Any

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class SocialMediaConnector(BaseConnector[list[dict[str, Any]]]):
    """Connector for social media monitoring.
    
    This is a mock implementation that generates sample social media posts.
    In production, integrate with:
    - Twitter/X API (v2)
    - Telegram Bot API
    - Reddit API
    - Facebook/Meta API
    """

    def __init__(self, config: ConnectorConfig | None = None):
        """Initialize social media connector."""
        if config is None:
            config = ConnectorConfig(
                name="SocialMedia",
                max_requests_per_minute=15,
                max_requests_per_hour=500,
                poll_interval_seconds=600,  # 10 minutes
            )
        
        super().__init__(config)
        
        # Sample posts for demonstration
        self.sample_topics = [
            "Kabul city security situation",
            "Border crossing delays at Torkham",
            "Humanitarian aid distribution in Herat",
            "Economic challenges in Afghanistan",
            "Education access for girls",
            "Healthcare situation in rural areas",
            "Infrastructure development projects",
            "Agricultural production updates",
        ]
        
        self.sample_sentiments = ["positive", "negative", "neutral", "concerned"]
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch social media posts (mock implementation)."""
        # In production, this would call real APIs:
        # - Twitter: GET /2/tweets/search/recent
        # - Telegram: getUpdates from monitored channels
        # - Reddit: /r/afghanistan/new.json
        
        # For now, generate mock data
        posts = []
        
        for _ in range(random.randint(5, 15)):
            topic = random.choice(self.sample_topics)
            sentiment = random.choice(self.sample_sentiments)
            
            post = {
                "id": f"post_{random.randint(100000, 999999)}",
                "platform": random.choice(["twitter", "telegram", "reddit"]),
                "author": f"user_{random.randint(1000, 9999)}",
                "content": f"Discussion about: {topic}",
                "timestamp": self._get_mock_timestamp(),
                "sentiment": sentiment,
                "engagement": {
                    "likes": random.randint(0, 1000),
                    "shares": random.randint(0, 100),
                    "comments": random.randint(0, 50),
                },
                "location": random.choice([
                    "Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", None
                ]),
                "hashtags": self._generate_hashtags(topic),
            }
            
            posts.append(post)
        
        logger.info(f"Generated {len(posts)} mock social media posts")
        return posts
    
    async def ingest_data(self, data: list[dict[str, Any]]) -> None:
        """Ingest social media posts into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for post in data:
            try:
                await kafka.publish_osint_data(
                    source_type="social",
                    source_id=f"{post['platform']}_{post['id']}",
                    content=post["content"],
                    metadata={
                        "platform": post["platform"],
                        "author": post["author"],
                        "timestamp": post["timestamp"],
                        "sentiment": post["sentiment"],
                        "engagement": post["engagement"],
                        "location": post["location"],
                        "hashtags": post["hashtags"],
                    },
                )
                
                logger.debug(f"Ingested social media post: {post['id']}")
            
            except Exception as e:
                logger.error(f"Error ingesting social media post: {e}")
                continue
    
    def _get_mock_timestamp(self) -> str:
        """Generate a mock timestamp."""
        from datetime import datetime, timedelta
        import random
        
        now = datetime.utcnow()
        offset = timedelta(hours=random.randint(0, 24))
        return (now - offset).isoformat() + "Z"
    
    def _generate_hashtags(self, topic: str) -> list[str]:
        """Generate relevant hashtags."""
        hashtags = []
        
        if "Kabul" in topic:
            hashtags.append("#Kabul")
        if "security" in topic:
            hashtags.extend(["#Security", "#Safety"])
        if "humanitarian" in topic:
            hashtags.extend(["#Humanitarian", "#Aid"])
        if "economic" in topic:
            hashtags.extend(["#Economy", "#Afghanistan"])
        
        # Always add general Afghanistan tag
        hashtags.append("#Afghanistan")
        
        return list(set(hashtags))
