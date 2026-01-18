# Complete System Workflow Guide

## Overview

This document describes the complete end-to-end workflow of the ISR Platform, from data ingestion to analysis and reporting.

---

## 🔄 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL DATA SOURCES                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📰 News Sources          🌤️ Weather           📱 Social Media    │
│  • NewsAPI.org           • OpenWeatherMap      • Twitter (mock)    │
│  • The Guardian          • 10 locations        • Telegram (mock)   │
│  • NY Times              • Forecast + AQI      • Reddit (mock)     │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA INGESTION LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔌 Connectors (6 total)                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐      │
│  │ News Connector │  │Weather Connector│  │Social Connector│      │
│  │ • Rate Limited │  │ • 30min polling │  │ • 10min polling│      │
│  │ • 15min polling│  │ • 10 locations  │  │ • Mock data    │      │
│  │ • 3 sources    │  └────────┬────────┘  └────────┬───────┘      │
│  └────────┬───────┘           │                    │               │
│           └───────────────────┴────────────────────┘               │
│                               │                                     │
│                    Features Applied:                                │
│                    • Rate Limiting (token bucket)                   │
│                    • Circuit Breaker (fault tolerance)              │
│                    • Retry Logic (exponential backoff)              │
│                    • Health Monitoring                              │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         KAFKA MESSAGE BUS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📨 Topics (29 total)                                               │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │ isr.osint.news          → News articles                  │     │
│  │ isr.osint.social        → Social media posts             │     │
│  │ isr.sensor.ground       → Weather data                   │     │
│  │ isr.sensor.satellite    → Satellite data (ready)         │     │
│  │ isr.analytics.threat    → Threat analysis results        │     │
│  │ isr.analytics.anomaly   → Anomaly detections             │     │
│  │ isr.analytics.narrative → Narrative analysis             │     │
│  │ isr.alerts.new          → New alerts                     │     │
│  │ isr.system.health       → System health metrics          │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  Features:                                                          │
│  • Exactly-once semantics                                          │
│  • Gzip compression                                                │
│  • Consumer groups (horizontal scaling)                            │
│  • Message persistence                                             │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STREAM PROCESSING PIPELINE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ⚙️ ETL Processing (Extract, Transform, Load)                      │
│                                                                     │
│  1️⃣ EXTRACT                                                         │
│     └─ Consume from Kafka topics                                   │
│                                                                     │
│  2️⃣ TRANSFORM (ML-Powered)                                         │
│     ├─ Data Cleansing                                              │
│     ├─ Entity Extraction (NER with transformers)                   │
│     ├─ Sentiment Analysis (transformer-based)                      │
│     ├─ Threat Detection (ensemble ML)                              │
│     ├─ Topic Classification (zero-shot)                            │
│     ├─ Geospatial Enrichment                                       │
│     └─ Anomaly Detection                                           │
│                                                                     │
│  3️⃣ LOAD                                                            │
│     └─ Publish enriched data to analytics topics                   │
│                                                                     │
│  Processing Stats Tracked:                                         │
│  • Messages processed                                              │
│  • Messages enriched                                               │
│  • Processing time                                                 │
│  • Error rate                                                      │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MACHINE LEARNING LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🤖 ML Services (8 services, 12+ models)                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │ 1. Named Entity Recognition (NER)                        │     │
│  │    Model: dslim/bert-base-NER                            │     │
│  │    → Extracts: Persons, Orgs, Locations, GPE             │     │
│  │                                                           │     │
│  │ 2. Sentiment Analysis                                     │     │
│  │    Model: distilbert-base-uncased-finetuned-sst-2        │     │
│  │    → Output: Positive/Negative/Neutral + confidence      │     │
│  │                                                           │     │
│  │ 3. Zero-Shot Classification                              │     │
│  │    Model: facebook/bart-large-mnli                       │     │
│  │    → Topics: Security, Military, Humanitarian, etc.      │     │
│  │                                                           │     │
│  │ 4. Threat Detection (Ensemble)                           │     │
│  │    → Combines: Keywords + Sentiment + NER + Classify     │     │
│  │    → Output: Score (0-1), Level (low/med/high/critical)  │     │
│  │                                                           │     │
│  │ 5. Semantic Embeddings                                   │     │
│  │    Model: sentence-transformers/all-MiniLM-L6-v2         │     │
│  │    → Similarity, Search, Clustering, Duplicates          │     │
│  │                                                           │     │
│  │ 6. Text Summarization                                    │     │
│  │    Model: facebook/bart-large-cnn                        │     │
│  │    → Abstractive & Extractive summaries                  │     │
│  │                                                           │     │
│  │ 7. Translation (Multilingual)                            │     │
│  │    Models: Helsinki-NLP, M2M100                          │     │
│  │    → 100+ languages, including Pashto, Dari, Urdu       │     │
│  │                                                           │     │
│  │ 8. Performance Monitoring                                │     │
│  │    → Tracks usage, latency, errors, throughput           │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ML Pipeline Features:                                             │
│  • GPU/CPU auto-detection                                          │
│  • Model caching (fast reload)                                     │
│  • Lazy loading (on-demand)                                        │
│  • Batch processing                                                │
│  • Graceful fallback (rule-based if ML fails)                      │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       STORAGE & DATABASE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🗄️ PostgreSQL + PostGIS                                           │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │ • Entities (persons, organizations, locations)            │     │
│  │ • Events (security incidents, operations)                 │     │
│  │ • Alerts (threat notifications)                           │     │
│  │ • Intelligence Reports                                    │     │
│  │ • Geospatial Data (with PostGIS)                          │     │
│  │ • User Management                                         │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  💾 Redis (Caching)                                                │
│  • Session cache                                                   │
│  • Query result cache                                              │
│  • Real-time data cache                                            │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          REST API LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🌐 FastAPI Endpoints (50+ endpoints)                              │
│                                                                     │
│  📊 Data Ingestion APIs                                            │
│  GET  /api/v1/ingestion/health                                     │
│  GET  /api/v1/ingestion/stats                                      │
│  GET  /api/v1/ingestion/connectors                                 │
│  POST /api/v1/ingestion/connectors/{name}/restart                  │
│                                                                     │
│  🤖 Machine Learning APIs                                          │
│  POST /api/v1/ml-api/ner/extract                                   │
│  POST /api/v1/ml-api/sentiment/analyze                             │
│  POST /api/v1/ml-api/classify/isr-topic                            │
│  POST /api/v1/ml-api/threat/detect                                 │
│  POST /api/v1/ml-api/similarity                                    │
│  POST /api/v1/ml-api/summarize                                     │
│  POST /api/v1/ml-api/translate                                     │
│                                                                     │
│  📈 Analytics APIs                                                 │
│  GET  /api/v1/analytics/threat-landscape                           │
│  GET  /api/v1/analytics/entity-relationships                       │
│  GET  /api/v1/analytics/temporal-patterns                          │
│                                                                     │
│  🚨 Alert APIs                                                     │
│  GET  /api/v1/alerts                                               │
│  POST /api/v1/alerts/{id}/acknowledge                              │
│                                                                     │
│  📊 Monitoring APIs                                                │
│  GET  /api/v1/ml-api/monitoring/system                             │
│  GET  /api/v1/ml-api/monitoring/models                             │
│  GET  /api/v1/ml-api/monitoring/request-rate                       │
│                                                                     │
│  Features:                                                          │
│  • Interactive Swagger UI (/docs)                                  │
│  • ReDoc documentation (/redoc)                                    │
│  • CORS enabled                                                    │
│  • JWT authentication ready                                        │
│  • Rate limiting                                                   │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🖥️ **CURRENT STATE: Backend API Only**                           │
│                                                                     │
│  Available Interfaces:                                             │
│  ✅ REST API (50+ endpoints)                                       │
│  ✅ Swagger UI (http://localhost:8000/docs)                        │
│  ✅ ReDoc (http://localhost:8000/redoc)                            │
│  ✅ curl/Postman/HTTPie compatible                                 │
│                                                                     │
│  ❌ Web UI (NOT IMPLEMENTED)                                       │
│  ❌ Dashboard (NOT IMPLEMENTED)                                    │
│  ❌ React/Vue Frontend (NOT IMPLEMENTED)                           │
│                                                                     │
│  To interact with the system:                                      │
│  • Use API directly (Swagger UI recommended)                       │
│  • Build custom UI using the REST API                              │
│  • Use command-line tools (curl, scripts)                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Workflow Examples

### Example 1: News Article Processing

```
1. Data Ingestion (Every 15 minutes)
   ↓
   Guardian API fetches latest Afghanistan news
   ↓
   Connector publishes to Kafka: isr.osint.news
   
2. Stream Processing (Real-time)
   ↓
   Consumer reads from isr.osint.news
   ↓
   ML Pipeline processes article:
   • NER extracts: "Taliban", "Kabul", "UN"
   • Sentiment: "negative" (0.82)
   • Threat detection: HIGH (0.78)
   • Topics: ["security threat", "military operations"]
   • Summary: "Taliban forces..."
   ↓
   Publishes enriched data to: isr.analytics.threat
   
3. Alert Generation
   ↓
   If threat score > 0.7:
   • Create alert in database
   • Publish to: isr.alerts.new
   • Can trigger notifications
   
4. API Access
   ↓
   User queries: GET /api/v1/alerts?severity=HIGH
   ↓
   Returns enriched alerts with ML analysis
```

### Example 2: Threat Intelligence Query

```
1. User Request
   ↓
   POST /api/v1/ml-api/threat/detect
   Body: {"text": "IED attack reported in Kandahar", "include_details": true}
   
2. ML Processing
   ↓
   Threat Detection Service processes:
   • Keyword detection: "IED", "attack", "Kandahar"
   • Sentiment analysis: negative
   • NER: Location="Kandahar"
   • Classification: "security threat" (0.92)
   ↓
   Ensemble scoring combines all signals
   
3. Response
   ↓
   {
     "threat_detected": true,
     "threat_score": 0.85,
     "threat_level": "high",
     "details": {
       "entities": ["Kandahar"],
       "threat_indicators": ["IED", "attack"],
       "sentiment": "negative"
     }
   }
```

### Example 3: Multilingual OSINT Processing

```
1. Input (Pashto Text)
   ↓
   POST /api/v1/ml-api/translate
   Body: {"text": "د طالبانو پوځونه...", "source_lang": "ps", "target_lang": "en"}
   
2. Translation
   ↓
   M2M100 model translates Pashto → English
   ↓
   Returns: "Taliban forces..."
   
3. Analysis Chain
   ↓
   Translated text → NER → Sentiment → Threat Detection
   ↓
   Enriched intelligence in English
   
4. Optional: Summarization
   ↓
   POST /api/v1/ml-api/summarize
   ↓
   Concise summary for analysts
```

---

## 🔄 Continuous Operations

### Background Processes

1. **Data Ingestion Loop** (Always Running)
   ```
   Every 15 min: News sources → Kafka
   Every 30 min: Weather data → Kafka
   Every 10 min: Social media → Kafka
   ```

2. **Stream Processing** (Always Running)
   ```
   Continuously: Consume → Process → Enrich → Publish
   ```

3. **Health Monitoring** (Every 60 seconds)
   ```
   Check:
   • Connector health
   • Kafka connectivity
   • ML model status
   • Circuit breaker states
   ↓
   Auto-restart failed connectors
   ↓
   Publish metrics to: isr.system.health
   ```

4. **ML Performance Tracking** (Continuous)
   ```
   Track:
   • Model usage (calls, latency)
   • Request rate (throughput)
   • Error rate
   • Memory usage
   ↓
   Available via: /api/v1/ml-api/monitoring/*
   ```

---

## 🎯 Use Case Workflows

### Intelligence Analyst Workflow

```
Morning Briefing:
1. GET /api/v1/alerts?since=24h → Recent alerts
2. GET /api/v1/analytics/threat-landscape → Threat overview
3. GET /api/v1/events?type=security → Security incidents

Investigation:
1. Find related articles:
   POST /api/v1/ml-api/search
   Body: {"query": "Taliban operations", "documents": [...]}
   
2. Analyze specific text:
   POST /api/v1/ml-api/threat/detect
   
3. Extract entities:
   POST /api/v1/ml-api/ner/extract
   
4. Check for duplicates:
   POST /api/v1/ml-api/duplicates

Report Generation:
1. GET /api/v1/reports/generate
2. Summarize findings:
   POST /api/v1/ml-api/summarize/news
```

### System Administrator Workflow

```
Health Check:
1. GET /api/v1/ingestion/health
2. GET /api/v1/ml-api/monitoring/system
3. GET /api/v1/ingestion/kafka/stats

Performance Review:
1. GET /api/v1/ml-api/monitoring/top-models
2. GET /api/v1/ml-api/monitoring/slow-requests
3. GET /api/v1/ml-api/monitoring/request-rate

Troubleshooting:
1. GET /api/v1/ingestion/connectors → Check status
2. POST /api/v1/ingestion/connectors/newsapi/restart
3. GET /api/v1/ml-api/monitoring/export → Export metrics
```

---

## 📊 Monitoring Dashboard (Available via API)

Access real-time metrics:

```bash
# System overview
curl http://localhost:8000/api/v1/ml-api/monitoring/system

# Connector status
curl http://localhost:8000/api/v1/ingestion/connectors

# ML performance
curl http://localhost:8000/api/v1/ml-api/monitoring/models

# Kafka metrics
curl http://localhost:8000/api/v1/ingestion/kafka/stats
```

---

## 🎨 UI Status: Backend API Only

**Current Implementation:**
- ✅ Complete REST API (50+ endpoints)
- ✅ Interactive Swagger UI for testing
- ✅ API documentation
- ❌ No web dashboard
- ❌ No React/Vue frontend

**To Access the System:**
1. Use Swagger UI: `http://localhost:8000/docs`
2. Use curl/Postman for API calls
3. Build your own frontend using the REST API

**See UI_SPECIFICATION.md for frontend design specs if you want to build one!**

---

## 🚀 Getting Started

1. Start services: `docker-compose up -d`
2. Access Swagger UI: `http://localhost:8000/docs`
3. Try endpoints interactively
4. Monitor system: `/api/v1/ml-api/monitoring/system`

---

This is the complete workflow of your ISR Platform!
