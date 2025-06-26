#!/bin/bash

echo "Running EC2 Instance Control App tests..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests
python3 test_app.py 