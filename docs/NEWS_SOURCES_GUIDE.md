# News Sources Integration Guide

## Overview

The ISR Platform now integrates with **three major news sources** to provide comprehensive coverage of Afghanistan and regional security topics:

1. **NewsAPI.org** - Aggregated news from 150,000+ sources
2. **The Guardian Open Platform** - Quality journalism with 2.7M+ articles
3. **New York Times API** - Premium coverage with 170+ years of archives

---

## 1. NewsAPI.org

### Overview
- **Website:** https://newsapi.org/
- **Free Tier:** 100 requests/day
- **Coverage:** 150,000+ news sources worldwide
- **Documentation:** https://newsapi.org/docs

### Features
- Real-time news aggregation
- Search by keywords and categories
- Source filtering
- Multi-language support (English for our use case)

### Setup

1. **Get API Key:**
   - Sign up at https://newsapi.org/register
   - Free tier provides 100 requests/day
   - Upgrade to Developer ($449/month) for unlimited

2. **Configure in `.env`:**
   ```bash
   NEWSAPI_ENABLED=true
   NEWSAPI_API_KEY=your_api_key_here
   NEWSAPI_POLL_INTERVAL_SECONDS=900  # 15 minutes
   ```

3. **Search Queries:**
   The connector searches for:
   - Afghanistan
   - Taliban
   - Kabul
   - Kandahar
   - Pakistan border
   - Central Asia conflict

### Rate Limits
- **Free Tier:** 100 requests/day
- **Developer:** Unlimited
- **Connector Config:** 5 req/min, 100 req/hour

### Data Published To
- Kafka Topic: `isr.osint.news`
- Fields: title, description, content, author, URL, source, published_at

---

## 2. The Guardian Open Platform

### Overview
- **Website:** https://open-platform.theguardian.com/
- **Free Tier:** 5,000 requests/day (Developer tier)
- **Coverage:** 2.7 million+ articles from 1999 onwards
- **Documentation:** https://open-platform.theguardian.com/documentation/

### Features
- High-quality journalism
- Rich metadata (tags, keywords, sections)
- Full article text available
- Advanced search capabilities
- Section-based filtering

### Setup

1. **Get API Key:**
   - Request at https://open-platform.theguardian.com/access/
   - Approval is typically instant
   - Developer tier is FREE

2. **Configure in `.env`:**
   ```bash
   GUARDIAN_ENABLED=true
   GUARDIAN_API_KEY=your_api_key_here
   GUARDIAN_POLL_INTERVAL_SECONDS=900  # 15 minutes
   ```

3. **Search Coverage:**
   The connector searches:
   - **By Keywords:** Afghanistan, Taliban, Kabul, Pakistan border, Central Asia security
   - **By Sections:** world/afghanistan, world/asia, world/middleeast

### Rate Limits
- **Developer Tier:** 5,000 requests/day, 12 requests/second
- **Connector Config:** 60 req/min, 720 req/hour, 5000 req/day

### Data Published To
- Kafka Topic: `isr.osint.news`
- Fields: headline, trailText, bodyText, byline, section, keywords, tags, URL, thumbnail

### Special Features
- **Rich Tags:** Keyword tags for better categorization
- **Sections:** Well-organized content hierarchy
- **Thumbnails:** Image URLs for visual content
- **Full Text:** Complete article body (first 1000 chars to avoid huge payloads)

---

## 3. New York Times API

### Overview
- **Website:** https://developer.nytimes.com/
- **Free Tier:** 500 requests/day
- **Coverage:** 170+ years of archives
- **Documentation:** https://developer.nytimes.com/docs/articlesearch-product/1/overview

### Features
- Article Search API (historical archives)
- Top Stories API (current headlines)
- Most Popular API (trending articles)
- Rich metadata with facets and keywords

### Setup

1. **Get API Key:**
   - Sign up at https://developer.nytimes.com/accounts/create
   - Create an app to get API key
   - Free tier provides 500 requests/day

2. **Configure in `.env`:**
   ```bash
   NYTIMES_ENABLED=true
   NYTIMES_API_KEY=your_api_key_here
   NYTIMES_POLL_INTERVAL_SECONDS=1800  # 30 minutes
   ```

3. **Data Sources:**
   The connector uses:
   - **Article Search API:** Historical search for Afghanistan-related articles
   - **Top Stories API:** Current headlines from World and Politics sections
   - **Filters:** Only articles from last 30 days mentioning Afghanistan/Taliban

### Rate Limits
- **Free Tier:** 500 requests/day, 5 requests/minute
- **Connector Config:** 5 req/min, 60 req/hour, 500 req/day

### Data Published To
- Kafka Topic: `isr.osint.news`
- Fields: headline, abstract, lead_paragraph, byline, section, keywords, facets, URL

### Special Features
- **Facets:** Geographic, organizational, and person tags
- **News Desk:** Editorial categorization
- **Document Types:** Article, blog post, multimedia, etc.
- **Word Count:** Article length metadata

---

## OpenWeatherMap API (Enhanced)

### Overview
- **Website:** https://openweathermap.org/api
- **Free Tier:** 60 requests/minute, 1M requests/month
- **Coverage:** 10 key Afghanistan locations
- **Documentation:** https://openweathermap.org/api

### Features (Enhanced)
- **Current Weather:** Real-time conditions
- **5-Day Forecast:** 3-hour interval predictions
- **Air Quality:** AQI and pollutant levels
- **Weather Alerts:** Severe weather warnings (if available)

### Setup

1. **Get API Key:**
   - Sign up at https://home.openweathermap.org/users/sign_up
   - Free tier is very generous
   - Instant activation

2. **Configure in `.env`:**
   ```bash
   WEATHER_ENABLED=true
   WEATHER_API_KEY=your_api_key_here
   WEATHER_POLL_INTERVAL_SECONDS=1800  # 30 minutes
   ```

3. **Monitored Locations (10 sites):**
   - **Capital:** Kabul
   - **Major Cities:** Kandahar, Herat, Mazar-i-Sharif
   - **Strategic:** Jalalabad, Kunduz, Lashkar Gah, Ghazni
   - **Border Crossings:** Torkham Border, Spin Boldak

### Rate Limits
- **Free Tier:** 60 req/min, 1,000,000 req/month
- **Connector Config:** 60 req/min, 1000 req/hour, 10000 req/day

### Data Published To
- Kafka Topic: `isr.sensor.ground`
- Fields: temperature, humidity, wind, visibility, conditions, forecast, air_quality

### Enhanced Features
- **Comprehensive Data:** Current + 24-hour forecast + air quality
- **Strategic Importance:** Each location tagged with importance level
- **Border Monitoring:** Weather at key border crossings for operational planning

---

## Comparison Table

| Source | Free Tier Limit | Coverage | Latency | Best For |
|--------|----------------|----------|---------|----------|
| **NewsAPI** | 100 req/day | 150k+ sources | Real-time | Broad aggregation |
| **The Guardian** | 5,000 req/day | Quality journalism | ~15 min | In-depth analysis |
| **NY Times** | 500 req/day | Premium content | ~30 min | Authoritative reporting |
| **OpenWeatherMap** | 60 req/min | Global weather | Real-time | Operational planning |

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    News Sources                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  NewsAPI   │  │  Guardian  │  │  NY Times  │           │
│  │   (100/d)  │  │  (5k/day)  │  │  (500/d)   │           │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
│        │                │                │                   │
│        └────────────────┴────────────────┘                   │
│                         │                                    │
│                  ┌──────▼──────┐                            │
│                  │   Kafka     │                            │
│                  │isr.osint.news                            │
│                  └──────┬──────┘                            │
│                         │                                    │
│                  ┌──────▼──────┐                            │
│                  │   Stream    │                            │
│                  │  Processor  │                            │
│                  └──────┬──────┘                            │
│                         │                                    │
│        ┌────────────────┼────────────────┐                 │
│        │                │                │                  │
│   ┌────▼─────┐   ┌─────▼────┐   ┌──────▼─────┐           │
│   │ Entity   │   │Sentiment │   │  Threat    │           │
│   │Extraction│   │ Analysis │   │  Scoring   │           │
│   └──────────┘   └──────────┘   └────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Starting the System

```python
from src.services.ingestion_bootstrap import bootstrap_ingestion_system, start_ingestion_system

# Register all connectors (including new news sources)
bootstrap_ingestion_system()

# Start ingestion
await start_ingestion_system()
```

### Monitoring via API

```bash
# Check all connectors
curl http://localhost:8000/api/v1/ingestion/connectors

# Check specific connector
curl http://localhost:8000/api/v1/ingestion/connectors/guardian

# View recent news articles from Kafka
curl http://localhost:8000/api/v1/ingestion/kafka/history?topic=isr.osint.news&limit=20
```

### Configuration Status

```bash
# View all configuration
curl http://localhost:8000/api/v1/ingestion/stats
```

---

## Data Flow

### News Articles
1. **Fetch:** Connector polls API every 15-30 minutes
2. **Filter:** Articles mentioning Afghanistan/Taliban/regional keywords
3. **Publish:** Raw articles to `isr.osint.news` topic
4. **Process:** Stream processor extracts entities, sentiment, threats
5. **Enrich:** Publish enriched data to `isr.analytics.narrative` topic
6. **Store:** Analytics services consume and store for querying

### Weather Data
1. **Fetch:** Poll OpenWeatherMap every 30 minutes
2. **Gather:** Current + forecast + air quality for 10 locations
3. **Publish:** Comprehensive data to `isr.sensor.ground` topic
4. **Process:** Stream processor validates and enriches
5. **Alert:** Detect anomalous conditions (extreme temps, storms)
6. **Store:** Available for operational planning queries

---

## Troubleshooting

### NewsAPI Issues
- **Error: 429 (Rate Limit):** Increase `NEWSAPI_POLL_INTERVAL_SECONDS`
- **Error: 401 (Unauthorized):** Check API key is valid
- **No Results:** Queries might be too specific, check logs

### Guardian API Issues
- **Error: 403 (Forbidden):** API key might need approval
- **Error: Rate Limited:** Adjust `GUARDIAN_MAX_REQUESTS_PER_MINUTE`
- **Empty Responses:** Normal if no recent articles match queries

### NY Times Issues
- **Error: 429:** Very strict 5 req/min limit, increase poll interval
- **Error: 401:** Verify API key and app is activated
- **Old Articles Only:** Article Search looks back 30 days, check Top Stories API

### OpenWeatherMap Issues
- **Error: 401:** API key activation can take 10 minutes
- **Missing Forecast:** Increase timeout settings
- **No Air Quality:** Not available for all locations

---

## Best Practices

1. **Stagger Poll Intervals:** Don't poll all sources simultaneously
2. **Monitor Rate Limits:** Check connector stats regularly
3. **Adjust Intervals:** Balance freshness vs. API costs
4. **Enable Circuit Breakers:** Automatic recovery from failures
5. **Review Logs:** Watch for errors or empty responses
6. **Deduplicate:** System handles duplicates by URL automatically

---

## Cost Analysis

### Free Tier Limits (Per Day)

| Source | Free Limit | Our Usage | Headroom |
|--------|-----------|-----------|----------|
| NewsAPI | 100 req | ~96 req (6 queries × 16 polls) | Tight |
| Guardian | 5,000 req | ~352 req (11 queries × 32 polls) | Excellent |
| NY Times | 500 req | ~96 req (8 queries × 12 polls) | Good |
| OpenWeatherMap | 28,800 req* | ~480 req (10 loc × 3 APIs × 16 polls) | Excellent |

*60 req/min × 60 min × 8 hours = 28,800 req per 8-hour day

### Recommendations
- **NewsAPI:** Consider paid tier if more frequent updates needed
- **Guardian:** Plenty of headroom, can increase poll frequency
- **NY Times:** Good balance, adjust queries as needed
- **OpenWeatherMap:** Very generous, no concerns

---

## Future Enhancements

- [ ] Add Reuters API integration
- [ ] Add BBC News API
- [ ] Add Al Jazeera RSS feeds
- [ ] Implement content deduplication across sources
- [ ] Add article similarity detection
- [ ] Create consolidated news digest
- [ ] Implement breaking news alerts
- [ ] Add multilingual support (Pashto, Dari)

---

## API Registration Links

Quick links to sign up for API keys:

- **NewsAPI:** https://newsapi.org/register
- **The Guardian:** https://open-platform.theguardian.com/access/
- **NY Times:** https://developer.nytimes.com/accounts/create
- **OpenWeatherMap:** https://home.openweathermap.org/users/sign_up

All offer free tiers suitable for development and testing!
