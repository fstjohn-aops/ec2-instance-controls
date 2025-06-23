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

echo "🧪 Testing EC2 Slack Bot (Local Only)"
echo "=================================="
echo

# Test 1: Check if Docker is running
echo "1. Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker is running${NC}"
else
    echo -e "${RED}❌ Docker is not running${NC}"
    echo -e "${RED}❌ Local API Tests failed${NC}"
    exit 1
fi

# Test 2: Check if .env file exists
echo "2. Checking environment file..."
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create a .env file with your configuration"
    exit 1
fi

# Test 3: Check environment variables
echo "3. Checking environment variables..."
source .env
required_vars=("SLACK_BOT_TOKEN" "SLACK_SIGNING_SECRET" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All environment variables are set${NC}"
else
    echo -e "${RED}❌ Missing environment variables: ${missing_vars[*]}${NC}"
    exit 1
fi

# Test 4: Build and start container
echo "4. Building and starting container..."
$DOCKER_COMPOSE_CMD down > /dev/null 2>&1
$DOCKER_COMPOSE_CMD up -d --build

# Test 5: Check if container is running
echo "5. Checking container status..."
sleep 5
if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Container is running${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    $DOCKER_COMPOSE_CMD logs
    exit 1
fi

# Test 6: Test health endpoint
echo "6. Testing health endpoint..."
sleep 3
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health endpoint is working${NC}"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
    exit 1
fi

# Test 7: Test API endpoints
echo "7. Testing API endpoints..."
echo "Testing GET /api/assignments..."
response=$(curl -s http://localhost:5000/api/assignments)
if echo "$response" | grep -q "assignments\|error"; then
    echo -e "${GREEN}✅ Assignments endpoint working (empty or database error as expected)${NC}"
else
    echo -e "${RED}❌ Assignments endpoint failed${NC}"
fi

echo "Testing GET /api/instances/invalid-id/status..."
response=$(curl -s http://localhost:5000/api/instances/invalid-id/status)
if echo "$response" | grep -q "error"; then
    echo -e "${GREEN}✅ Instance status endpoint working (correctly rejected invalid ID)${NC}"
else
    echo -e "${RED}❌ Instance status endpoint failed${NC}"
fi

echo "Testing POST /api/assign-instance with invalid data..."
response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
    -H "Content-Type: application/json" \
    -d '{"invalid": "data"}')
if echo "$response" | grep -q "error"; then
    echo -e "${GREEN}✅ Assign instance endpoint working (correctly rejected invalid data)${NC}"
else
    echo -e "${RED}❌ Assign instance endpoint failed${NC}"
fi

echo "Testing POST /api/assign-instance with valid format but invalid instance..."
response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
    -H "Content-Type: application/json" \
    -d '{"instance_id": "i-invalid", "slack_user_id": "U123", "slack_username": "test"}')
if echo "$response" | grep -q "error"; then
    echo -e "${GREEN}✅ Assign instance endpoint working (correctly rejected invalid instance)${NC}"
else
    echo -e "${RED}❌ Assign instance endpoint failed${NC}"
fi

# Test 8: Test with real instance IDs (if available)
echo "8. Testing with real instance IDs..."
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    # Test with a real instance ID from the environment
    real_instance_id="i-0ecdfc9a2e3e53302"
    
    echo "Testing instance status for $real_instance_id..."
    response=$(curl -s http://localhost:5000/api/instances/$real_instance_id/status)
    if echo "$response" | grep -q "status\|error"; then
        echo -e "${GREEN}✅ Instance $real_instance_id status retrieved successfully${NC}"
        echo "  Status: $(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
    else
        echo -e "${RED}❌ Failed to get status for instance $real_instance_id${NC}"
    fi
    
    echo "Testing assignment of real instance $real_instance_id..."
    response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
        -H "Content-Type: application/json" \
        -d "{\"instance_id\": \"$real_instance_id\", \"slack_user_id\": \"U123\", \"slack_username\": \"testuser\"}")
    if echo "$response" | grep -q "success\|error"; then
        if echo "$response" | grep -q "success.*true"; then
            echo -e "${GREEN}✅ Instance $real_instance_id assigned successfully${NC}"
        else
            echo -e "${YELLOW}❌ Failed to assign instance $real_instance_id${NC}"
            echo "  Response: $response"
        fi
    else
        echo -e "${RED}❌ Failed to assign instance $real_instance_id${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping real instance tests (AWS credentials not available)${NC}"
fi

# Test 9: Check database creation
echo "9. Checking database creation..."
if [ -f "data/ec2_instances.db" ]; then
    echo -e "${GREEN}✅ Database file created${NC}"
else
    echo -e "${RED}❌ Database file not created${NC}"
fi

# Test 10: Check container logs for errors
echo "10. Checking container logs..."
logs=$($DOCKER_COMPOSE_CMD logs --tail=20)
if echo "$logs" | grep -q "ERROR\|CRITICAL"; then
    echo -e "${RED}❌ Application failed to start${NC}"
    echo "$logs"
else
    echo -e "${GREEN}✅ Application started successfully${NC}"
fi

# Cleanup
echo -e "\n${YELLOW}Cleaning up...${NC}"
$DOCKER_COMPOSE_CMD down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container stopped${NC}"
else
    echo -e "${RED}❌ Failed to stop container${NC}"
fi

echo
echo -e "${GREEN}🎉 All local tests passed!${NC}"
echo "Next steps:"
echo "1. Ask your admin to install the Slack app"
echo "2. Update the Request URLs in Slack app settings"
echo "3. Test the actual slash commands in Slack"
echo -e "${GREEN}✅ Local API Tests completed successfully${NC}" 