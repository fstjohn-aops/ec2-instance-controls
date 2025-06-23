#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 EC2 Slack Bot - Improved Test Suite${NC}"
echo "=============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if docker-compose or docker compose is available
check_docker_compose() {
    if command_exists docker-compose; then
        echo "docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    else
        echo "none"
    fi
}

# Function to run Python test suite
run_python_tests() {
    echo -e "\n${YELLOW}Running Python Test Suite${NC}"
    echo "----------------------------------------"
    
    # Activate virtual environment for the test
    source venv/bin/activate
    if python3 test_suite.py; then
        echo -e "${GREEN}✅ Python test suite completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Python test suite failed${NC}"
        return 1
    fi
}

# Check environment
echo -e "\n${BLUE}Environment Check${NC}"
echo "=================="

# Check Python
if command_exists python3; then
    python_version=$(python3 --version 2>&1)
    echo -e "${GREEN}✅ Python found: $python_version${NC}"
else
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# Check pip
if command_exists pip3; then
    echo -e "${GREEN}✅ pip3 found${NC}"
else
    echo -e "${RED}❌ pip3 not found${NC}"
    exit 1
fi

# Check Docker
DOCKER_COMPOSE_CMD=$(check_docker_compose)
if [ "$DOCKER_COMPOSE_CMD" != "none" ]; then
    echo -e "${GREEN}✅ Docker Compose available: $DOCKER_COMPOSE_CMD${NC}"
    DOCKER_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  Docker Compose not available${NC}"
    DOCKER_AVAILABLE=false
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    VENV_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    VENV_EXISTS=false
fi

# Track overall success
overall_success=true

# Phase 1: Setup and Dependencies
echo -e "\n${BLUE}Phase 1: Setup and Dependencies${NC}"
echo "=================================="

# Create virtual environment if needed
if [ "$VENV_EXISTS" = false ]; then
    echo "Creating virtual environment..."
    if python3 -m venv venv; then
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        overall_success=false
    fi
fi

# Activate virtual environment and install dependencies
if [ -d "venv" ]; then
    echo "Installing dependencies..."
    source venv/bin/activate
    if pip install -r requirements.txt >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        overall_success=false
    fi
fi

# Phase 2: Python Test Suite
echo -e "\n${BLUE}Phase 2: Python Test Suite${NC}"
echo "=============================="
if run_python_tests; then
    echo -e "${GREEN}✅ Phase 2 passed${NC}"
else
    echo -e "${RED}❌ Phase 2 failed${NC}"
    overall_success=false
fi

# Phase 3: Container Tests (if Docker available)
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "\n${BLUE}Phase 3: Container Tests${NC}"
    echo "=========================="
    
    echo -e "\n${YELLOW}Starting container in test mode...${NC}"
    $DOCKER_COMPOSE_CMD down >/dev/null 2>&1
    TEST_MODE=true $DOCKER_COMPOSE_CMD up -d
    
    echo "Waiting for container to start..."
    sleep 10
    
    # Test if container is running
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Container is running${NC}"
        
        # Test health endpoint
        if curl -f http://localhost:5000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Health endpoint is working${NC}"
        else
            echo -e "${RED}❌ Health endpoint failed${NC}"
            overall_success=false
        fi
        
        # Test API endpoints
        echo "Testing API endpoints..."
        response=$(curl -s http://localhost:5000/api/assignments)
        if [ $? -eq 0 ] && echo "$response" | python3 -m json.tool >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API endpoints working${NC}"
        else
            echo -e "${RED}❌ API endpoints failed${NC}"
            overall_success=false
        fi
        
        # Test assign-instance endpoint specifically
        echo "Testing assign-instance endpoint..."
        assignment_response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
            -H "Content-Type: application/json" \
            -d '{"instance_id": "i-test-instance-1", "slack_user_id": "U123", "slack_username": "testuser"}')
        if [ $? -eq 0 ] && echo "$assignment_response" | python3 -m json.tool >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Assign-instance endpoint working${NC}"
        else
            echo -e "${RED}❌ Assign-instance endpoint failed${NC}"
            overall_success=false
        fi
    else
        echo -e "${RED}❌ Container failed to start${NC}"
        overall_success=false
    fi
    
    # Cleanup
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    $DOCKER_COMPOSE_CMD down
else
    echo -e "\n${YELLOW}Phase 3: Skipping container tests (Docker not available)${NC}"
fi

# Final results
echo -e "\n${BLUE}Test Results Summary${NC}"
echo "====================="

if $overall_success; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo -e "${YELLOW}Your EC2 Slack Bot is ready for:${NC}"
    echo "1. ✅ Environment setup working"
    echo "2. ✅ Dependencies installed"
    echo "3. ✅ Python test suite working"
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo "4. ✅ Container tests working"
        echo "5. ✅ API endpoints working"
    fi
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Configure real Slack credentials in .env"
    echo "2. Configure real AWS credentials"
    echo "3. Deploy to production"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${YELLOW}Please check the output above for details${NC}"
    exit 1
fi 