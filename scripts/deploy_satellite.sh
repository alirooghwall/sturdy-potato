#!/bin/bash
# Deployment script for satellite imagery analysis system

set -e

echo "=========================================="
echo "ISR Platform - Satellite Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}\n"

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker installed${NC}"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 not found.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 3 installed${NC}"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env file with your credentials before continuing.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ .env file exists${NC}\n"
}

# Create required directories
create_directories() {
    echo "Creating required directories..."
    
    mkdir -p data/satellite_cache
    mkdir -p visualizations
    mkdir -p models
    mkdir -p keys
    mkdir -p logs
    mkdir -p backups
    
    echo -e "${GREEN}✓ Directories created${NC}\n"
}

# Backup existing data
backup_data() {
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "Backing up existing data..."
        
        if [ -d "data" ]; then
            mkdir -p "$BACKUP_DIR"
            cp -r data "$BACKUP_DIR/"
            echo -e "${GREEN}✓ Data backed up to $BACKUP_DIR${NC}\n"
        else
            echo -e "${YELLOW}⚠ No existing data to backup${NC}\n"
        fi
    fi
}

# Install dependencies
install_dependencies() {
    echo "Installing Python dependencies..."
    
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    echo -e "${GREEN}✓ Dependencies installed${NC}\n"
}

# Download pre-trained models (if applicable)
download_models() {
    echo "Checking for ML models..."
    
    if [ ! -d "models" ] || [ -z "$(ls -A models)" ]; then
        echo -e "${YELLOW}⚠ ML models directory empty${NC}"
        echo "  To use ML features, download models to ./models/"
    else
        echo -e "${GREEN}✓ ML models found${NC}"
    fi
    echo ""
}

# Build Docker images
build_images() {
    echo "Building Docker images..."
    
    docker-compose -f docker-compose.yml -f docker-compose.satellite.yml build
    
    echo -e "${GREEN}✓ Docker images built${NC}\n"
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    
    # Start database only
    docker-compose up -d db
    
    # Wait for database to be ready
    echo "Waiting for database..."
    sleep 10
    
    # Run migrations
    docker-compose exec -T db psql -U user -d isr_db -c "SELECT 1;" || {
        echo -e "${RED}✗ Database not ready${NC}"
        exit 1
    }
    
    # Run Alembic migrations
    alembic upgrade head
    
    echo -e "${GREEN}✓ Migrations completed${NC}\n"
}

# Start services
start_services() {
    echo "Starting services..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.satellite.yml up -d
    else
        docker-compose -f docker-compose.yml -f docker-compose.satellite.yml up
    fi
    
    echo -e "${GREEN}✓ Services started${NC}\n"
}

# Health check
health_check() {
    echo "Running health checks..."
    
    # Wait for services to start
    sleep 15
    
    # Check API
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is healthy${NC}"
    else
        echo -e "${RED}✗ API health check failed${NC}"
    fi
    
    # Check database
    if docker-compose exec -T db pg_isready -U user > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is healthy${NC}"
    else
        echo -e "${RED}✗ Database health check failed${NC}"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is healthy${NC}"
    else
        echo -e "${RED}✗ Redis health check failed${NC}"
    fi
    
    echo ""
}

# Display service URLs
display_urls() {
    echo "=========================================="
    echo "Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Service URLs:"
    echo "  - API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - MinIO Console: http://localhost:9001"
    echo ""
    echo "Satellite Features:"
    echo "  - Sentinel-2 Integration: ${SATELLITE_SENTINEL2_ENABLED:-not configured}"
    echo "  - Google Earth Engine: ${SATELLITE_GEE_ENABLED:-not configured}"
    echo "  - MODIS Integration: ${SATELLITE_MODIS_ENABLED:-not configured}"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo "Stop services: docker-compose down"
    echo "=========================================="
}

# Main deployment flow
main() {
    check_prerequisites
    create_directories
    backup_data
    install_dependencies
    download_models
    build_images
    run_migrations
    start_services
    health_check
    display_urls
}

# Run main function
main
