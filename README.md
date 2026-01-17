# Afghanistan ISR Simulation & Analysis Platform

## Overview

A Military-Grade Intelligence, Surveillance & Reconnaissance (ISR) Simulation & Analysis Platform designed for Afghanistan and global security context. This platform provides comprehensive capabilities for:

- **Real-time and Historical Simulation** of security environments (border crossings, insurgent activity, infrastructure risk)
- **Multi-domain Data Fusion** combining satellite imagery, OSINT, cyber telemetry, and humanitarian data
- **AI/ML-powered Analytics** including threat scoring, anomaly detection, and explainable AI
- **Disaster & Crisis Modeling** for earthquakes, floods, and humanitarian response planning
- **Information Warfare Detection** monitoring disinformation campaigns and narrative analysis
- **Privacy-preserving Design** with anonymization and strict access controls

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System architecture, deployment topology, technology stack |
| [API Contracts](docs/API_CONTRACTS.md) | REST, GraphQL, and WebSocket API specifications |
| [Data Schemas](docs/DATA_SCHEMAS.md) | Database schemas, Kafka topics, data models |
| [ML Models](docs/ML_MODELS.md) | AI/ML model specifications, training strategies, explainability |
| [UI Specification](docs/UI_SPECIFICATION.md) | User interface behavior, dashboard design, interactions |
| [Security & Governance](docs/SECURITY_GOVERNANCE.md) | Security architecture, compliance, privacy, ethics |

## Architecture Highlights

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│   Web Dashboard │ Mobile App │ API Gateway │ Reporting      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CORE SERVICES                             │
│   Analytics Engine │ Simulation Engine │ Alerting Engine    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML ENGINE                              │
│   Visual Models │ NLP Models │ GNN │ Time-Series │ Anomaly  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│   PostgreSQL/PostGIS │ Elasticsearch │ Kafka │ Data Lake   │
└─────────────────────────────────────────────────────────────┘
```

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Sensor Fusion** | Correlate multi-source data (satellite, SIGINT, HUMINT) into unified tracks |
| **Threat Scoring** | Quantitative 0-100 threat assessment with explainable factors |
| **Anomaly Detection** | Real-time detection of unusual patterns in geo-movement, network, economics |
| **Simulation** | Agent-based simulation for what-if analysis and wargaming |
| **Disaster Modeling** | Physics-based earthquake/flood simulation with logistics optimization |
| **Narrative Analysis** | NLP-powered disinformation detection and campaign tracking |

## Technology Stack

| Layer | Technologies |
|-------|--------------|
| Frontend | React 18, TypeScript, Leaflet/Mapbox, D3.js |
| API | Kong Gateway, GraphQL, REST (OpenAPI 3.1) |
| Backend | Python, Go, Apache Kafka, Apache Flink |
| ML/AI | PyTorch, TensorFlow, XGBoost, Triton Inference Server |
| Database | PostgreSQL/PostGIS, Elasticsearch, Neo4j, Apache Iceberg |
| Infrastructure | Kubernetes, Istio, HashiCorp Vault, Prometheus/Grafana |

## Security & Compliance

- **Authentication**: Multi-factor authentication via Keycloak
- **Authorization**: RBAC + ABAC with XACML policy engine
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Privacy**: Data minimization, anonymization by default
- **Compliance**: NIST 800-53, GDPR principles
- **Audit**: Comprehensive logging with 7-year retention

## Ethical Principles

This platform is designed with ethical considerations at its core:

1. **Legality**: All operations comply with applicable laws
2. **Proportionality**: Data collection proportional to need
3. **Accountability**: Clear responsibility and audit trails
4. **Transparency**: Explainable AI for all automated decisions
5. **Non-maleficence**: Privacy protections, no invasive surveillance
6. **Human Dignity**: Respect for human rights, humanitarian focus

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+ with PostGIS extension (for production)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sturdy-potato
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Or run locally for development**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -e .

   # Run the API server
   uvicorn src.api.main:app --reload
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## Project Structure

```
sturdy-potato/
├── docs/                    # Design documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── API_CONTRACTS.md     # API specifications
│   ├── DATA_SCHEMAS.md      # Database schemas
│   ├── ML_MODELS.md         # ML model specs
│   ├── UI_SPECIFICATION.md  # UI design
│   └── SECURITY_GOVERNANCE.md # Security & compliance
├── src/                     # Source code
│   ├── api/                 # FastAPI application
│   │   ├── main.py          # Application entry point
│   │   └── routers/         # API route handlers
│   ├── config/              # Configuration
│   ├── models/              # Domain models
│   ├── schemas/             # API schemas (Pydantic)
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── docker-compose.yml       # Docker services
├── Dockerfile               # API container
├── pyproject.toml           # Python project config
└── requirements.txt         # Dependencies
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/login` | User authentication |
| `GET /api/v1/entities` | List tracked entities |
| `POST /api/v1/entities` | Create entity |
| `GET /api/v1/events` | List security events |
| `POST /api/v1/events` | Report event |
| `GET /api/v1/alerts` | List active alerts |
| `POST /api/v1/alerts/{id}/acknowledge` | Acknowledge alert |
| `POST /api/v1/analytics/threat-score` | Calculate threat score |
| `GET /api/v1/dashboard/overview` | Dashboard metrics |

## Project Status

This repository contains both design documentation and implementation for the ISR platform:

### Documentation (in `docs/`)
- Detailed architecture diagrams
- API specifications with examples
- Database schemas (PostgreSQL, Kafka Avro)
- ML model architectures and training strategies
- UI wireframes and interaction specifications
- Security controls and governance framework

### Implementation (in `src/`)
- FastAPI-based REST API
- Threat scoring service with explainable AI
- Anomaly detection service
- Authentication and authorization
- Entity, event, and alert management
- Dashboard and analytics endpoints

## Classification

**UNCLASSIFIED // FOR OFFICIAL USE ONLY**

---

*Document Version: 1.0*  
*Last Updated: 2026-01-17*