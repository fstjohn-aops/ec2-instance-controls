#!/bin/bash

echo "🧪 Quick Database Test"
echo "======================"

# Start container
echo "1. Starting container..."
docker compose up -d --build

# Wait for app to be ready
echo "2. Waiting for app to be ready..."
sleep 10

# Test database creation
echo "3. Testing database creation..."
response=$(curl -s http://localhost:5000/api/assignments)
echo "Assignments response: $response"

# Test creating an assignment
echo "4. Testing assignment creation..."
assignment_response=$(curl -s -X POST http://localhost:5000/api/assign-instance \
    -H "Content-Type: application/json" \
    -d '{"instance_id": "i-test-1", "slack_user_id": "U123", "slack_username": "testuser"}')
echo "Assignment response: $assignment_response"

# Check if database file exists
echo "5. Checking database file..."
if [ -f "data/ec2_instances.db" ]; then
    echo "✅ Database file exists"
    ls -la data/ec2_instances.db
else
    echo "❌ Database file not found"
fi

# Cleanup
echo "6. Cleaning up..."
docker compose down

echo "Test completed!" 