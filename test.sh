#!/bin/bash

# Simple script to run tests for the EC2 Instance Control Flask App

echo "Running tests for EC2 Instance Control App..."

# Set test mode
export TEST_MODE=true

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests
python3 -m pytest test_app.py -v 