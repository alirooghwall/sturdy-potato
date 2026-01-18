# Data Ingestion System Guide

## Overview

The ISR Platform now includes a comprehensive data ingestion system that collects data from multiple external sources in real-time.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ISR Platform Ingestion System               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   NewsAPI    │  │  Weather API │  │ Social Media │        │
│  │  Connector   │  │  Connector   │  │  Connector   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
│         └──────────────────┴──────────────────┘                │
│                            │                                    │
│                    ┌───────▼────────┐                          │
│                    │  Kafka Message │                          │
│                    │      Bus       │                          │
│                    └───────┬────────┘                          │
│                            │                                    │
│                    ┌───────▼────────┐                          │
│                    │     Stream     │                          │
│                    │   Processor    │                          │
│                    └───────┬────────┘                          │
│                            │                                    │
│                    ┌───────▼────────┐                          │
│                    │   Analytics &  │                          │
│                    │   ML Services  │                          │
│                    └────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Real Kafka Implementation

**Location:** `src/services/kafka_bus_real.py`

**Features:**
- Real Kafka connectivity using `aiokafka`
- Automatic fallback to in-memory mode
- Message acknowledgment and exactly-once semantics
- Consumer groups for scalability

**Topics:**
- `isr.sensor.satellite` - Satellite imagery data
- `isr.sensor.uav` - UAV/drone data
- `isr.sensor.ground` - Ground sensor data
- `isr.osint.news` - News articles
- `isr.osint.social` - Social media posts
- `isr.analytics.threat` - Threat analysis results
- `isr.analytics.anomaly` - Anomaly detections
- `isr.analytics.narrative` - Narrative analysis

### 2. Data Connectors

**Location:** `src/services/connectors/`

#### Base Connector (`base.py`)
Provides common functionality for all connectors:
- **Rate Limiting:** Token bucket algorithm with per-minute, per-hour, and per-day limits
- **Retry Logic:** Exponential backoff with configurable retries
- **Circuit Breaker:** Automatic failure detection and recovery
- **Health Monitoring:** Real-time status tracking

#### NewsAPI Connector (`news_api.py`)
- Fetches news articles from NewsAPI.org
- Searches for Afghanistan-related news
- Publishes to `isr.osint.news` topic
- Rate limit: 5 req/min (free tier)

#### Weather API Connector (`weather.py`)
- Fetches weather data from OpenWeatherMap
- Monitors 6 key Afghanistan locations
- Publishes to `isr.sensor.ground` topic
- Rate limit: 60 req/min

#### Social Media Connector (`social_media.py`)
- Mock implementation for social media monitoring
- In production: Twitter/X, Telegram, Reddit APIs
- Publishes to `isr.osint.social` topic

#### Satellite Connectors (`satellite.py`)
- Interfaces for Planet Labs, Sentinel Hub, Maxar
- Requires API subscriptions (skeleton implementation)

### 3. Stream Processing Pipeline

**Location:** `src/services/stream_processor.py`

**Features:**
- Real-time data transformation and enrichment
- Entity extraction from text
- Sentiment analysis
- Threat keyword detection
- Geospatial processing
- Anomaly detection
- Data cleansing and normalization

**Processing Flow:**
1. **Ingest:** Receive raw data from Kafka topics
2. **Cleanse:** Remove noise, normalize text
3. **Extract:** Identify entities, locations, keywords
4. **Enrich:** Add context, sentiment, threat scores
5. **Publish:** Send processed data to analytics topics

### 4. Ingestion Manager

**Location:** `src/services/ingestion_manager.py`

**Features:**
- Centralized control of all connectors
- Health monitoring with automatic restarts
- Performance metrics collection
- System-wide statistics
- Failure alerting

## Configuration

**Location:** `src/config/ingestion_config.py`

All connectors are configured via environment variables:

```bash
# NewsAPI
NEWSAPI_ENABLED=true
NEWSAPI_API_KEY=your_api_key_here
NEWSAPI_POLL_INTERVAL_SECONDS=900

# Weather API
WEATHER_ENABLED=true
WEATHER_API_KEY=your_api_key_here
WEATHER_POLL_INTERVAL_SECONDS=1800

# Social Media
SOCIAL_ENABLED=true
SOCIAL_USE_MOCK_DATA=true
SOCIAL_TWITTER_API_KEY=your_key_here
SOCIAL_TELEGRAM_BOT_TOKEN=your_token_here

# Satellite (requires subscriptions)
SATELLITE_ENABLED=false
SATELLITE_PLANET_API_KEY=your_key_here

# System-wide settings
INGESTION_ENABLED=true
INGESTION_AUTO_START=false
INGESTION_HEALTH_CHECK_INTERVAL=60
```

## API Endpoints

All ingestion endpoints are available under `/api/v1/ingestion`:

### Health & Status

```bash
# Get overall system health
GET /api/v1/ingestion/health

# Get comprehensive statistics
GET /api/v1/ingestion/stats

# List all connectors
GET /api/v1/ingestion/connectors

# Get specific connector status
GET /api/v1/ingestion/connectors/{name}
```

### Control Operations

```bash
# Restart a connector
POST /api/v1/ingestion/connectors/{name}/restart
```

### Kafka Monitoring

```bash
# Get Kafka statistics
GET /api/v1/ingestion/kafka/stats

# Get message history
GET /api/v1/ingestion/kafka/history?topic=isr.osint.news&limit=100
```

### Stream Processor

```bash
# Get stream processor statistics
GET /api/v1/ingestion/stream-processor/stats
```

## Usage

### Starting the Ingestion System

#### Option 1: Programmatically

```python
from src.services.ingestion_bootstrap import bootstrap_ingestion_system, start_ingestion_system

# Bootstrap (register connectors)
bootstrap_ingestion_system()

# Start all connectors
await start_ingestion_system()
```

#### Option 2: Via API

```bash
# The system can be started via the ingestion manager
# See API endpoints above
```

### Registering Custom Connectors

```python
from src.services.connectors.base import BaseConnector, ConnectorConfig
from src.services.ingestion_manager import get_ingestion_manager

class MyCustomConnector(BaseConnector):
    async def fetch_data(self):
        # Fetch data from your source
        return data
    
    async def ingest_data(self, data):
        # Process and publish to Kafka
        await self._kafka.publish(...)

# Register with manager
manager = get_ingestion_manager()
config = ConnectorConfig(name="MyConnector")
connector = MyCustomConnector(config)
manager.register_connector("my_connector", connector)
```

## Monitoring

### Health Checks

The system performs automatic health checks every 60 seconds:
- Monitors connector status
- Detects circuit breaker states
- Attempts automatic recovery
- Publishes health metrics to Kafka

### Statistics

Each connector tracks:
- Total requests made
- Successful requests
- Failed requests
- Records ingested
- Last success timestamp
- Last error message

### Alerting

Failed connectors trigger:
- Automatic restart attempts
- Health status degradation
- Kafka health messages (topic: `isr.system.health`)

## Development

### Running Tests

```bash
pytest tests/test_ingestion.py -v
```

### Adding a New Connector

1. Create a new file in `src/services/connectors/`
2. Extend `BaseConnector`
3. Implement `fetch_data()` and `ingest_data()`
4. Add configuration to `src/config/ingestion_config.py`
5. Register in `src/services/ingestion_bootstrap.py`

### Example: Custom RSS Feed Connector

```python
from src.services.connectors.base import BaseConnector

class RSSConnector(BaseConnector[list[dict]]):
    def __init__(self, feed_url: str, config: ConnectorConfig):
        super().__init__(config)
        self.feed_url = feed_url
    
    async def fetch_data(self) -> list[dict] | None:
        response = await self._client.get(self.feed_url)
        response.raise_for_status()
        # Parse RSS feed
        return articles
    
    async def ingest_data(self, data: list[dict]) -> None:
        for article in data:
            await self._kafka.publish_osint_data(
                source_type="news",
                source_id=article["id"],
                content=article["content"],
                metadata=article["metadata"],
            )
```

## Production Deployment

### Requirements

1. **Kafka Cluster:** Real Kafka cluster (not in-memory)
2. **API Keys:** Valid keys for NewsAPI, OpenWeatherMap, etc.
3. **Environment Variables:** Properly configured (see Configuration section)

### Docker Deployment

The system is already configured in `docker-compose.yml`:

```yaml
services:
  kafka:
    image: bitnami/kafka:3.6
    # ... configuration
  
  api:
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - NEWSAPI_API_KEY=${NEWSAPI_API_KEY}
      - WEATHER_API_KEY=${WEATHER_API_KEY}
```

### Starting in Production

```bash
# Set environment variables
export NEWSAPI_API_KEY=your_key
export WEATHER_API_KEY=your_key
export INGESTION_AUTO_START=true

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Connector Not Starting

Check:
1. Is it enabled in configuration?
2. Are API keys valid?
3. Check circuit breaker state
4. Review logs for errors

### Rate Limiting Issues

- Adjust `max_requests_per_minute` in configuration
- Increase `poll_interval_seconds`
- Check API subscription limits

### Kafka Connection Failures

- Verify `KAFKA_BOOTSTRAP_SERVERS` is correct
- Check if Kafka is running: `docker-compose ps kafka`
- System will fallback to in-memory mode automatically

### Circuit Breaker Open

- Check connector statistics for error details
- Manually restart connector via API
- Circuit breaker will auto-reset after timeout

## Performance Tips

1. **Tune Poll Intervals:** Balance freshness vs. API costs
2. **Enable Compression:** Kafka uses gzip compression
3. **Batch Processing:** Stream processor handles batches efficiently
4. **Horizontal Scaling:** Use Kafka consumer groups for multiple instances
5. **Caching:** Consider Redis for frequently accessed data

## Security

- **API Keys:** Store in environment variables, never commit to git
- **Rate Limiting:** Prevents API abuse and cost overruns
- **Circuit Breakers:** Protects against cascading failures
- **Audit Logs:** All operations logged to `isr.system.audit` topic

## Future Enhancements

- [ ] Apache Flink integration for advanced stream processing
- [ ] Satellite imagery processing with ML models
- [ ] Real Twitter/Telegram API integration
- [ ] Data quality scoring
- [ ] Advanced anomaly detection algorithms
- [ ] Custom alerting rules engine
