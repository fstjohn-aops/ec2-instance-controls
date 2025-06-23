#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 EC2 Slack Bot - Complete Test Suite${NC}"
echo "=========================================="

# Function to run a test and check result
run_test() {
    local test_name="$1"
    local test_script="$2"
    
    echo -e "\n${YELLOW}Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if ./$test_script; then
        echo -e "${GREEN}✅ $test_name completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        return 1
    fi
}

# Track overall success
overall_success=true

# Test 1: Basic local functionality (without Slack/AWS)
echo -e "\n${BLUE}Phase 1: Basic Local Tests${NC}"
if run_test "Local API Tests" "test_local.sh"; then
    echo -e "${GREEN}✅ Phase 1 passed${NC}"
else
    echo -e "${RED}❌ Phase 1 failed${NC}"
    overall_success=false
fi

# Test 2: Simulation tests (with test mode)
echo -e "\n${BLUE}Phase 2: Simulation Tests${NC}"
echo "Starting container in test mode..."

# Stop any existing containers
docker-compose down > /dev/null 2>&1

# Start with test mode
TEST_MODE=true docker-compose up -d

# Wait for container to be ready
echo "Waiting for container to start..."
sleep 10

if run_test "Slack Simulation Tests" "test_simulation.sh"; then
    echo -e "${GREEN}✅ Phase 2 passed${NC}"
else
    echo -e "${RED}❌ Phase 2 failed${NC}"
    overall_success=false
fi

# Cleanup
echo -e "\n${YELLOW}Cleaning up...${NC}"
docker-compose down

# Final results
echo -e "\n${BLUE}Test Results Summary${NC}"
echo "====================="

if $overall_success; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo -e "${YELLOW}Your EC2 Slack Bot is ready for:${NC}"
    echo "1. ✅ API endpoints working"
    echo "2. ✅ Database operations working"
    echo "3. ✅ Permission system working"
    echo "4. ✅ Error handling working"
    echo "5. ✅ Slack simulation working"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Ask your admin to install the Slack app"
    echo "2. Get real Slack bot token and signing secret"
    echo "3. Update .env with real credentials"
    echo "4. Deploy to production"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${YELLOW}Please check the output above for details${NC}"
    exit 1
fi 