#!/bin/bash

# Quick test to verify API endpoint fixes
echo "🔧 Testing API Endpoint Fixes"
echo "============================="

# Start container in test mode
echo "Starting container..."
docker-compose down >/dev/null 2>&1
TEST_MODE=true docker-compose up -d

echo "Waiting for container to start..."
sleep 10

# Test health endpoint
echo "Testing health endpoint..."
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint failed"
    exit 1
fi

# Test assignments endpoint
echo "Testing assignments endpoint..."
response=$(curl -s http://localhost:5000/api/assignments)
if [ $? -eq 0 ] && echo "$response" | python3 -m json.tool >/dev/null 2>&1; then
    echo "✅ Assignments endpoint working"
    echo "Response: $response"
else
    echo "❌ Assignments endpoint failed"
    echo "Response: $response"
fi

# Test assign-instance endpoint
echo "Testing assign-instance endpoint..."
assignment_response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
    -H "Content-Type: application/json" \
    -d '{"instance_id": "i-test-instance-1", "slack_user_id": "U123", "slack_username": "testuser"}')
if [ $? -eq 0 ] && echo "$assignment_response" | python3 -m json.tool >/dev/null 2>&1; then
    echo "✅ Assign-instance endpoint working"
    echo "Response: $assignment_response"
else
    echo "❌ Assign-instance endpoint failed"
    echo "Response: $assignment_response"
fi

# Cleanup
echo "Cleaning up..."
docker-compose down

echo "Test completed!" 