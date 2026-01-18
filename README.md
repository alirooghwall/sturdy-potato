# Afghanistan ISR Simulation & Analysis Platform

A military-grade Intelligence, Surveillance, and Reconnaissance (ISR) simulation and analysis platform for Afghanistan. This platform integrates multi-domain data fusion, AI/ML analytics, real-time simulation, and decision support capabilities.

## 🎯 Features

### Core Capabilities

- **Multi-Domain Data Fusion**: Integrate satellite imagery, OSINT, social media, cyber telemetry, and humanitarian data
- **AI/ML Analytics**: Threat scoring, anomaly detection, narrative analysis, and time-series forecasting
- **Simulation Engine**: Agent-based modeling, disaster simulation, historical scenario replay
- **Real-Time Dashboard**: Situational awareness, alerts, and interactive maps
- **Report Generation**: Automated SITREP, threat assessments, and custom reports

### Realistic Afghanistan Data

- **34 Provinces**: Complete geographic data with coordinates, populations, and risk levels
- **20+ Major Cities**: Population centers with demographics
- **12 Border Crossings**: Pakistan, Iran, Turkmenistan, Uzbekistan, Tajikistan borders
- **Threat Groups**: Taliban, ISIS-K, Haqqani Network intelligence profiles
- **Humanitarian Data**: IDP statistics, food security, and crisis indicators
- **9 Simulation Scenarios**: Historical battles, disasters, humanitarian crises

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ISR Platform Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Satellite  │  │    OSINT    │  │   Cyber     │  Data        │
│  │   Imagery   │  │ Social Media│  │  Telemetry  │  Sources     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │   Kafka Message Bus   │                          │
│              └───────────┬───────────┘                          │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  FastAPI Backend                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │  │
│  │  │Analytics│  │Simulation│  │Narrative│  │ Reports │       │  │
│  │  │ Engine  │  │  Engine  │  │Analysis │  │Generator│       │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│         ┌────────────────┼────────────────┐                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ PostgreSQL  │  │    Redis    │  │   ML Models │              │
│  │  + PostGIS  │  │    Cache    │  │   Service   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for full stack)
- PostgreSQL with PostGIS (or use Docker)

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd isr-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run the API
uvicorn src.api.main:app --reload
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Set required environment variables
export SECRET_KEY="your-secure-secret-key"
export DB_PASSWORD="your-db-password"

# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints Overview

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Auth** | `POST /api/v1/auth/login` | JWT authentication |
| **Entities** | `GET/POST /api/v1/entities` | Entity management |
| **Events** | `GET/POST /api/v1/events` | Security/humanitarian events |
| **Alerts** | `GET/POST /api/v1/alerts` | Alert management |
| **Analytics** | `POST /api/v1/analytics/threat-score` | Threat scoring |
| **Analytics** | `POST /api/v1/analytics/anomaly-detection/*` | Anomaly detection |
| **Simulations** | `GET/POST /api/v1/simulations` | Simulation management |
| **Narratives** | `POST /api/v1/narratives/analyze` | Narrative analysis |
| **ML Models** | `GET /api/v1/ml/models` | ML model management |
| **Reports** | `POST /api/v1/reports` | Report generation |
| **Dashboard** | `GET /api/v1/dashboard/*` | Dashboard data |

### Authentication

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token in requests
curl http://localhost:8000/api/v1/dashboard/overview \
  -H "Authorization: Bearer <your-token>"
```

## 🗺️ Available Simulation Scenarios

| Category | Scenario | Description |
|----------|----------|-------------|
| **Historical** | Tora Bora 2001 | December 2001 battle in White Mountains |
| **Historical** | Kunduz 2015 | Taliban capture of Kunduz city |
| **Disaster** | Herat Earthquake | Based on 2023 earthquake response |
| **Disaster** | Kabul Flood | Flash flood scenario |
| **Humanitarian** | Refugee Crisis | Mass displacement simulation |
| **Humanitarian** | Drought Response | Northern Afghanistan drought |
| **What-If** | Border Surge | Border crossing capacity analysis |
| **What-If** | Multi-Axis Attack | Coordinated attack response |
| **Training** | Checkpoint Ops | Security checkpoint training |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `SECRET_KEY` | JWT secret key | Required in production |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka servers | `localhost:9092` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| `VIEWER` | Read-only dashboard access |
| `ANALYST` | + Alert management, reports, simulations |
| `SENIOR_ANALYST` | + Entity/event management |
| `OPERATOR` | + System configuration |
| `ADMIN` | + User management |
| `SUPER_ADMIN` | Full system access |

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_simulation.py -v
```

### Test Coverage

- **99 Tests** covering:
  - API endpoints (22 tests)
  - Threat scoring (10 tests)
  - Anomaly detection (9 tests)
  - Simulation engine (14 tests)
  - Narrative analysis (14 tests)
  - Report generation (15 tests)
  - Kafka messaging (15 tests)

## 📁 Project Structure

```
isr-platform/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   └── routers/             # API endpoints
│   ├── config/
│   │   └── settings.py          # Configuration
│   ├── data/
│   │   ├── afghanistan.py       # Geographic data
│   │   ├── sample_data.py       # Sample entities/events
│   │   └── scenarios.py         # Simulation scenarios
│   ├── models/
│   │   ├── domain.py            # Domain models
│   │   ├── enums.py             # Enumerations
│   │   └── orm.py               # SQLAlchemy ORM
│   ├── schemas/
│   │   └── api.py               # Pydantic schemas
│   └── services/
│       ├── anomaly_detection.py
│       ├── auth.py
│       ├── kafka_bus.py
│       ├── ml_models.py
│       ├── narrative_analysis.py
│       ├── report_generator.py
│       ├── simulation_engine.py
│       └── threat_scoring.py
├── tests/                       # Test suite
├── scripts/
│   └── init-db.sql             # Database initialization
├── alembic/                     # Database migrations
├── docker-compose.yml           # Development stack
├── docker-compose.prod.yml      # Production stack
└── Dockerfile
```

## 🔒 Security

- **JWT Authentication** with configurable expiration
- **Role-Based Access Control (RBAC)** with 6 roles
- **Audit Logging** for all actions
- **Data Classification** support (UNCLASSIFIED to TOP SECRET)
- **Privacy-by-Design** with anonymization options

## 📊 ML Models

| Model | Type | Purpose |
|-------|------|---------|
| `yolov8-military` | Visual Detection | Military vehicle/equipment detection |
| `resnet-satellite` | Classification | Satellite imagery classification |
| `xlm-roberta-dari` | NLP | Dari/Pashto text classification |
| `xlm-roberta-ner` | NER | Multilingual entity extraction |
| `lstm-displacement` | Time Series | Population displacement forecasting |
| `prophet-threat` | Time Series | Threat level forecasting |
| `autoencoder-network` | Anomaly | Network traffic anomaly detection |
| `gnn-network` | Graph | Relationship analysis |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This platform is designed for simulation, analysis, and training purposes. It uses publicly available geographic and demographic data. No personal surveillance capabilities are included. All data processing follows privacy-by-design principles.

---

**Built with** ❤️ **for situational awareness and decision support**
