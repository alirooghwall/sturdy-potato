#!/bin/bash

# ISR Platform - Complete Startup Script
# This script automates the entire platform startup process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ISR Platform - Automated Startup${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${YELLOW}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=0
    
    print_step "Waiting for $service to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            print_success "$service is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    print_error "$service failed to start"
    return 1
}

# Main script
print_header

# 1. Check prerequisites
print_step "Checking prerequisites..."

MISSING_DEPS=0

if ! check_command docker; then
    MISSING_DEPS=1
fi

if ! check_command docker-compose; then
    MISSING_DEPS=1
fi

if ! check_command python3; then
    MISSING_DEPS=1
fi

if ! check_command nc; then
    echo -e "${YELLOW}Note: netcat (nc) not found. Service health checks may be limited.${NC}"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    print_error "Missing required dependencies. Please install them first."
    exit 1
fi

# 2. Check if .env exists
print_step "Checking configuration..."

if [ ! -f .env ]; then
    print_error ".env file not found"
    echo "Creating .env from template..."
    cp .env.example .env
    print_success ".env file created"
    echo -e "${YELLOW}⚠ Please edit .env and configure API keys before continuing${NC}"
    echo "Press Enter when ready to continue..."
    read
fi

# 3. Check Docker daemon
print_step "Checking Docker daemon..."

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi
print_success "Docker daemon is running"

# 4. Start infrastructure services
print_step "Starting infrastructure services..."

docker-compose up -d postgres redis kafka zookeeper

print_success "Infrastructure services started"

# 5. Wait for services to be ready
wait_for_service localhost 5432 "PostgreSQL"
wait_for_service localhost 6379 "Redis"
wait_for_service localhost 9092 "Kafka"

# 6. Install Python dependencies
print_step "Checking Python dependencies..."

if [ ! -d "venv" ]; then
    print_step "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true

print_step "Installing Python packages..."
pip install -q -r requirements.txt
print_success "Python dependencies installed"

# 7. Run database migrations
print_step "Running database migrations..."

if python -m alembic current &> /dev/null; then
    python -m alembic upgrade head
    print_success "Database migrations completed"
else
    print_error "Alembic not configured properly"
    echo "Skipping migrations..."
fi

# 8. Create admin user (if script exists)
if [ -f "scripts/create_admin_user.py" ]; then
    print_step "Creating admin user..."
    python scripts/create_admin_user.py 2>/dev/null || echo "Admin user may already exist"
    print_success "Admin user ready"
fi

# 9. Seed test data (optional)
if [ -f "scripts/seed_test_data.py" ]; then
    echo -e "\n${YELLOW}Would you like to seed test data? (y/N)${NC}"
    read -t 5 -n 1 seed_choice || seed_choice="n"
    echo
    if [[ $seed_choice =~ ^[Yy]$ ]]; then
        print_step "Seeding test data..."
        python scripts/seed_test_data.py
        print_success "Test data seeded"
    fi
fi

# 10. Start API server
print_step "Starting API server..."

# Kill existing processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start API in background
nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > .api.pid

sleep 3

if ps -p $API_PID > /dev/null; then
    print_success "API server started (PID: $API_PID)"
else
    print_error "API server failed to start"
    exit 1
fi

# 11. Wait for API to be ready
print_step "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API is ready"
        break
    fi
    sleep 1
done

# 12. Start ingestion (if auto-start enabled)
INGESTION_AUTO_START=$(grep INGESTION_AUTO_START .env | cut -d= -f2 || echo "false")

if [ "$INGESTION_AUTO_START" = "true" ]; then
    print_step "Starting data ingestion..."
    
    if [ -f "scripts/start_ingestion.py" ]; then
        nohup python scripts/start_ingestion.py > logs/ingestion.log 2>&1 &
        INGESTION_PID=$!
        echo $INGESTION_PID > .ingestion.pid
        print_success "Ingestion started (PID: $INGESTION_PID)"
    fi
fi

# 13. Start stream processor (optional)
echo -e "\n${YELLOW}Would you like to start the stream processor? (Y/n)${NC}"
read -t 5 -n 1 processor_choice || processor_choice="y"
echo

if [[ ! $processor_choice =~ ^[Nn]$ ]]; then
    if [ -f "scripts/start_stream_processor.py" ]; then
        print_step "Starting stream processor..."
        nohup python scripts/start_stream_processor.py > logs/stream_processor.log 2>&1 &
        PROCESSOR_PID=$!
        echo $PROCESSOR_PID > .processor.pid
        print_success "Stream processor started (PID: $PROCESSOR_PID)"
    fi
fi

# 14. Final health check
print_step "Running final health checks..."

# Check API
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_success "API health check passed"
else
    print_error "API health check failed"
fi

# Check readiness
READY_STATUS=$(curl -s http://localhost:8000/ready | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$READY_STATUS" = "ready" ] || [ "$READY_STATUS" = "degraded" ]; then
    print_success "Services readiness: $READY_STATUS"
else
    print_error "Services not ready"
fi

# 15. Display access information
echo
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ISR Platform Started Successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  API:         http://localhost:8000"
echo -e "  Swagger UI:  http://localhost:8000/docs"
echo -e "  ReDoc:       http://localhost:8000/redoc"
echo -e "  Health:      http://localhost:8000/health"
echo
echo -e "${BLUE}Default Credentials:${NC}"
echo -e "  Username:    admin"
echo -e "  Password:    changeme"
echo
echo -e "${BLUE}Process IDs:${NC}"
echo -e "  API:         $API_PID"
[ -n "$INGESTION_PID" ] && echo -e "  Ingestion:   $INGESTION_PID"
[ -n "$PROCESSOR_PID" ] && echo -e "  Processor:   $PROCESSOR_PID"
echo
echo -e "${BLUE}Log Files:${NC}"
echo -e "  API:         logs/api.log"
[ -n "$INGESTION_PID" ] && echo -e "  Ingestion:   logs/ingestion.log"
[ -n "$PROCESSOR_PID" ] && echo -e "  Processor:   logs/stream_processor.log"
echo
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Configure API keys: http://localhost:8000/docs#/Administration"
echo -e "  2. Create additional users"
echo -e "  3. Start submitting intelligence reports"
echo
echo -e "${YELLOW}To stop all services:${NC}"
echo -e "  ./scripts/stop_platform.sh"
echo
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
