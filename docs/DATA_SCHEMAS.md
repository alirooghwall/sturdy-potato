# Afghanistan ISR Platform - Data Schemas

## 1. Overview

This document defines the data schemas for the Afghanistan ISR Simulation & Analysis Platform. All schemas follow a consistent design philosophy emphasizing:

- **Privacy by Design**: Personal identifiers anonymized/pseudonymized by default
- **Temporal Awareness**: All records include valid-time and transaction-time semantics
- **Geospatial Integration**: Native support for PostGIS geometry types
- **Schema Evolution**: Designed for backward-compatible changes
- **Interoperability**: Aligned with STIX 2.1, OGC, and NIEM standards where applicable

---

## 2. Core Domain Schemas

### 2.1 Entity Schema

The foundational schema for all tracked entities in the system.

```sql
-- PostgreSQL Schema
CREATE SCHEMA isr_core;

CREATE TYPE isr_core.entity_type AS ENUM (
    'VEHICLE', 'PERSONNEL', 'FACILITY', 'AIRCRAFT', 
    'WATERCRAFT', 'COMMUNICATION_DEVICE', 'WEAPON_SYSTEM',
    'INSURGENT_CELL', 'MILITARY_UNIT', 'CONVOY', 'ORGANIZATION'
);

CREATE TYPE isr_core.entity_status AS ENUM (
    'ACTIVE', 'INACTIVE', 'UNKNOWN', 'DESTROYED', 'ARCHIVED'
);

CREATE TABLE isr_core.entities (
    entity_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type         isr_core.entity_type NOT NULL,
    entity_subtype      VARCHAR(100),
    display_name        VARCHAR(255),
    
    -- Anonymization: No direct personal identifiers
    -- Use opaque IDs that link to separate identity store (if needed)
    
    status              isr_core.entity_status DEFAULT 'ACTIVE',
    confidence_score    DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    first_observed      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_observed       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Current position (denormalized for query performance)
    current_position    GEOGRAPHY(POINT, 4326),
    current_position_accuracy_m DECIMAL(10,2),
    
    -- Attributes stored as JSONB for flexibility
    attributes          JSONB DEFAULT '{}',
    
    -- Classification and handling
    classification      VARCHAR(50) DEFAULT 'UNCLASSIFIED',
    handling_caveats    VARCHAR(255)[],
    
    -- Audit fields
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    created_by          VARCHAR(100),
    updated_by          VARCHAR(100),
    
    -- Soft delete
    is_deleted          BOOLEAN DEFAULT FALSE,
    deleted_at          TIMESTAMPTZ,
    
    CONSTRAINT entity_dates_valid CHECK (last_observed >= first_observed)
);

-- Spatial index for geographic queries
CREATE INDEX idx_entities_current_position 
    ON isr_core.entities USING GIST (current_position);

-- Index for type-based queries
CREATE INDEX idx_entities_type_status 
    ON isr_core.entities (entity_type, status);

-- Index for temporal queries
CREATE INDEX idx_entities_last_observed 
    ON isr_core.entities (last_observed DESC);
```

### JSON Schema for Entity Attributes

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://isr-platform.mil/schemas/entity-attributes.json",
  "title": "Entity Attributes",
  "type": "object",
  "properties": {
    "vehicle": {
      "type": "object",
      "properties": {
        "vehicleType": {
          "type": "string",
          "enum": ["SEDAN", "SUV", "PICKUP", "TRUCK", "BUS", "MOTORCYCLE", "TECHNICAL", "APC", "TANK", "UNKNOWN"]
        },
        "color": { "type": "string" },
        "estimatedOccupants": { "type": "integer", "minimum": 0 },
        "weaponsVisible": { "type": "boolean" },
        "licensePlateObfuscated": { "type": "string" }
      }
    },
    "insurgentCell": {
      "type": "object",
      "properties": {
        "estimatedSize": { "type": "integer", "minimum": 1 },
        "affiliatedGroup": { "type": "string" },
        "operationalCapability": {
          "type": "string",
          "enum": ["LIMITED", "MODERATE", "SIGNIFICANT", "UNKNOWN"]
        },
        "knownTTPs": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "facility": {
      "type": "object",
      "properties": {
        "facilityType": {
          "type": "string",
          "enum": ["COMPOUND", "SAFEHOUSE", "TRAINING_CAMP", "WEAPONS_CACHE", "IED_FACTORY", "COMMAND_CENTER", "CHECKPOINT", "UNKNOWN"]
        },
        "estimatedCapacity": { "type": "integer" },
        "lastActivityObserved": { "type": "string", "format": "date-time" }
      }
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "uniqueItems": true
    },
    "notes": { "type": "string", "maxLength": 5000 }
  },
  "additionalProperties": true
}
```

### 2.2 Track Schema

Time-series position and state data for entities.

```sql
-- TimescaleDB hypertable for time-series optimization
CREATE TABLE isr_core.tracks (
    track_id            UUID DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES isr_core.entities(entity_id),
    
    -- Temporal dimensions
    observation_time    TIMESTAMPTZ NOT NULL,
    ingestion_time      TIMESTAMPTZ DEFAULT NOW(),
    
    -- Position
    position            GEOGRAPHY(POINT, 4326) NOT NULL,
    altitude_m          DECIMAL(10,2),
    position_accuracy_m DECIMAL(10,2),
    
    -- Motion
    speed_mps           DECIMAL(10,2),
    heading_degrees     DECIMAL(5,2) CHECK (heading_degrees BETWEEN 0 AND 360),
    
    -- State
    confidence_score    DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Source attribution
    primary_source_type VARCHAR(50) NOT NULL,
    primary_source_id   VARCHAR(100),
    contributing_sources JSONB DEFAULT '[]',
    
    -- Fusion metadata
    is_fused            BOOLEAN DEFAULT FALSE,
    fusion_method       VARCHAR(50),
    
    PRIMARY KEY (entity_id, observation_time)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('isr_core.tracks', 'observation_time');

-- Compression policy for older data
ALTER TABLE isr_core.tracks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'entity_id'
);

SELECT add_compression_policy('isr_core.tracks', INTERVAL '7 days');

-- Spatial-temporal index
CREATE INDEX idx_tracks_position_time 
    ON isr_core.tracks USING GIST (position, observation_time);
```

### 2.3 Event Schema

Discrete events detected or reported in the operational environment.

```sql
CREATE TYPE isr_core.event_type AS ENUM (
    'EXPLOSION', 'GUNFIRE', 'IED_DETONATION', 'IED_DISCOVERED',
    'BORDER_CROSSING', 'CHECKPOINT_INCIDENT', 'ATTACK', 'AMBUSH',
    'KIDNAPPING', 'ASSASSINATION', 'DEMONSTRATION', 'RIOT',
    'DRUG_SEIZURE', 'WEAPONS_SEIZURE', 'ARREST', 'SURRENDER',
    'HUMANITARIAN_CRISIS', 'NATURAL_DISASTER', 'INFRASTRUCTURE_FAILURE',
    'COMMUNICATION_INTERCEPT', 'CYBER_INCIDENT', 'INFORMATION_OPERATION',
    'OTHER'
);

CREATE TYPE isr_core.event_severity AS ENUM (
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
);

CREATE TABLE isr_core.events (
    event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type          isr_core.event_type NOT NULL,
    event_subtype       VARCHAR(100),
    severity            isr_core.event_severity NOT NULL,
    
    -- Temporal
    occurred_at         TIMESTAMPTZ,
    occurred_at_precision VARCHAR(20) DEFAULT 'EXACT', -- EXACT, HOUR, DAY, APPROXIMATE
    reported_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Spatial
    location            GEOGRAPHY(GEOMETRY, 4326), -- Supports POINT, POLYGON, etc.
    location_description VARCHAR(500),
    region              VARCHAR(100),
    province            VARCHAR(100),
    district            VARCHAR(100),
    
    -- Description
    title               VARCHAR(255) NOT NULL,
    summary             TEXT,
    details             JSONB DEFAULT '{}',
    
    -- Impact assessment
    casualties_killed   INTEGER,
    casualties_wounded  INTEGER,
    damage_assessment   TEXT,
    population_affected INTEGER,
    
    -- Attribution
    attributed_to       UUID REFERENCES isr_core.entities(entity_id),
    attribution_confidence DECIMAL(3,2),
    
    -- Verification
    verification_status VARCHAR(50) DEFAULT 'UNVERIFIED',
    verified_by         VARCHAR(100),
    verified_at         TIMESTAMPTZ,
    
    -- Sources
    sources             JSONB DEFAULT '[]',
    
    -- Classification
    classification      VARCHAR(50) DEFAULT 'UNCLASSIFIED',
    handling_caveats    VARCHAR(255)[],
    
    -- Audit
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    created_by          VARCHAR(100),
    
    is_deleted          BOOLEAN DEFAULT FALSE
);

-- Spatial index
CREATE INDEX idx_events_location ON isr_core.events USING GIST (location);

-- Temporal index
CREATE INDEX idx_events_occurred_at ON isr_core.events (occurred_at DESC);

-- Type and severity index
CREATE INDEX idx_events_type_severity ON isr_core.events (event_type, severity);
```

---

## 3. Analytics Schemas

### 3.1 Threat Score Schema

```sql
CREATE SCHEMA isr_analytics;

CREATE TABLE isr_analytics.threat_scores (
    score_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES isr_core.entities(entity_id),
    
    -- Score
    overall_score       INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    category            VARCHAR(20) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    
    -- Factor breakdown
    factor_scores       JSONB NOT NULL,
    /*
    Example:
    {
        "credibility": {"score": 85, "weight": 0.20, "contribution": 17},
        "tacticalImpact": {"score": 72, "weight": 0.25, "contribution": 18},
        "capability": {"score": 68, "weight": 0.20, "contribution": 13.6},
        "vulnerability": {"score": 80, "weight": 0.20, "contribution": 16},
        "timeSensitivity": {"score": 65, "weight": 0.15, "contribution": 9.75}
    }
    */
    
    -- Explanation (XAI)
    explanation_summary TEXT,
    key_indicators      TEXT[],
    recommendations     TEXT[],
    
    -- Model metadata
    model_id            VARCHAR(100) NOT NULL,
    model_version       VARCHAR(50) NOT NULL,
    
    -- Context
    context_window_start TIMESTAMPTZ NOT NULL,
    context_window_end  TIMESTAMPTZ NOT NULL,
    
    -- Temporal
    calculated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until         TIMESTAMPTZ,
    
    -- For time-series tracking
    previous_score      INTEGER,
    score_change        INTEGER,
    trend_direction     VARCHAR(20) -- INCREASING, DECREASING, STABLE
);

-- Index for entity lookups
CREATE INDEX idx_threat_scores_entity ON isr_analytics.threat_scores (entity_id, calculated_at DESC);

-- Index for high-priority monitoring
CREATE INDEX idx_threat_scores_high ON isr_analytics.threat_scores (overall_score DESC) 
    WHERE overall_score >= 70;
```

### 3.2 Anomaly Detection Schema

```sql
CREATE TYPE isr_analytics.anomaly_domain AS ENUM (
    'GEO_MOVEMENT', 'NETWORK_TRAFFIC', 'ECONOMIC', 'SOCIAL_MEDIA',
    'COMMUNICATION', 'IMAGERY', 'MULTI_DOMAIN'
);

CREATE TABLE isr_analytics.anomalies (
    anomaly_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain              isr_analytics.anomaly_domain NOT NULL,
    anomaly_subtype     VARCHAR(100),
    
    -- Severity
    severity            VARCHAR(20) NOT NULL,
    severity_score      INTEGER CHECK (severity_score BETWEEN 0 AND 100),
    
    -- Detection
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    detection_window_start TIMESTAMPTZ,
    detection_window_end TIMESTAMPTZ,
    
    -- Location (if applicable)
    location            GEOGRAPHY(GEOMETRY, 4326),
    region              VARCHAR(100),
    
    -- Description
    description         TEXT NOT NULL,
    
    -- Statistical basis
    baseline_stats      JSONB,
    /*
    Example:
    {
        "period": "30_DAYS",
        "averageCount": 3.2,
        "standardDeviation": 1.1,
        "observedCount": 27,
        "zScore": 21.6
    }
    */
    
    -- Model info
    model_id            VARCHAR(100),
    model_version       VARCHAR(50),
    anomaly_score       DECIMAL(5,4),
    
    -- Related entities
    related_entities    UUID[],
    related_events      UUID[],
    
    -- Status
    status              VARCHAR(50) DEFAULT 'OPEN',
    reviewed_by         VARCHAR(100),
    reviewed_at         TIMESTAMPTZ,
    review_notes        TEXT,
    false_positive      BOOLEAN DEFAULT FALSE,
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial index
CREATE INDEX idx_anomalies_location ON isr_analytics.anomalies USING GIST (location);

-- Domain and severity index
CREATE INDEX idx_anomalies_domain_severity ON isr_analytics.anomalies (domain, severity, detected_at DESC);
```

### 3.3 Sensor Fusion Schema

```sql
CREATE TABLE isr_analytics.fusion_sessions (
    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_start       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end         TIMESTAMPTZ,
    
    -- Configuration
    fusion_algorithm    VARCHAR(100) NOT NULL, -- 'KALMAN', 'BAYESIAN', 'DEMPSTER_SHAFER'
    config_parameters   JSONB,
    
    -- Coverage
    spatial_bounds      GEOGRAPHY(POLYGON, 4326),
    
    -- Statistics
    tracks_processed    INTEGER DEFAULT 0,
    tracks_merged       INTEGER DEFAULT 0,
    duplicates_removed  INTEGER DEFAULT 0,
    
    -- Quality metrics
    average_confidence  DECIMAL(3,2),
    
    status              VARCHAR(50) DEFAULT 'RUNNING'
);

CREATE TABLE isr_analytics.fusion_contributions (
    contribution_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id            UUID NOT NULL,
    entity_id           UUID NOT NULL REFERENCES isr_core.entities(entity_id),
    session_id          UUID REFERENCES isr_analytics.fusion_sessions(session_id),
    
    -- Source
    source_type         VARCHAR(50) NOT NULL,
    source_id           VARCHAR(100),
    
    -- Contribution weight
    weight              DECIMAL(5,4) NOT NULL,
    confidence          DECIMAL(3,2),
    
    -- Timing
    observation_time    TIMESTAMPTZ NOT NULL,
    processing_time     TIMESTAMPTZ DEFAULT NOW(),
    
    -- Raw data reference
    raw_data_ref        VARCHAR(255)
);

-- Index for track assembly
CREATE INDEX idx_fusion_contributions_track 
    ON isr_analytics.fusion_contributions (track_id, observation_time);
```

---

## 4. Simulation Schemas

### 4.1 Scenario Schema

```sql
CREATE SCHEMA isr_simulation;

CREATE TYPE isr_simulation.scenario_type AS ENUM (
    'WHAT_IF', 'REPLAY', 'WARGAME', 'TRAINING', 'DISASTER'
);

CREATE TYPE isr_simulation.scenario_status AS ENUM (
    'DRAFT', 'READY', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'ARCHIVED'
);

CREATE TABLE isr_simulation.scenarios (
    scenario_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    scenario_type       isr_simulation.scenario_type NOT NULL,
    
    -- Temporal bounds
    baseline_date       TIMESTAMPTZ NOT NULL,
    duration_seconds    INTEGER NOT NULL,
    
    -- Spatial bounds
    region              GEOGRAPHY(POLYGON, 4326) NOT NULL,
    
    -- Initial conditions
    initial_conditions  JSONB NOT NULL,
    /*
    Example:
    {
        "agents": [...],
        "environment": {...},
        "events": [...]
    }
    */
    
    -- Objectives and metrics
    objectives          JSONB,
    
    -- Execution config
    stochastic_runs     INTEGER DEFAULT 1,
    random_seed         BIGINT,
    
    -- Status
    status              isr_simulation.scenario_status DEFAULT 'DRAFT',
    
    -- Ownership
    created_by          VARCHAR(100) NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    -- Versioning
    version             INTEGER DEFAULT 1,
    parent_scenario_id  UUID REFERENCES isr_simulation.scenarios(scenario_id)
);

CREATE TABLE isr_simulation.simulation_runs (
    run_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id         UUID NOT NULL REFERENCES isr_simulation.scenarios(scenario_id),
    
    -- Execution
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    status              VARCHAR(50) DEFAULT 'QUEUED',
    
    -- For stochastic runs
    run_number          INTEGER DEFAULT 1,
    random_seed_used    BIGINT,
    
    -- Resources
    compute_node        VARCHAR(100),
    gpu_allocated       INTEGER,
    
    -- Results summary
    summary_metrics     JSONB,
    
    -- Artifacts
    artifacts_location  VARCHAR(500),
    
    -- Error handling
    error_message       TEXT,
    error_details       JSONB
);

-- Index for scenario queries
CREATE INDEX idx_simulation_runs_scenario 
    ON isr_simulation.simulation_runs (scenario_id, run_number);
```

### 4.2 Agent Schema (for simulation)

```sql
CREATE TABLE isr_simulation.agent_definitions (
    agent_def_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    agent_type          VARCHAR(100) NOT NULL, -- INSURGENT_CELL, BORDER_PATROL, etc.
    name                VARCHAR(255),
    
    -- Behavior
    behavior_model      VARCHAR(100) NOT NULL,
    behavior_parameters JSONB,
    
    -- Capabilities
    capabilities        JSONB,
    /*
    {
        "movement": {"maxSpeed": 40, "terrain": ["ROAD", "LIGHT_VEGETATION"]},
        "detection": {"range": 500, "probability": 0.8},
        "weapons": ["AK47", "RPG"]
    }
    */
    
    -- Appearance
    visual_signature    JSONB,
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_simulation.agent_instances (
    instance_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES isr_simulation.simulation_runs(run_id),
    agent_def_id        UUID NOT NULL REFERENCES isr_simulation.agent_definitions(agent_def_id),
    
    -- Initial state
    initial_position    GEOGRAPHY(POINT, 4326),
    initial_state       JSONB,
    
    -- Group membership
    group_id            UUID,
    group_role          VARCHAR(50)
);

-- Agent state history (time-series)
CREATE TABLE isr_simulation.agent_states (
    state_id            UUID DEFAULT gen_random_uuid(),
    instance_id         UUID NOT NULL REFERENCES isr_simulation.agent_instances(instance_id),
    
    simulation_time     TIMESTAMPTZ NOT NULL,
    
    -- Position and motion
    position            GEOGRAPHY(POINT, 4326) NOT NULL,
    heading             DECIMAL(5,2),
    speed               DECIMAL(10,2),
    
    -- State
    status              VARCHAR(50),
    current_action      VARCHAR(100),
    state_variables     JSONB,
    
    PRIMARY KEY (instance_id, simulation_time)
);

-- Convert to hypertable
SELECT create_hypertable('isr_simulation.agent_states', 'simulation_time');
```

### 4.3 Disaster Model Schema

```sql
CREATE TABLE isr_simulation.disaster_scenarios (
    disaster_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disaster_type       VARCHAR(50) NOT NULL, -- EARTHQUAKE, FLOOD, DROUGHT, LANDSLIDE
    
    -- Event parameters
    parameters          JSONB NOT NULL,
    /*
    Earthquake example:
    {
        "epicenter": {"lat": 36.7, "lon": 71.3},
        "magnitude": 6.8,
        "depth_km": 15,
        "faultMechanism": "THRUST"
    }
    
    Flood example:
    {
        "riverSystem": "KABUL_RIVER",
        "rainfallMm": 150,
        "duration_hours": 48,
        "antecedentConditions": "SATURATED"
    }
    */
    
    -- Model configuration
    model_id            VARCHAR(100),
    model_version       VARCHAR(50),
    
    -- Results
    results             JSONB,
    impact_area         GEOGRAPHY(MULTIPOLYGON, 4326),
    
    -- Execution
    executed_at         TIMESTAMPTZ,
    execution_time_ms   INTEGER,
    
    created_by          VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_simulation.disaster_impacts (
    impact_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disaster_id         UUID NOT NULL REFERENCES isr_simulation.disaster_scenarios(disaster_id),
    
    -- Geographic unit
    admin_unit          VARCHAR(100), -- Province/District
    location            GEOGRAPHY(POLYGON, 4326),
    
    -- Population impact
    population_exposed  INTEGER,
    estimated_fatalities JSONB, -- {mean, p10, p50, p90}
    estimated_injuries  JSONB,
    displaced_population INTEGER,
    
    -- Infrastructure impact
    buildings_damaged   JSONB, -- {collapsed, severe, moderate, light}
    roads_affected_km   DECIMAL(10,2),
    bridges_affected    INTEGER,
    hospitals_affected  INTEGER,
    schools_affected    INTEGER,
    
    -- Economic impact
    economic_loss_usd   DECIMAL(15,2)
);
```

---

## 5. Information Warfare Schemas

### 5.1 Narrative Schema

```sql
CREATE SCHEMA isr_narrative;

CREATE TABLE isr_narrative.themes (
    theme_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    
    -- Parent theme for hierarchy
    parent_theme_id     UUID REFERENCES isr_narrative.themes(theme_id),
    
    -- Keywords for detection
    keywords            TEXT[],
    keyword_embeddings  VECTOR(768), -- For semantic matching (pgvector)
    
    -- Status
    status              VARCHAR(50) DEFAULT 'ACTIVE',
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_narrative.theme_observations (
    observation_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theme_id            UUID NOT NULL REFERENCES isr_narrative.themes(theme_id),
    
    -- Time bucket (hourly aggregation)
    time_bucket         TIMESTAMPTZ NOT NULL,
    
    -- Volume
    mention_count       INTEGER NOT NULL,
    unique_sources      INTEGER,
    
    -- Sentiment
    sentiment_score     DECIMAL(4,3), -- -1 to +1
    sentiment_variance  DECIMAL(4,3),
    
    -- Reach estimate
    estimated_reach     BIGINT,
    
    -- Geographic distribution
    geo_distribution    JSONB, -- {"AFGHANISTAN": 0.45, "PAKISTAN": 0.20, ...}
    
    -- Source type distribution
    source_distribution JSONB, -- {"SOCIAL_MEDIA": 0.5, "NEWS": 0.3, ...}
    
    PRIMARY KEY (theme_id, time_bucket)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('isr_narrative.theme_observations', 'time_bucket');
```

### 5.2 Disinformation Schema

```sql
CREATE TABLE isr_narrative.disinformation_content (
    content_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content
    source_url          TEXT,
    source_platform     VARCHAR(100),
    content_text        TEXT,
    content_hash        VARCHAR(64), -- SHA256 for deduplication
    language            VARCHAR(10),
    
    -- Temporal
    published_at        TIMESTAMPTZ,
    discovered_at       TIMESTAMPTZ DEFAULT NOW(),
    
    -- Analysis results
    disinformation_score DECIMAL(3,2), -- 0-1 likelihood
    confidence          DECIMAL(3,2),
    category            VARCHAR(50), -- LIKELY, POSSIBLE, UNLIKELY
    
    -- Claim analysis
    claims_analyzed     JSONB,
    /*
    [
        {
            "claim": "...",
            "verdict": "FALSE",
            "confidence": 0.95,
            "evidence": [...]
        }
    ]
    */
    
    -- Source credibility
    source_credibility  JSONB,
    
    -- Coordination signals
    coordination_detected BOOLEAN DEFAULT FALSE,
    coordination_signals JSONB,
    
    -- Campaign linkage
    campaign_id         UUID,
    
    -- Review
    reviewed            BOOLEAN DEFAULT FALSE,
    reviewed_by         VARCHAR(100),
    reviewed_at         TIMESTAMPTZ,
    confirmed_disinfo   BOOLEAN
);

-- Index for deduplication
CREATE UNIQUE INDEX idx_disinfo_content_hash 
    ON isr_narrative.disinformation_content (content_hash);

-- Full-text search
CREATE INDEX idx_disinfo_content_text 
    ON isr_narrative.disinformation_content 
    USING GIN (to_tsvector('simple', content_text));

CREATE TABLE isr_narrative.disinformation_campaigns (
    campaign_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    
    -- Detection
    first_detected      TIMESTAMPTZ NOT NULL,
    last_activity       TIMESTAMPTZ,
    status              VARCHAR(50) DEFAULT 'ACTIVE',
    
    -- Scope
    narratives          TEXT[],
    platforms           VARCHAR(100)[],
    
    -- Metrics
    total_posts         INTEGER DEFAULT 0,
    unique_accounts     INTEGER DEFAULT 0,
    estimated_reach     BIGINT,
    
    -- Attribution (careful with privacy)
    attributed_network  VARCHAR(255),
    attribution_confidence DECIMAL(3,2),
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. Alert Schema

```sql
CREATE SCHEMA isr_alerting;

CREATE TYPE isr_alerting.alert_severity AS ENUM (
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
);

CREATE TYPE isr_alerting.alert_status AS ENUM (
    'OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'FALSE_POSITIVE'
);

CREATE TABLE isr_alerting.alerts (
    alert_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Classification
    category            VARCHAR(100) NOT NULL, -- SECURITY, HUMANITARIAN, CYBER, DISINFORMATION
    subcategory         VARCHAR(100),
    severity            isr_alerting.alert_severity NOT NULL,
    
    -- Content
    title               VARCHAR(255) NOT NULL,
    summary             TEXT NOT NULL,
    details             JSONB,
    
    -- Spatial
    location            GEOGRAPHY(GEOMETRY, 4326),
    region              VARCHAR(100),
    
    -- Scoring
    threat_score        INTEGER,
    confidence          DECIMAL(3,2),
    
    -- Source chain
    trigger_type        VARCHAR(100), -- RULE, ANOMALY, ML_MODEL, MANUAL
    trigger_id          VARCHAR(255),
    sources             JSONB,
    
    -- Status management
    status              isr_alerting.alert_status DEFAULT 'OPEN',
    
    -- Assignment
    assigned_to_user    VARCHAR(100),
    assigned_to_team    VARCHAR(100),
    assigned_at         TIMESTAMPTZ,
    
    -- SLA
    response_deadline   TIMESTAMPTZ,
    resolution_deadline TIMESTAMPTZ,
    
    -- Resolution
    resolved_at         TIMESTAMPTZ,
    resolved_by         VARCHAR(100),
    resolution_notes    TEXT,
    resolution_type     VARCHAR(100),
    
    -- Related items
    related_entities    UUID[],
    related_events      UUID[],
    related_alerts      UUID[],
    
    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at     TIMESTAMPTZ
);

-- Index for dashboard queries
CREATE INDEX idx_alerts_status_severity 
    ON isr_alerting.alerts (status, severity, created_at DESC);

-- Spatial index
CREATE INDEX idx_alerts_location 
    ON isr_alerting.alerts USING GIST (location);

-- Alert history for audit trail
CREATE TABLE isr_alerting.alert_history (
    history_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id            UUID NOT NULL REFERENCES isr_alerting.alerts(alert_id),
    
    action              VARCHAR(100) NOT NULL,
    previous_status     isr_alerting.alert_status,
    new_status          isr_alerting.alert_status,
    
    changed_by          VARCHAR(100) NOT NULL,
    changed_at          TIMESTAMPTZ DEFAULT NOW(),
    notes               TEXT,
    
    metadata            JSONB
);

CREATE INDEX idx_alert_history_alert 
    ON isr_alerting.alert_history (alert_id, changed_at DESC);
```

---

## 7. Data Ingestion Schemas

### 7.1 Satellite Imagery Metadata

```sql
CREATE SCHEMA isr_ingestion;

CREATE TABLE isr_ingestion.satellite_imagery (
    image_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source
    sensor_name         VARCHAR(100) NOT NULL,
    provider            VARCHAR(100),
    
    -- Capture info
    capture_time        TIMESTAMPTZ NOT NULL,
    
    -- Spatial
    bounding_box        GEOGRAPHY(POLYGON, 4326) NOT NULL,
    center_point        GEOGRAPHY(POINT, 4326),
    
    -- Technical specs
    resolution_m        DECIMAL(10,4),
    band_type           VARCHAR(50), -- PANCHROMATIC, MULTISPECTRAL, SAR
    bands               VARCHAR(50)[],
    cloud_cover_pct     DECIMAL(5,2),
    sun_elevation       DECIMAL(5,2),
    off_nadir_angle     DECIMAL(5,2),
    
    -- File info
    file_format         VARCHAR(20),
    file_size_bytes     BIGINT,
    storage_location    VARCHAR(500),
    
    -- Processing status
    processing_status   VARCHAR(50) DEFAULT 'PENDING',
    processed_at        TIMESTAMPTZ,
    
    -- Analysis results reference
    analysis_results    JSONB,
    detected_objects    INTEGER,
    
    -- Metadata
    original_metadata   JSONB,
    
    ingested_at         TIMESTAMPTZ DEFAULT NOW(),
    classification      VARCHAR(50) DEFAULT 'UNCLASSIFIED'
);

-- Spatial index for coverage queries
CREATE INDEX idx_satellite_bbox 
    ON isr_ingestion.satellite_imagery USING GIST (bounding_box);

-- Time index
CREATE INDEX idx_satellite_capture_time 
    ON isr_ingestion.satellite_imagery (capture_time DESC);
```

### 7.2 OSINT Feed Schema

```sql
CREATE TABLE isr_ingestion.osint_feeds (
    feed_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    feed_name           VARCHAR(255) NOT NULL,
    feed_type           VARCHAR(50) NOT NULL, -- RSS, API, SCRAPER
    source_url          TEXT NOT NULL,
    
    -- Configuration
    language            VARCHAR(10),
    update_frequency    INTERVAL,
    credibility_rating  DECIMAL(3,2),
    categories          VARCHAR(100)[],
    
    -- Processing config
    processing_config   JSONB,
    
    -- Status
    status              VARCHAR(50) DEFAULT 'ACTIVE',
    last_polled         TIMESTAMPTZ,
    next_poll           TIMESTAMPTZ,
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Stats
    total_items_processed BIGINT DEFAULT 0,
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_ingestion.osint_items (
    item_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id             UUID REFERENCES isr_ingestion.osint_feeds(feed_id),
    
    -- Content
    source_id           VARCHAR(255), -- Original ID from source
    source_url          TEXT,
    title               TEXT,
    content             TEXT,
    content_hash        VARCHAR(64),
    
    -- Temporal
    published_at        TIMESTAMPTZ,
    ingested_at         TIMESTAMPTZ DEFAULT NOW(),
    
    -- Language
    detected_language   VARCHAR(10),
    translated_content  TEXT,
    translation_language VARCHAR(10),
    
    -- NLP Results
    entities_extracted  JSONB,
    topics              TEXT[],
    sentiment_score     DECIMAL(4,3),
    
    -- Geolocation (if extracted)
    extracted_locations JSONB,
    primary_location    GEOGRAPHY(POINT, 4326),
    
    -- Classification
    relevance_score     DECIMAL(3,2),
    categories          VARCHAR(100)[],
    
    -- Processing
    processing_status   VARCHAR(50) DEFAULT 'PENDING',
    processed_at        TIMESTAMPTZ
);

-- Deduplication index
CREATE UNIQUE INDEX idx_osint_items_hash 
    ON isr_ingestion.osint_items (content_hash);

-- Full-text search
CREATE INDEX idx_osint_items_content 
    ON isr_ingestion.osint_items 
    USING GIN (to_tsvector('simple', title || ' ' || COALESCE(content, '')));
```

---

## 8. User & Access Control Schemas

### 8.1 User Schema

```sql
CREATE SCHEMA isr_iam;

CREATE TABLE isr_iam.users (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identity (synced from Keycloak)
    external_id         VARCHAR(255) UNIQUE NOT NULL,
    username            VARCHAR(100) UNIQUE NOT NULL,
    email               VARCHAR(255),
    display_name        VARCHAR(255),
    
    -- Organization
    organization        VARCHAR(255),
    department          VARCHAR(255),
    
    -- Clearance
    clearance_level     VARCHAR(50),
    nationality         VARCHAR(50),
    
    -- Status
    status              VARCHAR(50) DEFAULT 'ACTIVE',
    last_login          TIMESTAMPTZ,
    
    -- Preferences
    preferences         JSONB DEFAULT '{}',
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_iam.roles (
    role_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name           VARCHAR(100) UNIQUE NOT NULL,
    description         TEXT,
    permissions         VARCHAR(255)[], -- List of permission codes
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_iam.user_roles (
    user_id             UUID REFERENCES isr_iam.users(user_id),
    role_id             UUID REFERENCES isr_iam.roles(role_id),
    granted_at          TIMESTAMPTZ DEFAULT NOW(),
    granted_by          UUID REFERENCES isr_iam.users(user_id),
    expires_at          TIMESTAMPTZ,
    
    PRIMARY KEY (user_id, role_id)
);
```

### 8.2 Audit Log Schema

```sql
CREATE TABLE isr_iam.audit_logs (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Who
    user_id             UUID REFERENCES isr_iam.users(user_id),
    username            VARCHAR(100),
    user_ip             INET,
    user_agent          TEXT,
    
    -- What
    action              VARCHAR(100) NOT NULL,
    resource_type       VARCHAR(100),
    resource_id         VARCHAR(255),
    
    -- Details
    request_method      VARCHAR(10),
    request_path        TEXT,
    request_params      JSONB,
    
    -- Result
    result              VARCHAR(50), -- SUCCESS, FAILURE, DENIED
    result_details      JSONB,
    
    -- When
    timestamp           TIMESTAMPTZ DEFAULT NOW(),
    
    -- Classification
    classification      VARCHAR(50)
);

-- Time-based partitioning
SELECT create_hypertable('isr_iam.audit_logs', 'timestamp');

-- Index for user queries
CREATE INDEX idx_audit_logs_user 
    ON isr_iam.audit_logs (user_id, timestamp DESC);

-- Index for resource queries
CREATE INDEX idx_audit_logs_resource 
    ON isr_iam.audit_logs (resource_type, resource_id, timestamp DESC);

-- Retention policy (keep for 7 years per requirements)
SELECT add_retention_policy('isr_iam.audit_logs', INTERVAL '7 years');
```

---

## 9. Apache Kafka Topic Schemas (Avro)

### 9.1 Event Schema

```json
{
  "type": "record",
  "name": "ISREvent",
  "namespace": "mil.isr.events",
  "fields": [
    {"name": "eventId", "type": "string"},
    {"name": "eventType", "type": {"type": "enum", "name": "EventType", "symbols": ["EXPLOSION", "GUNFIRE", "IED_DETONATION", "BORDER_CROSSING", "ATTACK", "OTHER"]}},
    {"name": "severity", "type": {"type": "enum", "name": "Severity", "symbols": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}},
    {"name": "occurredAt", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "location", "type": ["null", {
      "type": "record",
      "name": "GeoPoint",
      "fields": [
        {"name": "latitude", "type": "double"},
        {"name": "longitude", "type": "double"},
        {"name": "altitude", "type": ["null", "double"], "default": null}
      ]
    }], "default": null},
    {"name": "region", "type": ["null", "string"], "default": null},
    {"name": "title", "type": "string"},
    {"name": "summary", "type": ["null", "string"], "default": null},
    {"name": "details", "type": ["null", "string"], "default": null},
    {"name": "sourceType", "type": "string"},
    {"name": "sourceId", "type": ["null", "string"], "default": null},
    {"name": "confidence", "type": "double"},
    {"name": "classification", "type": "string", "default": "UNCLASSIFIED"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}, "default": {}}
  ]
}
```

### 9.2 Track Update Schema

```json
{
  "type": "record",
  "name": "TrackUpdate",
  "namespace": "mil.isr.tracks",
  "fields": [
    {"name": "trackId", "type": "string"},
    {"name": "entityId", "type": "string"},
    {"name": "entityType", "type": "string"},
    {"name": "observationTime", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "position", "type": {
      "type": "record",
      "name": "Position",
      "fields": [
        {"name": "latitude", "type": "double"},
        {"name": "longitude", "type": "double"},
        {"name": "altitude", "type": ["null", "double"], "default": null},
        {"name": "accuracy", "type": ["null", "double"], "default": null}
      ]
    }},
    {"name": "velocity", "type": ["null", {
      "type": "record",
      "name": "Velocity",
      "fields": [
        {"name": "speed", "type": "double"},
        {"name": "heading", "type": "double"},
        {"name": "unit", "type": "string", "default": "MPS"}
      ]
    }], "default": null},
    {"name": "confidence", "type": "double"},
    {"name": "sourceType", "type": "string"},
    {"name": "sourceId", "type": "string"},
    {"name": "isFused", "type": "boolean", "default": false},
    {"name": "attributes", "type": {"type": "map", "values": "string"}, "default": {}}
  ]
}
```

### 9.3 Alert Schema

```json
{
  "type": "record",
  "name": "Alert",
  "namespace": "mil.isr.alerts",
  "fields": [
    {"name": "alertId", "type": "string"},
    {"name": "category", "type": "string"},
    {"name": "subcategory", "type": ["null", "string"], "default": null},
    {"name": "severity", "type": {"type": "enum", "name": "AlertSeverity", "symbols": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}},
    {"name": "title", "type": "string"},
    {"name": "summary", "type": "string"},
    {"name": "location", "type": ["null", "mil.isr.tracks.Position"], "default": null},
    {"name": "region", "type": ["null", "string"], "default": null},
    {"name": "threatScore", "type": ["null", "int"], "default": null},
    {"name": "confidence", "type": "double"},
    {"name": "triggerType", "type": "string"},
    {"name": "triggerId", "type": ["null", "string"], "default": null},
    {"name": "relatedEntityIds", "type": {"type": "array", "items": "string"}, "default": []},
    {"name": "relatedEventIds", "type": {"type": "array", "items": "string"}, "default": []},
    {"name": "createdAt", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "classification", "type": "string", "default": "UNCLASSIFIED"}
  ]
}
```

---

## 10. Data Catalog & Lineage

### Dataset Registry Schema

```sql
CREATE SCHEMA isr_catalog;

CREATE TABLE isr_catalog.datasets (
    dataset_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    name                VARCHAR(255) NOT NULL UNIQUE,
    description         TEXT,
    
    -- Classification
    domain              VARCHAR(100), -- SATELLITE, OSINT, CYBER, HUMANITARIAN, etc.
    data_type           VARCHAR(100), -- STREAMING, BATCH, REFERENCE
    
    -- Schema
    schema_definition   JSONB,
    schema_version      VARCHAR(50),
    
    -- Source
    source_system       VARCHAR(255),
    ingestion_method    VARCHAR(100),
    update_frequency    INTERVAL,
    
    -- Quality
    quality_score       DECIMAL(3,2),
    completeness        DECIMAL(3,2),
    
    -- Access
    classification      VARCHAR(50),
    owner_team          VARCHAR(100),
    steward_contact     VARCHAR(255),
    
    -- Lifecycle
    retention_days      INTEGER,
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE isr_catalog.data_lineage (
    lineage_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    source_dataset_id   UUID REFERENCES isr_catalog.datasets(dataset_id),
    target_dataset_id   UUID REFERENCES isr_catalog.datasets(dataset_id),
    
    transformation_type VARCHAR(100),
    transformation_desc TEXT,
    
    pipeline_id         VARCHAR(255),
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 11. Privacy & Anonymization Markers

All schemas include privacy considerations:

```sql
-- Example: Adding privacy markers to entity table
ALTER TABLE isr_core.entities ADD COLUMN privacy_flags JSONB DEFAULT '{
    "containsPII": false,
    "anonymizationApplied": true,
    "anonymizationMethod": "PSEUDONYMIZATION",
    "dataMinimization": true,
    "retentionClass": "OPERATIONAL",
    "consentBasis": "LEGITIMATE_INTEREST"
}';

-- Privacy audit view
CREATE VIEW isr_core.privacy_audit AS
SELECT 
    entity_id,
    entity_type,
    privacy_flags->>'containsPII' as contains_pii,
    privacy_flags->>'anonymizationApplied' as anonymized,
    privacy_flags->>'anonymizationMethod' as anon_method,
    created_at,
    updated_at
FROM isr_core.entities
WHERE privacy_flags->>'containsPII' = 'true';
```

---

*Document Version: 1.0*  
*Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY*  
*Last Updated: 2026-01-17*
