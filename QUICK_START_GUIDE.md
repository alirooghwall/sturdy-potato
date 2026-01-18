# ISR Platform - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Git
- 8GB RAM minimum

---

## Option 1: Automated Setup (Recommended)

### Step 1: Clone & Configure
```bash
git clone <your-repo-url>
cd sturdy-potato

# Copy environment template
cp .env.example .env
```

### Step 2: Configure API Keys
Edit `.env` and add your API keys:

```bash
# REQUIRED - Generate secret key
SECRET_KEY=your_random_secret_key_here  # Generate: openssl rand -hex 32

# RECOMMENDED - For news ingestion
NEWSAPI_API_KEY=your_newsapi_key        # Get from: https://newsapi.org
GUARDIAN_API_KEY=your_guardian_key      # Get from: https://open-platform.theguardian.com

# OPTIONAL - For LLM features
OPENAI_API_KEY=your_openai_key          # Get from: https://platform.openai.com
```

### Step 3: Run Startup Script
```bash
# Make script executable
chmod +x scripts/start_platform.sh scripts/stop_platform.sh

# Start everything
./scripts/start_platform.sh
```

That's it! The script will:
✅ Start Docker services (PostgreSQL, Redis, Kafka)
✅ Run database migrations
✅ Create admin user
✅ Start API server
✅ Start data ingestion
✅ Show you access URLs

---

## Option 2: Manual Setup

### Step 1: Start Infrastructure
```bash
docker-compose up -d postgres redis kafka zookeeper
```

### Step 2: Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Initialize Database
```bash
# Run migrations
python -m alembic upgrade head

# Create admin user
python scripts/create_admin_user.py
```

### Step 4: Start Services
```bash
# Terminal 1: API Server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Data Ingestion
python scripts/start_ingestion.py

# Terminal 3: Stream Processor
python scripts/start_stream_processor.py
```

---

## 🎯 Access the Platform

### Web Interfaces
- **Swagger UI (API Docs):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Default Login
- **Username:** `admin`
- **Password:** `changeme`

⚠️ **Change default password immediately!**

---

## 📋 First Steps After Installation

### 1. Test Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "service": "isr-platform-api"
}
```

### 2. Get Authentication Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}'
```

Save the `access_token` from response.

### 3. Configure API Keys (via UI)
1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Enter your token: `Bearer <your_token>`
4. Navigate to **Administration** section
5. Use `/api/v1/admin/config` to view/update API keys
6. Test keys with `/api/v1/admin/config/test-api-key`

### 4. Submit Your First Intelligence Report
```bash
# Using the field agent endpoint
curl -X POST http://localhost:8000/api/v1/field/submit-report \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "OBSERVATION",
    "priority": "MEDIUM",
    "title": "Test Report",
    "description": "Testing the field submission system",
    "location": {
      "latitude": 34.5553,
      "longitude": 69.2075,
      "description": "Kabul city center"
    },
    "observed_at": "2024-01-15T14:30:00Z",
    "confidence": "HIGH",
    "classification": "UNCLASSIFIED",
    "entities_mentioned": ["Test"],
    "tags": ["test"]
  }'
```

### 5. Try ML Analysis
```bash
# Analyze text for threats
curl -X POST http://localhost:8000/api/v1/ml-api/threat/detect \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Suspicious vehicle movement near checkpoint",
    "include_details": true
  }'
```

---

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Application
APP_NAME=ISR Platform
DEBUG=true                          # Set false in production
ENVIRONMENT=development

# Security
SECRET_KEY=<random-key>             # REQUIRED
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/isr_platform

# Ingestion
INGESTION_AUTO_START=true           # Auto-start data collection
NEWSAPI_API_KEY=<your-key>
GUARDIAN_API_KEY=<your-key>
NYTIMES_API_KEY=<your-key>

# LLM (Optional)
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>

# ML
USE_ML_PROCESSING=true
ENABLE_GPU=false                    # Set true if CUDA available
```

---

## 📊 Verify Everything Works

### Check API
```bash
curl http://localhost:8000/health
```

### Check Dependencies
```bash
curl http://localhost:8000/ready
```

Should return status of:
- ✅ Database (PostgreSQL)
- ✅ Cache (Redis)
- ✅ Message Bus (Kafka)

### Check Ingestion
```bash
curl http://localhost:8000/api/v1/ingestion/health
```

### Check ML System
```bash
curl http://localhost:8000/api/v1/ml-api/monitoring/system
```

---

## 🎓 Next Steps

### 1. Explore the API
Visit http://localhost:8000/docs and try endpoints:
- **Field Agents:** Submit intelligence reports
- **ML Analysis:** Analyze text, extract entities, detect threats
- **Analytics:** View threat landscape, entity relationships
- **Alerts:** View and manage alerts
- **Reports:** Generate intelligence reports

### 2. Create Additional Users
```bash
# Create analyst user (via API)
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "analyst1",
    "email": "analyst1@example.com",
    "password": "securepassword",
    "roles": ["analyst"]
  }'
```

### 3. Configure Data Sources
1. Get API keys from providers (see API_KEYS_SETUP.md)
2. Add keys to `.env` or via admin config UI
3. Restart ingestion or use runtime config update

### 4. Read Documentation
- **COMPLETE_WORKFLOWS.md** - Detailed workflows for all operations
- **SYSTEM_ANALYSIS_AND_AMBIGUITIES.md** - Features and roadmap
- **docs/COMPLETE_WORKFLOW.md** - Technical architecture
- **docs/ML_INTEGRATION_GUIDE.md** - ML capabilities

---

## 🛑 Stopping the Platform

### Using Script
```bash
./scripts/stop_platform.sh
```

### Manual Stop
```bash
# Stop Python processes
kill $(cat .api.pid)
kill $(cat .ingestion.pid)
kill $(cat .processor.pid)

# Stop Docker services
docker-compose down
```

---

## 🐛 Troubleshooting

### API Won't Start
```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill existing process
lsof -ti:8000 | xargs kill -9

# Check logs
tail -f logs/api.log
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Kafka Connection Error
```bash
# Check Kafka is running
docker-compose ps kafka

# Restart Kafka cluster
docker-compose restart kafka zookeeper
```

### Ingestion Not Working
```bash
# Check logs
tail -f logs/ingestion.log

# Verify API keys are set
grep API_KEY .env

# Test API key
curl -X POST http://localhost:8000/api/v1/admin/config/test-api-key \
  -H "Authorization: Bearer <token>" \
  -d '{"service": "newsapi", "api_key": "your_key"}'
```

### ML Models Not Loading
```bash
# Check disk space
df -h

# Check model cache directory
ls -lh ./models/

# Clear cache and restart
rm -rf ./models/*
./scripts/stop_platform.sh
./scripts/start_platform.sh
```

---

## 📚 Additional Resources

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Guides
- [Complete Workflows](COMPLETE_WORKFLOWS.md)
- [ML Integration](docs/ML_INTEGRATION_GUIDE.md)
- [API Contracts](docs/API_CONTRACTS.md)
- [Data Ingestion](docs/INGESTION_GUIDE.md)

### Getting API Keys
- NewsAPI: https://newsapi.org/register
- The Guardian: https://open-platform.theguardian.com/access/
- NY Times: https://developer.nytimes.com/get-started
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

---

## ✅ Quick Checklist

- [ ] Docker installed and running
- [ ] Python 3.10+ installed
- [ ] `.env` file created with API keys
- [ ] `SECRET_KEY` generated and set
- [ ] Database migrations run
- [ ] Admin user created
- [ ] API accessible at http://localhost:8000
- [ ] Can login and get token
- [ ] Health checks passing
- [ ] At least one API key configured
- [ ] Ingestion running
- [ ] Submitted test report

---

## 🎉 You're Ready!

Your ISR Platform is now running. Start submitting intelligence, analyzing threats, and generating reports!

For detailed workflows, see **COMPLETE_WORKFLOWS.md**.

For questions or issues, check the troubleshooting section above or review the documentation in the `docs/` folder.
