# ISR Platform - Complete Workflows Documentation

## 🎯 Overview

This document provides **step-by-step workflows** for all system operations, from initial setup to daily intelligence operations.

---

## 🚀 WORKFLOW 1: Initial System Setup (First Time)

### Prerequisites
- Docker & Docker Compose installed
- Git installed
- 8GB RAM minimum
- 20GB disk space

### Step-by-Step Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd sturdy-potato

# 2. Copy environment template
cp .env.example .env

# 3. Edit API keys (REQUIRED)
# Open .env and configure:
nano .env

# Minimum required:
# - SECRET_KEY (generate: openssl rand -hex 32)
# - NEWSAPI_API_KEY (get from: https://newsapi.org/)
# - GUARDIAN_API_KEY (get from: https://open-platform.theguardian.com/)

# Optional but recommended:
# - OPENAI_API_KEY (for LLM features)
# - WEATHER_API_KEY (for weather intelligence)

# 4. Start infrastructure services
docker-compose up -d postgres redis kafka zookeeper

# 5. Wait for services to be ready (30 seconds)
sleep 30

# 6. Run database migrations
python -m alembic upgrade head

# 7. Create initial admin user
python scripts/create_admin_user.py

# 8. (Optional) Seed test data
python scripts/seed_test_data.py

# 9. Start the API server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 10. In another terminal, start ingestion
python scripts/start_ingestion.py

# 11. In another terminal, start stream processor
python scripts/start_stream_processor.py
```

### Verification
```bash
# Check API health
curl http://localhost:8000/health

# Check ingestion status
curl http://localhost:8000/api/v1/ingestion/health

# Open Swagger UI
open http://localhost:8000/docs
```

---

## ⚡ WORKFLOW 2: Daily Startup (Regular Use)

```bash
# If services stopped, restart infrastructure
docker-compose up -d

# Start API
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Start ingestion (in another terminal)
python scripts/start_ingestion.py

# Start stream processor (in another terminal)
python scripts/start_stream_processor.py

# Access system
open http://localhost:8000/docs
```

---

## 📊 WORKFLOW 3: Intelligence Analyst - Morning Briefing

### Goal: Get situational awareness for the day

```bash
# 1. Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst1", "password": "yourpassword"}'

# Save token
export TOKEN="your_access_token_here"

# 2. Check critical alerts (last 24 hours)
curl -X GET "http://localhost:8000/api/v1/alerts?severity=CRITICAL&since=24h" \
  -H "Authorization: Bearer $TOKEN"

# 3. Get threat landscape overview
curl -X GET "http://localhost:8000/api/v1/analytics/threat-landscape" \
  -H "Authorization: Bearer $TOKEN"

# 4. Review recent events
curl -X GET "http://localhost:8000/api/v1/events?limit=20&sort=timestamp:desc" \
  -H "Authorization: Bearer $TOKEN"

# 5. Check entity updates (key persons/groups)
curl -X GET "http://localhost:8000/api/v1/entities?status=ACTIVE&updated_since=24h" \
  -H "Authorization: Bearer $TOKEN"

# 6. Review narratives (information campaigns)
curl -X GET "http://localhost:8000/api/v1/narratives?active=true" \
  -H "Authorization: Bearer $TOKEN"
```

### Expected Output
- 5-10 critical alerts requiring attention
- Threat level assessment by region
- Key events from last 24 hours
- Entity movement/activity updates
- Active propaganda/information campaigns

---

## 🔍 WORKFLOW 4: Field Agent - Submit Intelligence Report

### Scenario: Agent witnesses suspicious activity

#### Option A: Using API Directly
```bash
# 1. Agent authenticates
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "agent_field_01", "password": "agentpass"}'

export AGENT_TOKEN="agent_access_token"

# 2. Submit HUMINT report
curl -X POST http://localhost:8000/api/v1/field/submit-report \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "HUMINT",
    "priority": "HIGH",
    "title": "Suspicious Vehicle Movement",
    "description": "Observed convoy of 3 pickup trucks with mounted weapons heading north from Kandahar. Approximately 15-20 personnel. No markings visible.",
    "location": {
      "latitude": 31.6089,
      "longitude": 65.7372,
      "description": "Highway 1, 15km north of Kandahar"
    },
    "observed_at": "2024-01-15T14:30:00Z",
    "confidence": "HIGH",
    "classification": "SECRET",
    "entities_mentioned": ["Taliban", "Kandahar"],
    "attachments": []
  }'

# 3. Submit photo evidence (if available)
curl -X POST http://localhost:8000/api/v1/field/upload-media \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -F "file=@photo_evidence.jpg" \
  -F "report_id=<report_id_from_step2>" \
  -F "media_type=PHOTO"
```

#### Option B: Using Web Form (Future)
```
1. Open mobile app or web portal
2. Select "Submit Report"
3. Choose template: "Suspicious Activity"
4. Fill form:
   - What: Convoy movement
   - Where: Auto-detect GPS or manual entry
   - When: Auto-timestamp or select time
   - Priority: HIGH/MEDIUM/LOW
   - Details: Text description
5. Add photos/videos (optional)
6. Submit
7. Receive confirmation & report ID
```

---

## 🎯 WORKFLOW 5: Intelligence Analysis - Investigate Threat

### Scenario: Analyst investigating reported Taliban activity

```bash
export TOKEN="your_token"

# 1. Search for related intelligence
curl -X POST http://localhost:8000/api/v1/analytics/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Taliban Kandahar weapons",
    "time_range": "7d",
    "sources": ["HUMINT", "OSINT", "SIGINT"],
    "min_relevance": 0.7
  }'

# 2. Extract entities from intelligence
curl -X POST http://localhost:8000/api/v1/ml-api/ner/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Taliban commander Mullah Omar was spotted in Kandahar with convoy",
    "language": "en"
  }'

# 3. Assess threat level
curl -X POST http://localhost:8000/api/v1/analytics/threat-score \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "entity_uuid_here",
    "include_explanation": true,
    "context": {
      "time_window": "7d",
      "geographic_radius_km": 50
    }
  }'

# 4. Find similar incidents (pattern analysis)
curl -X POST http://localhost:8000/api/v1/ml-api/similarity \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "convoy movement with weapons",
    "top_k": 10,
    "time_range": "30d"
  }'

# 5. Generate intelligence report
curl -X POST http://localhost:8000/api/v1/llm/generate-report \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "threat_analysis",
    "entity_ids": ["entity1", "entity2"],
    "time_range": "7d",
    "classification": "SECRET",
    "include_recommendations": true
  }'
```

---

## 🚨 WORKFLOW 6: Alert Response - Critical Threat Detected

### Trigger: System detects high-confidence threat

```
Automated Flow:
1. ML Pipeline detects threat (score > 0.8)
   ↓
2. Alert created in database (severity: CRITICAL)
   ↓
3. Published to Kafka: isr.alerts.new
   ↓
4. Notification Service triggers:
   - Email to on-call analyst
   - SMS to duty officer
   - Slack channel alert
   - Dashboard popup
   ↓
5. Analyst Reviews Alert

Analyst Actions:
```

```bash
export TOKEN="analyst_token"

# 1. Get alert details
curl -X GET http://localhost:8000/api/v1/alerts/{alert_id} \
  -H "Authorization: Bearer $TOKEN"

# 2. Acknowledge alert (stops escalation)
curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/acknowledge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "acknowledged_by": "analyst_user_id",
    "notes": "Investigating. Correlating with SIGINT."
  }'

# 3. Get related intelligence
curl -X GET "http://localhost:8000/api/v1/alerts/{alert_id}/context" \
  -H "Authorization: Bearer $TOKEN"

# 4. Create investigation case
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Kandahar Threat Investigation",
    "priority": "HIGH",
    "related_alert_ids": ["{alert_id}"],
    "assigned_to": ["analyst1", "analyst2"]
  }'

# 5. After investigation, resolve alert
curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/resolve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "CONFIRMED_THREAT",
    "actions_taken": "Notified ground commander, increased ISR coverage",
    "case_id": "case_uuid"
  }'
```

---

## 📡 WORKFLOW 7: Data Ingestion - Add New Source

### Scenario: Add new news source

```bash
# 1. Configure new connector
# Edit .env file:
NEW_SOURCE_ENABLED=true
NEW_SOURCE_API_KEY=your_api_key
NEW_SOURCE_POLL_INTERVAL=900

# 2. Restart ingestion service
# Stop and restart: python scripts/start_ingestion.py

# 3. Verify connector started
curl http://localhost:8000/api/v1/ingestion/connectors

# Expected response:
{
  "connectors": [
    {"name": "newsapi", "status": "RUNNING", "last_run": "..."},
    {"name": "guardian", "status": "RUNNING", "last_run": "..."},
    {"name": "new_source", "status": "RUNNING", "last_run": "..."}
  ]
}

# 4. Monitor ingestion
curl http://localhost:8000/api/v1/ingestion/stats

# 5. Check Kafka topic for new data
# View topic: isr.osint.news
```

---

## 🤖 WORKFLOW 8: ML Pipeline - Analyze Custom Text

### Scenario: Analyst has unstructured text to analyze

```bash
export TOKEN="your_token"

# Complete analysis pipeline for a text:

# 1. Translate if needed (e.g., Pashto to English)
curl -X POST http://localhost:8000/api/v1/ml-api/translate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "د طالبانو پوځونه په کندهار کې",
    "source_lang": "ps",
    "target_lang": "en"
  }'

# 2. Extract entities
curl -X POST http://localhost:8000/api/v1/ml-api/ner/extract \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Taliban forces in Kandahar",
    "language": "en"
  }'

# 3. Analyze sentiment
curl -X POST http://localhost:8000/api/v1/ml-api/sentiment \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Taliban forces in Kandahar",
    "language": "en"
  }'

# 4. Classify topic
curl -X POST http://localhost:8000/api/v1/ml-api/classify \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Taliban forces in Kandahar",
    "categories": ["security_threat", "humanitarian", "political", "economic"]
  }'

# 5. Detect threat
curl -X POST http://localhost:8000/api/v1/ml-api/threat/detect \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Taliban forces in Kandahar",
    "include_details": true
  }'

# 6. Generate summary
curl -X POST http://localhost:8000/api/v1/ml-api/summarize \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Long text about Taliban operations...",
    "max_length": 100
  }'
```

---

## 📊 WORKFLOW 9: Reporting - Generate Intelligence Report

### Scenario: Weekly intelligence summary

```bash
export TOKEN="your_token"

# 1. Generate threat landscape report
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "threat_landscape",
    "time_range": "7d",
    "regions": ["Kabul", "Kandahar", "Helmand"],
    "classification": "SECRET",
    "format": "PDF",
    "include_charts": true,
    "include_recommendations": true
  }'

# 2. Generate entity profile
curl -X POST http://localhost:8000/api/v1/reports/entity-profile \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "entity_id": "taliban_commander_uuid",
    "include_associates": true,
    "include_timeline": true,
    "include_intelligence_summary": true
  }'

# 3. Generate situational report
curl -X POST http://localhost:8000/api/v1/reports/sitrep \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "region": "Kandahar Province",
    "time_range": "24h",
    "priority_items": ["security", "humanitarian"],
    "classification": "SECRET"
  }'

# 4. Download report
curl -X GET http://localhost:8000/api/v1/reports/{report_id}/download \
  -H "Authorization: Bearer $TOKEN" \
  --output report.pdf
```

---

## 🛠️ WORKFLOW 10: System Administration

### Daily Health Checks

```bash
# 1. Check API health
curl http://localhost:8000/health

# 2. Check service readiness
curl http://localhost:8000/ready

# 3. Check ingestion health
curl http://localhost:8000/api/v1/ingestion/health

# 4. Check ML system health
curl http://localhost:8000/api/v1/ml-api/monitoring/system

# 5. Check database connectivity
docker-compose exec postgres pg_isready

# 6. Check Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# 7. View ingestion statistics
curl http://localhost:8000/api/v1/ingestion/stats

# 8. View ML model performance
curl http://localhost:8000/api/v1/ml-api/monitoring/models
```

### Troubleshooting Common Issues

```bash
# Issue: Ingestion not working
# Solution: Restart connectors
curl -X POST http://localhost:8000/api/v1/ingestion/connectors/restart-all \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Issue: Kafka connection errors
# Solution: Restart Kafka
docker-compose restart kafka zookeeper

# Issue: Database connection errors
# Solution: Check database is running
docker-compose ps postgres
docker-compose logs postgres

# Issue: ML models not loading
# Solution: Check disk space and model cache
df -h
ls -lh ./models/

# Issue: API slow response
# Solution: Check Redis cache
docker-compose exec redis redis-cli PING
docker-compose exec redis redis-cli INFO stats
```

---

## 🔄 WORKFLOW 11: Data Pipeline - Complete Flow

### End-to-End Data Journey

```
External Source → Ingestion → Kafka → Stream Processor → ML Pipeline → Database → API → User

Example: News Article Processing
```

```
1. NEWS SOURCE (Guardian API)
   Article published: "Taliban attack in Kabul"
   ↓

2. INGESTION CONNECTOR
   - Fetches article every 15 minutes
   - Applies rate limiting
   - Handles errors with retry
   ↓

3. KAFKA TOPIC: isr.osint.news
   {
     "source": "guardian",
     "title": "Taliban attack in Kabul",
     "content": "...",
     "published_at": "2024-01-15T10:00:00Z",
     "url": "..."
   }
   ↓

4. STREAM PROCESSOR
   - Consumes from Kafka
   - Validates data
   - Enriches with metadata
   ↓

5. ML PIPELINE (Parallel Processing)
   ├─ NER: Extracts ["Taliban", "Kabul"]
   ├─ Sentiment: "negative" (0.82)
   ├─ Classification: "security_threat" (0.91)
   ├─ Threat Detection: HIGH (0.78)
   └─ Summarization: "Taliban forces attacked..."
   ↓

6. KAFKA TOPIC: isr.analytics.threat
   {
     "original_id": "...",
     "entities": ["Taliban", "Kabul"],
     "sentiment": "negative",
     "threat_score": 0.78,
     "threat_level": "HIGH",
     "summary": "..."
   }
   ↓

7. ALERT GENERATION (if threat_score > 0.7)
   - Create alert in database
   - Set severity: HIGH
   - Publish to: isr.alerts.new
   ↓

8. NOTIFICATION SERVICE
   - Email: analyst@example.com
   - SMS: Duty officer
   - Slack: #intelligence-alerts
   ↓

9. DATABASE STORAGE
   - alerts table: New record
   - events table: Incident record
   - entities table: Update Taliban entity
   ↓

10. API EXPOSURE
    GET /api/v1/alerts → Returns new alert
    ↓

11. ANALYST ACCESS
    - Dashboard shows alert
    - Email notification received
    - Analyst reviews and acknowledges
```

### Timeline: Real-Time Processing
```
T+0:00  - Article published by Guardian
T+0:15  - Ingestion connector fetches article
T+0:16  - Published to Kafka (isr.osint.news)
T+0:17  - Stream processor consumes message
T+0:18  - ML pipeline processes (NER, sentiment, threat)
T+0:20  - Enriched data published to analytics topic
T+0:21  - Alert generated (if threshold met)
T+0:22  - Notification sent to analyst
T+0:23  - Available via API

Total: 23 seconds from publication to analyst notification
```

---

## 🎯 WORKFLOW 12: LLM-Powered Intelligence

### Using AI for Advanced Analysis

```bash
export TOKEN="your_token"

# 1. Conversational Intelligence Query
curl -X POST http://localhost:8000/api/v1/llm/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the current threat trends in Kandahar province?",
    "include_context": true,
    "max_tokens": 500
  }'

# 2. Automated Insight Discovery
curl -X POST http://localhost:8000/api/v1/llm/discover-insights \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "time_range": "7d",
    "regions": ["Kandahar", "Helmand"],
    "focus_areas": ["security", "humanitarian"]
  }'

# 3. Predictive Intelligence
curl -X POST http://localhost:8000/api/v1/llm/predict \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "entity_id": "taliban_entity_uuid",
    "prediction_window": "48h",
    "include_confidence": true
  }'

# 4. Anomaly Explanation
curl -X POST http://localhost:8000/api/v1/llm/explain-anomaly \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "anomaly_id": "anomaly_uuid",
    "request_recommendations": true
  }'

# 5. Intelligent Report Generation
curl -X POST http://localhost:8000/api/v1/llm/generate-report \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "report_type": "executive_summary",
    "time_range": "7d",
    "classification": "SECRET",
    "tone": "formal",
    "include_recommendations": true
  }'
```

---

## 📱 WORKFLOW 13: Field Agent Mobile Operations (Future)

### Mobile App Workflow

```
MORNING:
1. Agent opens mobile app
2. Receives daily briefing push notification
3. Reviews assigned patrol route
4. Downloads offline map data (in case no signal)

DURING PATROL:
1. Agent moves through area
2. App tracks GPS location (optional)
3. Agent observes suspicious activity
4. Quick action: Tap "Report Incident"
5. Select template: "Suspicious Vehicle"
6. Auto-fill: Location (GPS), Time (now)
7. Add: Description (voice-to-text)
8. Take: Photos with camera
9. Submit: Queues if offline, sends when online

INTEL SUBMISSION:
1. Report arrives at server
2. Appears in analyst queue immediately
3. ML pipeline auto-analyzes
4. If high threat, generates alert
5. Analyst reviews within minutes
6. Can request clarification from agent

AGENT RECEIVES:
1. Acknowledgment notification
2. Report ID for tracking
3. Any questions from analysts
4. Relevant alerts for their location
```

---

## 🎓 Quick Reference Commands

### Most Common Operations

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"username":"user","password":"pass"}'

# Get alerts
curl -X GET http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN"

# Submit report
curl -X POST http://localhost:8000/api/v1/field/submit-report \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"...","description":"...","priority":"HIGH"}'

# Analyze text
curl -X POST http://localhost:8000/api/v1/ml-api/threat/detect \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text":"suspicious activity..."}'

# Generate report
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"report_type":"sitrep","time_range":"24h"}'

# Check system health
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/ingestion/health
curl http://localhost:8000/api/v1/ml-api/monitoring/system
```

---

This completes the comprehensive workflow documentation for the ISR Platform!
