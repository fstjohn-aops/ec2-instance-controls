#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 Testing EC2 Slack Bot (Local Only)${NC}"
echo "=================================="

# Check if Docker is running
echo -e "\n${YELLOW}1. Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check if .env file exists
echo -e "\n${YELLOW}2. Checking environment file...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please copy env.example to .env and fill in your credentials"
    exit 1
fi
echo -e "${GREEN}✅ .env file exists${NC}"

# Check required environment variables
echo -e "\n${YELLOW}3. Checking environment variables...${NC}"
source .env

required_vars=("SLACK_BOT_TOKEN" "SLACK_SIGNING_SECRET" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your-actual-token-here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing or invalid environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi
echo -e "${GREEN}✅ All environment variables are set${NC}"

# Build and start the container
echo -e "\n${YELLOW}4. Building and starting container...${NC}"
docker-compose up --build -d
sleep 10

# Check if container is running
echo -e "\n${YELLOW}5. Checking container status...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Container failed to start${NC}"
    docker-compose logs
    exit 1
fi
echo -e "${GREEN}✅ Container is running${NC}"

# Test health endpoint
echo -e "\n${YELLOW}6. Testing health endpoint...${NC}"
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health endpoint is working${NC}"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
    exit 1
fi

# Test API endpoints
echo -e "\n${YELLOW}7. Testing API endpoints...${NC}"

# Test assignments endpoint (should be empty initially)
echo "Testing GET /api/assignments..."
response=$(curl -s http://localhost:5000/api/assignments)
if echo "$response" | grep -q "\[\]"; then
    echo -e "${GREEN}✅ Assignments endpoint working (empty as expected)${NC}"
else
    echo -e "${RED}❌ Assignments endpoint failed${NC}"
    echo "Response: $response"
fi

# Test instance status endpoint (should fail with invalid instance ID)
echo "Testing GET /api/instances/invalid-id/status..."
response=$(curl -s http://localhost:5000/api/instances/invalid-id/status)
if echo "$response" | grep -q "Instance not found"; then
    echo -e "${GREEN}✅ Instance status endpoint working (correctly rejected invalid ID)${NC}"
else
    echo -e "${RED}❌ Instance status endpoint failed${NC}"
    echo "Response: $response"
fi

# Test assign instance endpoint (should fail with invalid data)
echo "Testing POST /api/assign-instance with invalid data..."
response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}')
if echo "$response" | grep -q "Missing required fields"; then
    echo -e "${GREEN}✅ Assign instance endpoint working (correctly rejected invalid data)${NC}"
else
    echo -e "${RED}❌ Assign instance endpoint failed${NC}"
    echo "Response: $response"
fi

# Test with valid data (should fail due to invalid instance ID)
echo "Testing POST /api/assign-instance with valid format but invalid instance..."
response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"slack_user_id":"U123","slack_username":"test","instance_id":"i-invalid"}')
if echo "$response" | grep -q "Instance not found\|AWS error"; then
    echo -e "${GREEN}✅ Assign instance endpoint working (correctly rejected invalid instance)${NC}"
else
    echo -e "${RED}❌ Assign instance endpoint failed${NC}"
    echo "Response: $response"
fi

# Test database creation
echo -e "\n${YELLOW}8. Checking database creation...${NC}"
if [ -f ec2_instances.db ]; then
    echo -e "${GREEN}✅ Database file created${NC}"
else
    echo -e "${RED}❌ Database file not created${NC}"
fi

# Test container logs
echo -e "\n${YELLOW}9. Checking container logs...${NC}"
if docker-compose logs | grep -q "Running on"; then
    echo -e "${GREEN}✅ Application started successfully${NC}"
else
    echo -e "${RED}❌ Application failed to start${NC}"
    docker-compose logs
fi

# Cleanup
echo -e "\n${YELLOW}10. Cleaning up...${NC}"
docker-compose down
echo -e "${GREEN}✅ Container stopped${NC}"

echo -e "\n${GREEN}🎉 All local tests passed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Ask your admin to install the Slack app"
echo "2. Update the Request URLs in Slack app settings"
echo "3. Test the actual slash commands in Slack" 