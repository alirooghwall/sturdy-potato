#!/bin/bash

# ISR Platform - Stop Script

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}Stopping ISR Platform...${NC}\n"

# Stop Python processes
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if ps -p $API_PID > /dev/null; then
        kill $API_PID
        echo -e "${GREEN}✓${NC} Stopped API server (PID: $API_PID)"
    fi
    rm .api.pid
fi

if [ -f .ingestion.pid ]; then
    INGESTION_PID=$(cat .ingestion.pid)
    if ps -p $INGESTION_PID > /dev/null; then
        kill $INGESTION_PID
        echo -e "${GREEN}✓${NC} Stopped ingestion (PID: $INGESTION_PID)"
    fi
    rm .ingestion.pid
fi

if [ -f .processor.pid ]; then
    PROCESSOR_PID=$(cat .processor.pid)
    if ps -p $PROCESSOR_PID > /dev/null; then
        kill $PROCESSOR_PID
        echo -e "${GREEN}✓${NC} Stopped stream processor (PID: $PROCESSOR_PID)"
    fi
    rm .processor.pid
fi

# Stop Docker services
echo -e "\n${BLUE}Stopping Docker services...${NC}"
docker-compose down

echo -e "\n${GREEN}ISR Platform stopped.${NC}\n"
