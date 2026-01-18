"""Stream processing pipeline for ISR Platform.

Provides real-time data transformation, enrichment, and analytics.
Implements ETL (Extract, Transform, Load) logic for incoming data streams.

Now includes ML-powered processing:
- NER with transformers
- Sentiment analysis with transformers
- Threat detection with ensemble models
- Topic classification
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Coroutine
from uuid import uuid4

from src.services.kafka_bus_real import (
    KafkaMessage,
    MessageTopic,
    get_kafka_bus,
)

# Import ML services (lazy loading to avoid startup delays)
_ml_services_loaded = False
_ner_service = None
_sentiment_service = None
_threat_service = None
_classification_service = None

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


# Type alias for stream processors
StreamProcessor = Callable[[KafkaMessage], Coroutine[Any, Any, KafkaMessage | None]]


@dataclass
class ProcessingStats:
    """Statistics for stream processing."""
    messages_processed: int = 0
    messages_enriched: int = 0
    messages_filtered: int = 0
    errors: int = 0
    processing_time_total: float = 0.0
    
    @property
    def avg_processing_time(self) -> float:
        """Average processing time per message."""
        if self.messages_processed == 0:
            return 0.0
        return self.processing_time_total / self.messages_processed


class StreamProcessingPipeline:
    """Real-time stream processing pipeline.
    
    Features:
    - Data cleansing and normalization
    - Entity extraction and enrichment
    - Geospatial processing
    - Threat scoring and classification
    - Anomaly detection
    - Data aggregation and windowing
    """

    def __init__(self, use_ml: bool = True):
        """Initialize stream processing pipeline.
        
        Args:
            use_ml: Whether to use ML models (requires torch, transformers)
        """
        self._kafka = get_kafka_bus()
        self._running = False
        self._processors: dict[MessageTopic, list[StreamProcessor]] = {}
        self._stats: dict[MessageTopic, ProcessingStats] = {}
        self._use_ml = use_ml
        
        # ML services will be lazy loaded
        if self._use_ml:
            logger.info("ML-powered processing enabled")
        else:
            logger.info("Using rule-based processing (ML disabled)")
    
    async def start(self) -> None:
        """Start the processing pipeline."""
        if self._running:
            return
        
        logger.info("Starting stream processing pipeline...")
        
        # Ensure Kafka is connected
        await self._kafka.connect()
        
        # Register processors for different data types
        self._register_processors()
        
        # Start consuming from topics
        topics_to_process = [
            MessageTopic.SENSOR_SATELLITE,
            MessageTopic.SENSOR_UAV,
            MessageTopic.SENSOR_GROUND,
            MessageTopic.OSINT_NEWS,
            MessageTopic.OSINT_SOCIAL,
            MessageTopic.OSINT_RADIO,
        ]
        
        await self._kafka.start_consumer(topics_to_process)
        
        self._running = True
        logger.info("✓ Stream processing pipeline started")
    
    async def stop(self) -> None:
        """Stop the processing pipeline."""
        if not self._running:
            return
        
        logger.info("Stopping stream processing pipeline...")
        
        self._running = False
        
        logger.info("✓ Stream processing pipeline stopped")
    
    def _register_processors(self) -> None:
        """Register stream processors for each topic."""
        # OSINT News processing
        self._kafka.subscribe(
            MessageTopic.OSINT_NEWS,
            self._create_processor_handler(self._process_news_data),
        )
        
        # OSINT Social Media processing
        self._kafka.subscribe(
            MessageTopic.OSINT_SOCIAL,
            self._create_processor_handler(self._process_social_data),
        )
        
        # Sensor data processing
        self._kafka.subscribe(
            MessageTopic.SENSOR_SATELLITE,
            self._create_processor_handler(self._process_sensor_data),
        )
        
        self._kafka.subscribe(
            MessageTopic.SENSOR_UAV,
            self._create_processor_handler(self._process_sensor_data),
        )
        
        self._kafka.subscribe(
            MessageTopic.SENSOR_GROUND,
            self._create_processor_handler(self._process_sensor_data),
        )
        
        logger.info("Registered stream processors for all topics")
    
    def _create_processor_handler(
        self, processor: StreamProcessor
    ) -> Callable[[KafkaMessage], Coroutine[Any, Any, None]]:
        """Create a handler that wraps a processor with stats tracking."""
        async def handler(message: KafkaMessage) -> None:
            start_time = asyncio.get_event_loop().time()
            
            # Initialize stats if needed
            if message.topic not in self._stats:
                self._stats[message.topic] = ProcessingStats()
            
            stats = self._stats[message.topic]
            
            try:
                # Process the message
                result = await processor(message)
                
                stats.messages_processed += 1
                
                if result:
                    stats.messages_enriched += 1
                else:
                    stats.messages_filtered += 1
                
                # Track processing time
                elapsed = asyncio.get_event_loop().time() - start_time
                stats.processing_time_total += elapsed
            
            except Exception as e:
                logger.error(f"Error processing message from {message.topic}: {e}")
                stats.errors += 1
        
        return handler
    
    # ==================== Data Processors ====================
    
    async def _process_news_data(self, message: KafkaMessage) -> KafkaMessage | None:
        """Process news data: cleanse, extract entities, analyze sentiment."""
        try:
            payload = message.payload
            content = payload.get("content", "")
            metadata = payload.get("metadata", {})
            
            # 1. Data cleansing
            cleaned_content = self._cleanse_text(content)
            
            # 2. ML-powered entity extraction
            entities = self._extract_entities_ml(cleaned_content)
            
            # 3. Location extraction (ML-powered)
            locations = entities.get("locations", [])
            
            # 4. ML sentiment analysis
            sentiment = self._analyze_sentiment_ml(cleaned_content)
            
            # 5. ML threat detection
            threat_analysis = self._detect_threats_ml(cleaned_content)
            threat_indicators = threat_analysis.get("details", {}).get("keyword_matches", {})
            
            # Skip if no relevant content
            if not entities and not locations and not threat_indicators:
                logger.debug(f"Filtering out non-relevant news: {content[:50]}...")
                return None
            
            # Add ML-powered topic classification
            topics = []
            if self._use_ml:
                topics = self._classify_topic_ml(cleaned_content)
            
            # Create enriched message
            enriched_payload = {
                **payload,
                "processed": True,
                "cleaned_content": cleaned_content,
                "ml_powered": self._use_ml,
                "entities": entities,
                "locations": locations,
                "sentiment": sentiment,
                "threat_analysis": threat_analysis if self._use_ml else None,
                "threat_indicators": threat_indicators,
                "topics": topics,
                "relevance_score": (
                    len(entities.get("all", [])) if isinstance(entities, dict) 
                    else len(entities)
                ) + len(locations) + len(threat_indicators),
            }
            
            # Publish to analytics topic
            await self._kafka.publish(
                topic=MessageTopic.ANALYTICS_NARRATIVE,
                payload=enriched_payload,
                key=message.key,
                priority=message.priority,
            )
            
            logger.debug(f"Processed news article with {len(entities)} entities")
            
            return message
        
        except Exception as e:
            logger.error(f"Error processing news data: {e}")
            return None
    
    async def _process_social_data(self, message: KafkaMessage) -> KafkaMessage | None:
        """Process social media data: detect trends, identify coordinated activity."""
        try:
            payload = message.payload
            content = payload.get("content", "")
            metadata = payload.get("metadata", {})
            
            # 1. Clean content
            cleaned_content = self._cleanse_text(content)
            
            # 2. Hashtag analysis
            hashtags = metadata.get("hashtags", [])
            
            # 3. Engagement analysis
            engagement = metadata.get("engagement", {})
            engagement_score = (
                engagement.get("likes", 0) * 1 +
                engagement.get("shares", 0) * 3 +
                engagement.get("comments", 0) * 2
            )
            
            # 4. Bot detection (simplified)
            is_potential_bot = self._detect_bot_behavior(metadata)
            
            # 5. Coordinated activity detection
            is_coordinated = self._detect_coordinated_activity(metadata, hashtags)
            
            # Skip low-engagement, non-relevant posts
            if engagement_score < 10 and not is_coordinated:
                return None
            
            enriched_payload = {
                **payload,
                "processed": True,
                "cleaned_content": cleaned_content,
                "engagement_score": engagement_score,
                "is_potential_bot": is_potential_bot,
                "is_coordinated": is_coordinated,
                "sentiment": self._analyze_sentiment(cleaned_content),
            }
            
            # Publish to analytics
            await self._kafka.publish(
                topic=MessageTopic.ANALYTICS_NARRATIVE,
                payload=enriched_payload,
                key=message.key,
                priority=message.priority,
            )
            
            logger.debug(f"Processed social media post with engagement score {engagement_score}")
            
            return message
        
        except Exception as e:
            logger.error(f"Error processing social data: {e}")
            return None
    
    async def _process_sensor_data(self, message: KafkaMessage) -> KafkaMessage | None:
        """Process sensor data: normalize, validate, enrich with geospatial data."""
        try:
            payload = message.payload
            sensor_type = payload.get("sensor_type", "unknown")
            data = payload.get("data", {})
            
            # 1. Data validation
            if not self._validate_sensor_data(data):
                logger.warning(f"Invalid sensor data from {sensor_type}")
                return None
            
            # 2. Normalize coordinates
            if "coordinates" in data:
                coords = data["coordinates"]
                normalized_coords = self._normalize_coordinates(coords)
                data["coordinates_normalized"] = normalized_coords
            
            # 3. Add geospatial context
            if "location" in data:
                geo_context = self._get_geospatial_context(data["location"])
                data["geo_context"] = geo_context
            
            # 4. Anomaly detection
            is_anomalous = self._detect_sensor_anomaly(sensor_type, data)
            
            enriched_payload = {
                **payload,
                "processed": True,
                "is_anomalous": is_anomalous,
                "processing_timestamp": utcnow().isoformat(),
            }
            
            # If anomalous, trigger alert
            if is_anomalous:
                await self._kafka.publish(
                    topic=MessageTopic.ANALYTICS_ANOMALY,
                    payload={
                        "sensor_id": payload.get("sensor_id"),
                        "sensor_type": sensor_type,
                        "anomaly_type": "sensor_reading",
                        "severity": "MEDIUM",
                        "details": data,
                    },
                    priority=message.priority,
                )
            
            # Publish processed sensor data
            await self._kafka.publish(
                topic=MessageTopic.ANALYTICS_THREAT,
                payload=enriched_payload,
                key=message.key,
            )
            
            logger.debug(f"Processed {sensor_type} sensor data")
            
            return message
        
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            return None
    
    # ==================== Helper Methods ====================
    
    def _cleanse_text(self, text: str) -> str:
        """Clean and normalize text data."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove URLs (simplified)
        import re
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text.strip()
    
    def _extract_entities(self, text: str) -> list[dict[str, str]]:
        """Extract named entities (simplified implementation)."""
        entities = []
        
        # Simple keyword-based entity extraction
        entity_keywords = {
            "ORGANIZATION": ["Taliban", "NATO", "UN", "Red Cross", "ISAF"],
            "LOCATION": ["Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad"],
            "GROUP": ["insurgent", "militant", "forces", "troops"],
        }
        
        text_lower = text.lower()
        
        for entity_type, keywords in entity_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    entities.append({
                        "type": entity_type,
                        "value": keyword,
                    })
        
        return entities
    
    def _extract_locations(self, text: str) -> list[str]:
        """Extract location mentions."""
        locations = []
        
        location_names = [
            "Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad",
            "Kunduz", "Ghazni", "Helmand", "Nangarhar", "Pakistan",
        ]
        
        text_lower = text.lower()
        
        for location in location_names:
            if location.lower() in text_lower:
                locations.append(location)
        
        return list(set(locations))
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment (simplified)."""
        text_lower = text.lower()
        
        positive_words = ["peace", "aid", "help", "support", "success", "progress"]
        negative_words = ["attack", "killed", "violence", "threat", "crisis", "danger"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
    
    def _detect_threat_keywords(self, text: str) -> list[str]:
        """Detect threat-related keywords."""
        threat_keywords = [
            "attack", "bomb", "IED", "ambush", "militant", "insurgent",
            "Taliban", "threat", "violence", "weapon", "explosive",
        ]
        
        text_lower = text.lower()
        detected = [kw for kw in threat_keywords if kw.lower() in text_lower]
        
        return detected
    
    def _detect_bot_behavior(self, metadata: dict[str, Any]) -> bool:
        """Detect potential bot behavior (simplified)."""
        # Simple heuristics
        engagement = metadata.get("engagement", {})
        
        # Very high activity with low engagement might be a bot
        likes = engagement.get("likes", 0)
        shares = engagement.get("shares", 0)
        
        if shares > 100 and likes < 10:
            return True
        
        return False
    
    def _detect_coordinated_activity(
        self, metadata: dict[str, Any], hashtags: list[str]
    ) -> bool:
        """Detect coordinated social media activity."""
        # Multiple accounts using same hashtags at similar times
        # This is a simplified check
        
        if len(hashtags) > 5:
            # Too many hashtags might indicate coordination
            return True
        
        return False
    
    def _validate_sensor_data(self, data: dict[str, Any]) -> bool:
        """Validate sensor data structure."""
        # Basic validation
        if not data:
            return False
        
        # Check for required fields based on sensor type
        return True
    
    def _normalize_coordinates(self, coords: dict[str, Any]) -> dict[str, float]:
        """Normalize coordinate formats."""
        lat = coords.get("lat", coords.get("latitude", 0.0))
        lon = coords.get("lon", coords.get("longitude", 0.0))
        
        return {
            "latitude": float(lat),
            "longitude": float(lon),
        }
    
    def _get_geospatial_context(self, location: str) -> dict[str, Any]:
        """Get geospatial context for a location."""
        # In production, query geospatial database
        return {
            "location": location,
            "country": "Afghanistan",
            "risk_level": "MEDIUM",  # Would be dynamically determined
        }
    
    def _detect_sensor_anomaly(self, sensor_type: str, data: dict[str, Any]) -> bool:
        """Detect anomalies in sensor data."""
        # Simplified anomaly detection
        
        if sensor_type == "ground" and "temperature" in data:
            temp = data["temperature"]
            # Extreme temperatures
            if temp < -30 or temp > 50:
                return True
        
        return False
    
    def _load_ml_services(self):
        """Lazy load ML services."""
        global _ml_services_loaded, _ner_service, _sentiment_service, _threat_service, _classification_service
        
        if not _ml_services_loaded and self._use_ml:
            try:
                logger.info("Loading ML services...")
                from src.services.ml import (
                    get_ner_service,
                    get_sentiment_service,
                    get_threat_detection_service,
                    get_classification_service,
                )
                
                _ner_service = get_ner_service()
                _sentiment_service = get_sentiment_service()
                _threat_service = get_threat_detection_service()
                _classification_service = get_classification_service()
                
                _ml_services_loaded = True
                logger.info("✓ ML services loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load ML services: {e}")
                logger.info("Falling back to rule-based processing")
                self._use_ml = False
    
    def _extract_entities_ml(self, text: str) -> dict[str, Any]:
        """Extract entities using ML models."""
        if not self._use_ml:
            return self._extract_entities(text)
        
        self._load_ml_services()
        
        if _ner_service:
            try:
                # Get all entities
                all_entities = _ner_service.extract_entities(text, min_confidence=0.6)
                
                # Get specific types
                locations = _ner_service.extract_locations(text, min_confidence=0.6)
                organizations = _ner_service.extract_organizations(text, min_confidence=0.6)
                persons = _ner_service.extract_persons(text, min_confidence=0.6)
                
                return {
                    "all": all_entities,
                    "locations": locations,
                    "organizations": organizations,
                    "persons": persons,
                }
            except Exception as e:
                logger.error(f"ML entity extraction failed: {e}")
                return self._extract_entities(text)
        
        return self._extract_entities(text)
    
    def _analyze_sentiment_ml(self, text: str) -> str:
        """Analyze sentiment using ML models."""
        if not self._use_ml:
            return self._analyze_sentiment(text)
        
        self._load_ml_services()
        
        if _sentiment_service:
            try:
                result = _sentiment_service.analyze(text)
                return result["sentiment"]
            except Exception as e:
                logger.error(f"ML sentiment analysis failed: {e}")
                return self._analyze_sentiment(text)
        
        return self._analyze_sentiment(text)
    
    def _detect_threats_ml(self, text: str) -> dict[str, Any]:
        """Detect threats using ML models."""
        if not self._use_ml:
            threat_keywords = self._detect_threat_keywords(text)
            return {
                "threat_detected": len(threat_keywords) > 0,
                "threat_score": min(len(threat_keywords) * 0.2, 1.0),
                "threat_level": "medium" if threat_keywords else "low",
                "details": {"keyword_matches": {"general": threat_keywords}},
            }
        
        self._load_ml_services()
        
        if _threat_service:
            try:
                return _threat_service.detect_threats(text, include_details=True)
            except Exception as e:
                logger.error(f"ML threat detection failed: {e}")
                threat_keywords = self._detect_threat_keywords(text)
                return {
                    "threat_detected": len(threat_keywords) > 0,
                    "threat_score": min(len(threat_keywords) * 0.2, 1.0),
                    "threat_level": "medium" if threat_keywords else "low",
                }
        
        threat_keywords = self._detect_threat_keywords(text)
        return {
            "threat_detected": len(threat_keywords) > 0,
            "threat_score": min(len(threat_keywords) * 0.2, 1.0),
            "threat_level": "medium" if threat_keywords else "low",
        }
    
    def _classify_topic_ml(self, text: str) -> list[dict[str, Any]]:
        """Classify topic using ML models."""
        if not self._use_ml:
            return []
        
        self._load_ml_services()
        
        if _classification_service:
            try:
                return _classification_service.classify_isr_topic(text, top_k=3)
            except Exception as e:
                logger.error(f"ML topic classification failed: {e}")
                return []
        
        return []
    
    def get_stats(self) -> dict[str, Any]:
        """Get processing statistics."""
        return {
            "running": self._running,
            "ml_enabled": self._use_ml,
            "ml_loaded": _ml_services_loaded,
            "topics": {
                topic.value: {
                    "messages_processed": stats.messages_processed,
                    "messages_enriched": stats.messages_enriched,
                    "messages_filtered": stats.messages_filtered,
                    "errors": stats.errors,
                    "avg_processing_time_ms": stats.avg_processing_time * 1000,
                }
                for topic, stats in self._stats.items()
            },
        }


# Global instance
_stream_processor: StreamProcessingPipeline | None = None


def get_stream_processor() -> StreamProcessingPipeline:
    """Get the stream processor instance."""
    global _stream_processor
    if _stream_processor is None:
        _stream_processor = StreamProcessingPipeline()
    return _stream_processor
