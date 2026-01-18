-- ISR Platform Database Initialization Script
-- Creates extensions and initial schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schemas
CREATE SCHEMA IF NOT EXISTS isr;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set search path
SET search_path TO isr, public;

-- Grant permissions
GRANT ALL ON SCHEMA isr TO isr_user;
GRANT ALL ON SCHEMA audit TO isr_user;

-- Create enum types
DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM (
        'VEHICLE', 'PERSONNEL', 'FACILITY', 'COMMUNICATION', 
        'INFRASTRUCTURE', 'INSURGENT_CELL', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE threat_level AS ENUM (
        'UNKNOWN', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE event_severity AS ENUM (
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM (
        'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED', 'EXPIRED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'VIEWER', 'ANALYST', 'SENIOR_ANALYST', 'OPERATOR', 'ADMIN', 'SUPER_ADMIN'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS isr.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role DEFAULT 'VIEWER',
    clearance_level VARCHAR(50) DEFAULT 'UNCLASSIFIED',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON isr.users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON isr.users(role);

-- Create entities table with PostGIS geometry
CREATE TABLE IF NOT EXISTS isr.entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    classification VARCHAR(50) DEFAULT 'UNCLASSIFIED',
    threat_level threat_level DEFAULT 'UNKNOWN',
    status VARCHAR(20) DEFAULT 'ACTIVE',
    confidence_score FLOAT DEFAULT 0.0,
    location GEOMETRY(Point, 4326),
    altitude FLOAT,
    province VARCHAR(100),
    first_observed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_observed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON isr.entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_threat ON isr.entities(threat_level);
CREATE INDEX IF NOT EXISTS idx_entities_location ON isr.entities USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_entities_province ON isr.entities(province);

-- Create events table
CREATE TABLE IF NOT EXISTS isr.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity event_severity NOT NULL,
    classification VARCHAR(50) DEFAULT 'UNCLASSIFIED',
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED',
    location GEOMETRY(Point, 4326),
    location_name VARCHAR(255),
    region VARCHAR(100),
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_type VARCHAR(50),
    source_id VARCHAR(255),
    source_reliability VARCHAR(20) DEFAULT 'UNKNOWN',
    casualties_count INTEGER,
    affected_population INTEGER,
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_type ON isr.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON isr.events(severity);
CREATE INDEX IF NOT EXISTS idx_events_location ON isr.events USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_events_region ON isr.events(region);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON isr.events(occurred_at);

-- Create alerts table
CREATE TABLE IF NOT EXISTS isr.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity event_severity NOT NULL,
    priority INTEGER DEFAULT 3,
    status alert_status DEFAULT 'ACTIVE',
    source_system VARCHAR(100),
    location GEOMETRY(Point, 4326),
    region VARCHAR(100),
    assigned_user_id UUID REFERENCES isr.users(id),
    event_id UUID REFERENCES isr.events(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_type ON isr.alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON isr.alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON isr.alerts(severity, priority);
CREATE INDEX IF NOT EXISTS idx_alerts_assigned ON isr.alerts(assigned_user_id);

-- Create threat_scores table
CREATE TABLE IF NOT EXISTS isr.threat_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID REFERENCES isr.entities(id),
    event_id UUID REFERENCES isr.events(id),
    overall_score FLOAT NOT NULL,
    category VARCHAR(20) NOT NULL,
    credibility_score FLOAT DEFAULT 0.0,
    tactical_impact_score FLOAT DEFAULT 0.0,
    capability_score FLOAT DEFAULT 0.0,
    vulnerability_score FLOAT DEFAULT 0.0,
    time_sensitivity_score FLOAT DEFAULT 0.0,
    context_window_start TIMESTAMP WITH TIME ZONE,
    context_window_end TIMESTAMP WITH TIME ZONE,
    model_id VARCHAR(100) DEFAULT 'threat-scorer-v1',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recommendations JSONB DEFAULT '[]',
    explanation JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_threat_scores_entity ON isr.threat_scores(entity_id);
CREATE INDEX IF NOT EXISTS idx_threat_scores_event ON isr.threat_scores(event_id);
CREATE INDEX IF NOT EXISTS idx_threat_scores_time ON isr.threat_scores(calculated_at);

-- Create anomalies table
CREATE TABLE IF NOT EXISTS isr.anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(50) NOT NULL,
    anomaly_subtype VARCHAR(100) NOT NULL,
    severity event_severity NOT NULL,
    severity_score FLOAT NOT NULL,
    anomaly_score FLOAT,
    z_score FLOAT,
    threshold FLOAT,
    entity_id UUID REFERENCES isr.entities(id),
    region VARCHAR(100),
    location GEOMETRY(Point, 4326),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    baseline_stats JSONB DEFAULT '{}',
    contributing_factors JSONB DEFAULT '[]',
    model_id VARCHAR(100) DEFAULT 'anomaly-detector-v1',
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_anomalies_domain ON isr.anomalies(domain);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON isr.anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected ON isr.anomalies(detected_at);

-- Create narrative_analyses table
CREATE TABLE IF NOT EXISTS isr.narrative_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL,
    narrative_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    sentiment_category VARCHAR(30) NOT NULL,
    sentiment_score FLOAT NOT NULL,
    coordination_score FLOAT DEFAULT 0.0,
    virality_score FLOAT DEFAULT 0.0,
    threat_relevance FLOAT DEFAULT 0.0,
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_credibility VARCHAR(30) DEFAULT 'UNKNOWN',
    language VARCHAR(20) NOT NULL,
    entities JSONB DEFAULT '[]',
    topics JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    propaganda_indicators JSONB DEFAULT '[]',
    fact_check_flags JSONB DEFAULT '[]',
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_id VARCHAR(100) DEFAULT 'narrative-analyzer-v1'
);

CREATE INDEX IF NOT EXISTS idx_narrative_type ON isr.narrative_analyses(narrative_type);
CREATE INDEX IF NOT EXISTS idx_narrative_source ON isr.narrative_analyses(source_type);
CREATE INDEX IF NOT EXISTS idx_narrative_threat ON isr.narrative_analyses(threat_relevance);

-- Create simulations table
CREATE TABLE IF NOT EXISTS isr.simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    simulation_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'CREATED',
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    current_time TIMESTAMP WITH TIME ZONE NOT NULL,
    time_step_minutes INTEGER DEFAULT 15,
    scenario_id UUID,
    scenario_name VARCHAR(255),
    parameters JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    agent_count INTEGER DEFAULT 0,
    event_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES isr.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_simulations_type ON isr.simulations(simulation_type);
CREATE INDEX IF NOT EXISTS idx_simulations_status ON isr.simulations(status);

-- Create audit_logs table in audit schema
CREATE TABLE IF NOT EXISTS audit.logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    request_id VARCHAR(255),
    ip_address INET,
    user_agent VARCHAR(500),
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit.logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit.logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.logs(timestamp);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DO $$ 
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'isr' AND table_name IN ('users', 'entities', 'events', 'alerts', 'simulations')
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON isr.%I', t, t);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON isr.%I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END $$;

-- Insert default admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO isr.users (username, email, hashed_password, full_name, role, clearance_level, is_active)
VALUES (
    'admin',
    'admin@isr-platform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.lIh9iL5BK5Kj1O',  -- admin123
    'System Administrator',
    'SUPER_ADMIN',
    'TOP SECRET',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Insert demo analyst user
INSERT INTO isr.users (username, email, hashed_password, full_name, role, clearance_level, is_active)
VALUES (
    'analyst',
    'analyst@isr-platform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.lIh9iL5BK5Kj1O',  -- admin123
    'Senior Analyst',
    'SENIOR_ANALYST',
    'SECRET',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'ISR Platform database initialized successfully';
END $$;
