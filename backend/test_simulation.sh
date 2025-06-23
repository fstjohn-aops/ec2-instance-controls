#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if docker-compose or docker compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "none"
    fi
}

DOCKER_COMPOSE_CMD=$(check_docker_compose)

if [ "$DOCKER_COMPOSE_CMD" = "none" ]; then
    echo "❌ Neither docker-compose nor docker compose found"
    exit 1
fi

echo "🧪 EC2 Slack Bot Simulation Tests"
echo "======================================"
echo

# Check if container is running
echo "1. Checking if container is running..."
if ! $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    echo -e "${RED}❌ Container is not running. Please start it first with: $DOCKER_COMPOSE_CMD up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Container is running${NC}"

# Wait for app to be ready
echo "2. Waiting for app to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ App is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ App failed to start within 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

# Set up test data
echo "3. Setting up test data..."
echo "Creating test instance assignments..."

# Create test assignments
test_assignments=(
    '{"instance_id": "i-test-instance-1", "slack_user_id": "U123", "slack_username": "alice"}'
    '{"instance_id": "i-test-instance-2", "slack_user_id": "U456", "slack_username": "bob"}'
    '{"instance_id": "i-test-instance-3", "slack_user_id": "U789", "slack_username": "charlie"}'
    '{"instance_id": "i-0ecdfc9a2e3e53302", "slack_user_id": "U999", "slack_username": "admin"}'
)

for assignment in "${test_assignments[@]}"; do
    response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
        -H "Content-Type: application/json" \
        -d "$assignment")
    echo "$response"
done

echo -e "${GREEN}✅ Test data created${NC}"

# Run test scenarios
echo "4. Running test scenarios..."
echo

# Test 1: Alice tries to start her assigned instance
echo "Test 1: Alice tries to start her assigned instance"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U123",
        "command": "/ec2-start",
        "text": ""
    }')
echo "Response: $response"
echo

# Test 2: Bob tries to stop his assigned instance
echo "Test 2: Bob tries to stop his assigned instance"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U456",
        "command": "/ec2-stop",
        "text": ""
    }')
echo "Response: $response"
echo

# Test 3: Charlie checks status of his assigned instance
echo "Test 3: Charlie checks status of his assigned instance"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U789",
        "command": "/ec2-status",
        "text": ""
    }')
echo "Response: $response"
echo

# Test 4: User without assignment tries to start instance
echo "Test 4: User without assignment tries to start instance"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U000",
        "command": "/ec2-start",
        "text": ""
    }')
echo "Response: $response"
echo

# Test 5: Alice tries to start her already running instance
echo "Test 5: Alice tries to start her already running instance"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U123",
        "command": "/ec2-start",
        "text": ""
    }')
echo "Response: $response"
echo

# Test 6: Alice tries to start Bob's instance (permission test)
echo "Test 6: Alice tries to start Bob's instance (permission test)"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U123",
        "command": "/ec2-start",
        "text": "i-test-instance-2"
    }')
echo "Response: $response"
echo

# Test 7: Alice tries to start her own instance (permission test)
echo "Test 7: Alice tries to start her own instance (permission test)"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U123",
        "command": "/ec2-start",
        "text": "i-test-instance-1"
    }')
echo "Response: $response"
echo

# Test 8: Admin tries to start the server instance
echo "Test 8: Admin tries to start the server instance"
response=$(curl -s -X POST http://localhost:5000/api/slack/command \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "U999",
        "command": "/ec2-start",
        "text": "i-0ecdfc9a2e3e53302"
    }')
echo "Response: $response"
echo

# Test 9: Check all current assignments
echo "Test 9: Check all current assignments"
assignments=$(curl -s http://localhost:5000/api/assignments)
echo "Assignments: $assignments"
echo

# Test 10: Check current instance states
echo "Test 10: Check current instance states"
test_instances=("i-test-instance-1" "i-test-instance-2" "i-test-instance-3" "i-0ecdfc9a2e3e53302")

for instance in "${test_instances[@]}"; do
    status=$(curl -s http://localhost:5000/api/instances/$instance/status)
    echo "Instance $instance: $status"
done
echo

echo -e "${GREEN}🎉 Simulation tests completed!${NC}"
echo "Summary:"
echo "- Test data created with 4 users and 4 instances"
echo "- Tested user permissions and instance control"
echo "- Tested error handling for unauthorized access"
echo "- Tested state transitions (start/stop)"
echo "- All responses mimic what Slack would receive"
echo -e "${GREEN}✅ Slack Simulation Tests completed successfully${NC}" 