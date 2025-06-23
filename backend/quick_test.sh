#!/bin/bash

# Quick Test Script for EC2 Instance
# This script handles the common issues we found

echo "🚀 Quick Test for EC2 Slack Bot"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this from the backend directory."
    exit 1
fi

# Step 1: Set up environment
echo "1. Setting up environment..."

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Test Configuration
TEST_MODE=true

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=true
EOF
    echo "✅ Created .env file"
else
    echo "✅ .env file exists"
fi

# Step 2: Set up virtual environment
echo "2. Setting up virtual environment..."

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Step 3: Install dependencies
echo "3. Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Step 4: Run Python test suite
echo "4. Running Python test suite..."
python3 test_suite.py
PYTHON_EXIT_CODE=$?

# Step 5: Run improved test suite
echo "5. Running improved test suite..."
./run_tests_improved.sh
IMPROVED_EXIT_CODE=$?

# Summary
echo ""
echo "📊 Test Results Summary"
echo "======================"

if [ $PYTHON_EXIT_CODE -eq 0 ]; then
    echo "✅ Python test suite: PASSED"
else
    echo "❌ Python test suite: FAILED"
fi

if [ $IMPROVED_EXIT_CODE -eq 0 ]; then
    echo "✅ Improved test suite: PASSED"
else
    echo "❌ Improved test suite: FAILED"
fi

# Overall result
if [ $PYTHON_EXIT_CODE -eq 0 ] || [ $IMPROVED_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 At least one test suite passed!"
    echo "Your EC2 Slack Bot is ready for deployment."
    echo ""
    echo "Next steps:"
    echo "1. Edit .env with your real credentials"
    echo "2. Deploy to production"
    exit 0
else
    echo ""
    echo "❌ All test suites failed."
    echo "Please check the output above for details."
    exit 1
fi 