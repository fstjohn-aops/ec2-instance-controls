#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 EC2 Slack Bot Simulation Tests${NC}"
echo "======================================"

# Check if container is running
echo -e "\n${YELLOW}1. Checking if container is running...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Container is not running. Please start it first with: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Container is running${NC}"

# Wait for app to be ready
echo -e "\n${YELLOW}2. Waiting for app to be ready...${NC}"
sleep 5

# Set up test data
echo -e "\n${YELLOW}3. Setting up test data...${NC}"

# Create test instance assignments
echo "Creating test instance assignments..."

# User 1 controls instance 1
curl -s -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"slack_user_id":"U123","slack_username":"alice","instance_id":"i-test-instance-1","instance_name":"Alice Test Server"}'

# User 2 controls instance 2
curl -s -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"slack_user_id":"U456","slack_username":"bob","instance_id":"i-test-instance-2","instance_name":"Bob Test Server"}'

# User 3 controls instance 3
curl -s -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"slack_user_id":"U789","slack_username":"charlie","instance_id":"i-test-instance-3","instance_name":"Charlie Test Server"}'

# User 4 has no instance assigned
# User 5 controls multiple instances (for permission testing)
curl -s -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"slack_user_id":"U999","slack_username":"admin","instance_id":"i-0ecdfc9a2e3e53302","instance_name":"Admin Server"}'

echo -e "${GREEN}✅ Test data created${NC}"

# Test scenarios
echo -e "\n${YELLOW}4. Running test scenarios...${NC}"

# Test 1: User with assigned instance tries to start their instance
echo -e "\n${BLUE}Test 1: Alice tries to start her assigned instance${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U123"}')
echo "Response: $response"

# Test 2: User with assigned instance tries to stop their instance
echo -e "\n${BLUE}Test 2: Bob tries to stop his assigned instance${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/stop \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U456"}')
echo "Response: $response"

# Test 3: User with assigned instance checks status
echo -e "\n${BLUE}Test 3: Charlie checks status of his assigned instance${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/status \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U789"}')
echo "Response: $response"

# Test 4: User without assigned instance tries to start
echo -e "\n${BLUE}Test 4: User without assignment tries to start instance${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U000"}')
echo "Response: $response"

# Test 5: User tries to start already running instance
echo -e "\n${BLUE}Test 5: Alice tries to start her already running instance${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U123"}')
echo "Response: $response"

# Test 6: Permission test - User tries to control instance they don't own
echo -e "\n${BLUE}Test 6: Alice tries to start Bob's instance (permission test)${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/start-specific \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U123","instance_id":"i-test-instance-2"}')
echo "Response: $response"

# Test 7: Permission test - User tries to control their own instance
echo -e "\n${BLUE}Test 7: Alice tries to start her own instance (permission test)${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/start-specific \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U123","instance_id":"i-test-instance-1"}')
echo "Response: $response"

# Test 8: Admin user controls server instance
echo -e "\n${BLUE}Test 8: Admin tries to start the server instance${NC}"
response=$(curl -s -X POST http://localhost:5000/api/simulate/slack/start-specific \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U999","instance_id":"i-0ecdfc9a2e3e53302"}')
echo "Response: $response"

# Test 9: Check all assignments
echo -e "\n${BLUE}Test 9: Check all current assignments${NC}"
response=$(curl -s http://localhost:5000/api/assignments)
echo "Assignments: $response"

# Test 10: Check instance states
echo -e "\n${BLUE}Test 10: Check current instance states${NC}"
for instance_id in "i-test-instance-1" "i-test-instance-2" "i-test-instance-3" "i-0ecdfc9a2e3e53302"; do
    response=$(curl -s http://localhost:5000/api/instances/$instance_id/status)
    echo "Instance $instance_id: $response"
done

echo -e "\n${GREEN}🎉 Simulation tests completed!${NC}"
echo -e "${YELLOW}Summary:${NC}"
echo "- Test data created with 4 users and 4 instances"
echo "- Tested user permissions and instance control"
echo "- Tested error handling for unauthorized access"
echo "- Tested state transitions (start/stop)"
echo "- All responses mimic what Slack would receive" 